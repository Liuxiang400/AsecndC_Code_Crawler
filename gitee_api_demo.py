#!/usr/bin/env python3
"""
Gitee API 爬虫示例
使用 Gitee API v5 获取仓库信息
支持 OAuth2 授权

主入口文件 - 提供命令行界面
"""

import sys
from demos import (
    demo_crawl_gitee_repo,
    demo_crawl_code_files,
    demo_search_repositories,
    demo_oauth_authorization
)


def print_banner():
    """打印程序横幅"""
    print("\n" + "=" * 60)
    print("Gitee API 爬虫示例")
    print("=" * 60)


def print_menu():
    """打印主菜单"""
    print("\n请选择运行模式:")
    print("1. 基础仓库信息爬取")
    print("2. 代码文件爬取（新功能）")
    print("3. OAuth2 授权演示")
    print("4. 仓库搜索")


def get_mode():
    """
    获取运行模式

    Returns:
        模式字符串
    """
    # 如果有命令行参数，使用参数
    if len(sys.argv) > 1:
        return sys.argv[1]

    # 否则显示菜单并让用户选择
    print_menu()
    choice = input("\n请输入选项 (1/2/3/4): ").strip()
    mode_map = {
        "1": "basic",
        "2": "code",
        "3": "oauth",
        "4": "search"
    }
    return mode_map.get(choice, "code")


def main():
    """主函数"""
    print_banner()

    mode = get_mode()

    if mode == "basic":
        demo_crawl_gitee_repo()
    elif mode == "code":
        demo_crawl_code_files()
    elif mode == "oauth":
        demo_oauth_authorization()
    elif mode == "search":
        demo_search_repositories()
    else:
        print("❌ 无效的选项")
        sys.exit(1)


if __name__ == "__main__":
    main()
