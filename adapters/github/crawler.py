#!/usr/bin/env python3
"""
GitHub 爬虫模块
提供仓库文件爬取和保存功能
"""

import os
from typing import Dict, List, Optional
from core.base_crawler import BaseCrawler
from adapters.github.api import GitHubAPI


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
