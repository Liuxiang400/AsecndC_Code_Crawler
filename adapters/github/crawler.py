#!/usr/bin/env python3
"""
GitHub 爬虫模块
提供仓库文件爬取和保存功能
"""

import os
import json
import re
from typing import Dict, List, Optional
from datetime import datetime
from core.base_crawler import BaseCrawler
from adapters.github.api import GitHubAPI
from utils import clean_issue_data, sanitize_filename


class GitHubCrawler(BaseCrawler):
    """GitHub 仓库爬虫"""

    def __init__(self, api: GitHubAPI):
        """
        初始化爬虫

        Args:
            api: GitHubAPI 实例
        """
        super().__init__(api)

    def crawl_repo_files(
        self,
        owner: str,
        repo: str,
        path: str = "",
        branch: str = "main",
        max_files: int = 100,
        file_extensions: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        递归爬取仓库中的所有代码文件

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            path: 起始路径，空字符串表示根目录
            branch: 分支名，默认main（GitHub默认分支）
            max_files: 最大文件数量限制
            file_extensions: 文件扩展名过滤列表，如 ['.py', '.js']，None表示所有文件

        Returns:
            字典，键为文件路径，值为文件内容
        """
        print(f"\n=== 爬取仓库文件: {owner}/{repo}/{path} ===")
        files_dict = {}
        file_count = 0

        def _crawl_recursive(current_path: str):
            nonlocal file_count
            if file_count >= max_files:
                return

            # 获取当前目录的内容
            contents = self.api.get_repo_contents(owner, repo, current_path, branch)
            if not isinstance(contents, list):
                return

            for item in contents:
                if file_count >= max_files:
                    break

                item_type = item.get("type")
                item_name = item.get("name")
                item_path = item.get("path")

                if item_type == "dir":
                    # 递归处理子目录
                    _crawl_recursive(item_path)
                elif item_type == "file":
                    # 检查文件扩展名
                    if file_extensions:
                        if not any(item_name.endswith(ext) for ext in file_extensions):
                            continue

                    # 获取文件内容
                    file_data = self.api.get_file_content(owner, repo, item_path, branch)
                    if file_data and file_data.get("decoded_content"):
                        files_dict[item_path] = file_data["decoded_content"]
                        file_count += 1
                        print(f"✓ 已获取: {item_path} ({file_count}/{max_files})")

        _crawl_recursive(path)
        print(f"\n✅ 共爬取 {file_count} 个文件")
        return files_dict

    def save_repo_files(
        self,
        owner: str,
        repo: str,
        output_dir: str = "./repo_files",
        path: str = "",
        branch: str = "main",
        max_files: int = 100,
        file_extensions: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        爬取仓库文件并保存到本地目录

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            output_dir: 本地输出目录
            path: 起始路径
            branch: 分支名
            max_files: 最大文件数量
            file_extensions: 文件扩展名过滤

        Returns:
            字典，键为文件路径，值为本地保存路径
        """
        # 爬取文件
        files_dict = self.crawl_repo_files(
            owner, repo, path, branch, max_files, file_extensions
        )

        if not files_dict:
            print("没有获取到任何文件")
            return {}

        # 创建输出目录
        repo_dir = os.path.join(output_dir, f"{owner}_{repo}")
        os.makedirs(repo_dir, exist_ok=True)

        saved_files = {}
        for file_path, content in files_dict.items():
            # 构建本地文件路径
            local_path = os.path.join(repo_dir, file_path)
            local_dir = os.path.dirname(local_path)

            # 创建目录
            os.makedirs(local_dir, exist_ok=True)

            # 写入文件
            try:
                with open(local_path, "w", encoding="utf-8") as f:
                    f.write(content)
                saved_files[file_path] = local_path
                print(f"💾 已保存: {local_path}")
            except Exception as e:
                print(f"❌ 保存失败 {local_path}: {e}")

        print(f"\n✅ 共保存 {len(saved_files)} 个文件到: {repo_dir}")
        return saved_files

    def crawl_repo_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        max_issues: int = 100,
    ) -> List[Dict]:
        """
        爬取 GitHub 仓库的 Issues

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            state: 状态 (open/closed/all)
            max_issues: 最大 issue 数量

        Returns:
            Issue 列表
        """
        print(f"\n=== 爬取 Issues: {owner}/{repo} ({state}) ===")
        issues_list = []

        # 如果 state 是 "all"，需要分别获取 open 和 closed
        if state == "all":
            states_to_fetch = ["open", "closed"]
        else:
            states_to_fetch = [state]

        for current_state in states_to_fetch:
            # 使用 API 方法获取 issues
            issues = self.api.get_repo_issues(owner, repo, current_state)

            if issues and isinstance(issues, list):
                issues_list.extend(issues)
                print(f"✓ 获取到 {len(issues)} 个 {current_state} 状态的 issues")

            # 限制数量
            if len(issues_list) >= max_issues:
                issues_list = issues_list[:max_issues]
                break

        print(f"✅ 共爬取 {len(issues_list)} 个 issues")
        return issues_list

    def save_repo_issues(
        self,
        owner: str,
        repo: str,
        output_dir: str,
        state: str = "open",
        max_issues: int = 100,
    ) -> Dict[str, str]:
        """
        爬取并保存 Issues 到本地（精简格式 + 评论）

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            output_dir: 输出目录
            state: 状态 (open/closed/all)
            max_issues: 最大 issue 数量

        Returns:
            字典，键为 issue 编号，值为保存路径
        """
        # 爬取 issues
        issues_list = self.crawl_repo_issues(owner, repo, state, max_issues)

        if not issues_list:
            print("没有获取到任何 issues")
            return {}

        # 创建输出目录
        # 组织结构: output_dir/owner_repo/issues/
        repo_dir = os.path.join(output_dir, f"{owner}_{repo}")
        issues_dir = os.path.join(repo_dir, "issues")
        os.makedirs(issues_dir, exist_ok=True)

        saved_issues = {}
        cleaned_issues_list = []  # 用于索引文件

        for issue in issues_list:
            issue_number = issue.get('number', 'unknown')
            issue_title = issue.get('title', 'untitled')

            # 获取评论
            comments = []
            try:
                comments = self.api.get_issue_comments(owner, repo, issue_number)
                print(f"✓ 获取到 {len(comments)} 条评论")
            except Exception as e:
                print(f"⚠️  获取评论失败: {e}")

            # 清洗数据（只保留有价值的信息）
            cleaned_issue = clean_issue_data(issue, comments)
            cleaned_issues_list.append(cleaned_issue)

            # 清理文件名
            safe_title = sanitize_filename(issue_title)

            # 保存为 JSON（精简格式）
            filename = f"issue_{issue_number}_{safe_title}.json"
            filepath = os.path.join(issues_dir, filename)

            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(cleaned_issue, f, ensure_ascii=False, indent=2)
                saved_issues[issue_number] = filepath
                print(f"💾 已保存: {filepath}")
            except Exception as e:
                print(f"❌ 保存失败 {filepath}: {e}")

        # 保存汇总索引（使用清洗后的数据）
        self._create_issues_index(issues_dir, owner, repo, state, cleaned_issues_list, saved_issues)

        print(f"\n✅ 共保存 {len(saved_issues)} 个 issues 到: {issues_dir}")
        return saved_issues

    def _create_issues_index(
        self,
        issues_dir: str,
        owner: str,
        repo: str,
        state: str,
        issues_list: List[Dict],
        saved_issues: Dict[str, str]
    ):
        """
        创建 issues 索引文件

        Args:
            issues_dir: issues 目录路径
            owner: 仓库所有者
            repo: 仓库名称
            state: issue 状态
            issues_list: issues 列表
            saved_issues: 已保存的 issues 字典
        """
        index_file = os.path.join(issues_dir, "issues_index.json")

        index_data = {
            'repo': f"{owner}/{repo}",
            'state': state,
            'total': len(issues_list),
            'crawl_time': datetime.now().isoformat(),
            'issues': [
                {
                    'number': issue.get('number'),
                    'title': issue.get('title'),
                    'state': issue.get('state'),
                    'created_at': issue.get('created_at'),
                    'updated_at': issue.get('updated_at'),
                    'file': saved_issues.get(issue.get('number'))
                }
                for issue in issues_list
            ]
        }

        try:
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
            print(f"📋 索引文件已创建: {index_file}")
        except Exception as e:
            print(f"❌ 创建索引文件失败: {e}")
