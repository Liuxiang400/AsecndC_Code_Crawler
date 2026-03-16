#!/usr/bin/env python3
"""
工具函数模块
提供通用的辅助函数
"""

import json
from typing import Any, Dict, List, Optional


def print_json(data: Any, title: str = "") -> None:
    """
    美化打印JSON数据

    Args:
        data: 要打印的数据（可以是字典、列表等）
        title: 可选的标题
    """
    if title:
        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print("=" * 60)
    print(json.dumps(data, indent=2, ensure_ascii=False))


def print_repo_summary(repo_info: Dict) -> None:
    """
    打印仓库摘要信息

    Args:
        repo_info: 仓库信息字典
    """
    if not repo_info or "name" not in repo_info:
        return

    print(f"\n📦 仓库名称: {repo_info.get('name')}")
    print(f"📝 描述: {repo_info.get('description', 'N/A')}")
    print(f"⭐ Stars: {repo_info.get('stargazers_count', 0)}")
    print(f"🌐 语言: {repo_info.get('language', 'N/A')}")
    print(f"🔗 URL: {repo_info.get('html_url', 'N/A')}")


def print_readme_preview(readme: Dict, max_chars: int = 500) -> None:
    """
    打印README内容预览

    Args:
        readme: README数据字典
        max_chars: 最大显示字符数
    """
    if not readme or "text" not in readme:
        return

    print(f"\n📄 README 内容:")
    print("-" * 60)

    readme_text = readme["text"]
    if len(readme_text) > max_chars:
        print(readme_text[:max_chars] + f"\n... (内容过长，已截断)")
    else:
        print(readme_text)

    print("-" * 60)


def print_file_structure(contents: list) -> None:
    """
    打印文件/目录结构

    Args:
        contents: 文件/目录列表
    """
    if not isinstance(contents, list) or not contents:
        return

    print(f"\n📂 仓库文件结构:")
    print(f"根目录文件/文件夹数量: {len(contents)}")

    for item in contents:
        item_type = item.get("type", "unknown")
        item_name = item.get("name", "unknown")
        item_size = item.get("size", 0)

        if item_type == "dir":
            print(f"  📁 {item_name}/")
        else:
            print(f"  📄 {item_name} ({item_size} bytes)")


def print_issues_summary(issues: list, max_display: int = 3) -> None:
    """
    打印Issues摘要

    Args:
        issues: Issues列表
        max_display: 最多显示的数量
    """
    if not isinstance(issues, list) or not issues:
        return

    print(f"\n🎋 Open Issues数量: {len(issues)}")

    if issues:
        print(f"\n前{min(max_display, len(issues))}个Open Issues:")
        for i, issue in enumerate(issues[:max_display], 1):
            print(f"\n{i}. Issue #{issue.get('number', 'N/A')}")
            print(f"   标题: {issue.get('title', 'N/A')}")
            print(f"   作者: {issue.get('user', {}).get('login', 'N/A')}")
            print(f"   状态: {issue.get('state', 'N/A')}")
            print(f"   创建时间: {issue.get('created_at', 'N/A')}")

            body = issue.get('body', '')
            if body:
                body_preview = body[:100] + "..." if len(body) > 100 else body
                print(f"   内容: {body_preview}")


def clean_issue_data(issue: Dict, comments: Optional[List[Dict]] = None) -> Dict:
    """
    清洗 Issue 数据，只保留有价值的信息

    Args:
        issue: 原始 Issue 数据
        comments: Issue 评论列表（可选）

    Returns:
        清洗后的 Issue 数据
    """
    # 提取标签
    labels = []
    if issue.get('labels'):
        if isinstance(issue['labels'], list):
            labels = [label.get('name', '') for label in issue['labels'] if label.get('name')]

    # 清洗评论数据
    cleaned_comments = []
    if comments:
        for comment in comments:
            cleaned_comment = {
                'author': comment.get('user', {}).get('login', 'Unknown'),
                'created_at': comment.get('created_at', ''),
                'updated_at': comment.get('updated_at', ''),
                'body': comment.get('body', '')
            }
            cleaned_comments.append(cleaned_comment)

    # 构建精简的 Issue 数据
    cleaned_issue = {
        'number': issue.get('number'),
        'title': issue.get('title', ''),
        'state': issue.get('state', ''),
        'author': issue.get('user', {}).get('login', 'Unknown'),
        'created_at': issue.get('created_at', ''),
        'updated_at': issue.get('updated_at', ''),
        'closed_at': issue.get('closed_at'),
        'body': issue.get('body', ''),
        'comments': cleaned_comments,
        'comments_count': len(cleaned_comments),
        'labels': labels,
        'html_url': issue.get('html_url', '')
    }

    # 如果是 Pull Request，添加 PR 信息
    if issue.get('pull_request'):
        cleaned_issue['is_pull_request'] = True
        cleaned_issue['merged_at'] = issue.get('pull_request', {}).get('merged_at')
    else:
        cleaned_issue['is_pull_request'] = False

    return cleaned_issue


def sanitize_filename(filename: str) -> str:
    """
    清理文件名中的非法字符

    Args:
        filename: 原始文件名

    Returns:
        清理后的文件名
    """
    import re
    # 移除或替换非法字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 限制长度
    if len(filename) > 100:
        filename = filename[:100]
    return filename.strip()
