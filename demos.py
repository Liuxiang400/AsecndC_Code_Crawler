#!/usr/bin/env python3
"""
演示函数模块
包含各种使用场景的演示函数
"""

import os
import dotenv
from gitee_api import GiteeAPI
from gitee_oauth import GiteeOAuth
from gitee_crawler import GiteeCrawler
from utils import print_json, print_repo_summary, print_readme_preview, print_file_structure, print_issues_summary


def demo_crawl_gitee_repo():
    """演示：爬取Gitee仓库的代码、Issues和README"""
    dotenv.load_dotenv()
    # 或者通过环境变量设置: export GITEE_ACCESS_TOKEN="your_token"
    access_token = os.getenv("GITEE_ACCESS_TOKEN")

    # 初始化API客户端
    api = GiteeAPI(access_token=access_token)

    # 示例：爬取一个公开的小仓库
    # 你可以修改为你感兴趣的仓库
    owner = "harrygt"  # 示例所有者
    repo = "ascendc-tutorial"  # 示例仓库名

    print(f"\n开始爬取 Gitee 仓库: {owner}/{repo}")
    print("=" * 60)

    # 1. 获取仓库基本信息
    repo_info = api.get_repo(owner, repo)
    if repo_info:
        print_json(repo_info, "仓库基本信息")
        print_repo_summary(repo_info)

    # 2. 获取并展示 README 内容（解码后）
    readme = api.get_repo_readme_decoded(owner, repo)
    if readme and "text" in readme:
        print_readme_preview(readme)

    # 3. 获取仓库的文件/目录结构
    contents = api.get_repo_contents(owner, repo, path="")
    print_file_structure(contents)

    # 4. 获取前3个文件的内容（如果是代码文件）
    if isinstance(contents, list) and contents:
        code_files = [item for item in contents if item.get("type") == "file"][:3]
        for file_item in code_files:
            file_path = file_item.get("name", "")
            print(f"\n📝 获取文件: {file_path}")
            file_content = api.get_file_content(owner, repo, file_path)
            if file_content and file_content.get("decoded_content"):
                # 只显示前200个字符
                content_preview = file_content["decoded_content"][:200]
                if len(file_content["decoded_content"]) > 200:
                    content_preview += "\n... (内容过长，已截断)"
                print(f"内容预览:\n{content_preview}")
            else:
                print("无法获取文件内容（可能是二进制文件）")

    # 5. 获取 Issues
    issues = api.get_repo_issues(owner, repo, state="open")
    print_issues_summary(issues)

    print("\n" + "=" * 60)
    print("✅ 爬取完成!")


def demo_crawl_code_files():
    """演示：爬取仓库代码文件"""
    dotenv.load_dotenv()
    access_token = os.getenv("GITEE_ACCESS_TOKEN")

    # 初始化API客户端
    api = GiteeAPI(access_token=access_token)
    crawler = GiteeCrawler(api)

    # 目标仓库
    owner = "harrygt"
    repo = "ascendc-tutorial"

    print(f"\n开始爬取仓库代码文件: {owner}/{repo}")
    print("=" * 60)

    # 方式1：只爬取Python文件，最多50个
    print("\n📥 方式1：爬取指定类型的文件（python）")
    python_files = crawler.crawl_repo_files(
        owner=owner,
        repo=repo,
        branch="master",
        max_files=50,
        file_extensions=[".python"],
    )

    if python_files:
        print(f"\n获取到 {len(python_files)} 个Python文件:")
        for file_path in list(python_files.keys())[:5]:
            print(f"  - {file_path}")
            # 显示文件内容的前100个字符
            if len(python_files[file_path]) > 100:
                print(f"    预览: {python_files[file_path][:100]}...")
            else:
                print(f"    预览: {python_files[file_path]}")

    # 方式2：爬取所有文件类型，最多30个
    print("\n\n📥 方式2：爬取所有类型文件")
    all_files = crawler.crawl_repo_files(
        owner=owner,
        repo=repo,
        branch="master",
        max_files=30,
        file_extensions=None,
    )

    if all_files:
        print(f"\n获取到 {len(all_files)} 个文件:")
        for file_path in list(all_files.keys())[:10]:
            file_size = len(all_files[file_path])
            print(f"  - {file_path} ({file_size} bytes)")

    # 方式3：爬取并保存到本地
    print("\n\n📥 方式3：爬取并保存到本地目录")
    saved_files = crawler.save_repo_files(
        owner=owner,
        repo=repo,
        output_dir=f"output/{repo}",
        branch="master",
        max_files=20,
        file_extensions=[".py", ".md", ".txt",".cpp",".h","hpp","c"],
    )

    if saved_files:
        print(f"\n✅ 成功保存 {len(saved_files)} 个文件")
        print("文件映射（远程路径 -> 本地路径）:")
        for remote_path, local_path in list(saved_files.items())[:5]:
            print(f"  {remote_path} -> {local_path}")

    print("\n" + "=" * 60)
    print("✅ 代码文件爬取完成!")


def demo_search_repositories():
    """演示：搜索仓库"""
    api = GiteeAPI()

    print("\n=== 搜索仓库示例 ===")

    # 搜索热门的Python仓库
    results = api.search_repositories(
        query="python",
        language="python",
        sort="stars",
        order="desc",
        per_page=10
    )

    if isinstance(results, list) and results:
        print(f"\n找到 {len(results)} 个仓库:")
        for i, repo in enumerate(results, 1):
            print(f"\n{i}. {repo.get('full_name')}")
            print(f"   描述: {repo.get('description', 'N/A')[:60]}...")
            print(f"   Stars: {repo.get('stargazers_count', 0)}")
            print(f"   URL: {repo.get('html_url')}")


def demo_oauth_authorization():
    """演示：OAuth2 授权流程"""
    print("\n" + "=" * 60)
    print("Gitee OAuth2 授权演示")
    print("=" * 60)

    # 配置你的 OAuth 应用信息
    # 需要在 https://gitee.com/settings/applications 创建应用
    # 可以通过环境变量设置:
    # export GITEE_CLIENT_ID="your_client_id"
    # export GITEE_CLIENT_SECRET="your_client_secret"

    client_id = os.getenv("GITEE_CLIENT_ID")
    if not client_id:
        client_id = input("请输入你的 Client ID: ").strip()
    if not client_id:
        print("❌ Client ID 不能为空")
        return

    client_secret = os.getenv("GITEE_CLIENT_SECRET")
    if not client_secret:
        client_secret = input("请输入你的 Client Secret: ").strip()
    if not client_secret:
        print("❌ Client Secret 不能为空")
        return

    # 创建 OAuth 客户端
    oauth = GiteeOAuth(
        client_id=client_id,
        client_secret=client_secret,
        scopes=["user_info", "projects", "pull_requests", "issues", "notes"],
    )

    # 尝试从文件加载已保存的令牌
    if oauth.load_from_file():
        if oauth.is_token_expired():
            print("⚠️  已保存的令牌已过期，尝试刷新...")
            if not oauth.refresh_access_token():
                print("⚠️  刷新失败，需要重新授权")
            else:
                print("✅ 令牌刷新成功")
        else:
            print("✅ 已加载有效的访问令牌")
    else:
        # 使用交互式授权
        print("\n选择授权方式:")
        print("1. 浏览器授权（推荐）")
        print("2. 密码授权（需要应用支持）")

        choice = input("\n请选择 (1/2): ").strip()

        if choice == "1":
            if not oauth.authorize_interactive():
                print("❌ 授权失败")
                return
        elif choice == "2":
            username = input("请输入 Gitee 用户名: ").strip()
            password = input("请输入 Gitee 密码: ").strip()

            if not oauth.get_token_with_password(username, password):
                print("❌ 授权失败")
                return
        else:
            print("❌ 无效的选择")
            return

    # 保存令牌到文件
    oauth.save_to_file()

    # 使用 OAuth 令牌创建 API 客户端
    api = GiteeAPI(oauth=oauth)

    print("\n" + "=" * 60)
    print("🧪 测试 API 调用")
    print("=" * 60)

    # 测试获取用户信息
    print("\n📊 获取当前用户信息...")
    user_info = api.get_user_info()
    if user_info:
        print(f"✅ 用户: {user_info.get('login')}")
        print(f"   姓名: {user_info.get('name')}")
        print(f"   Email: {user_info.get('email')}")
        print(f"   关注: {user_info.get('following_count')}")
        print(f"   粉丝: {user_info.get('followers_count')}")

    # 测试获取用户的仓库
    print("\n📦 获取用户的仓库...")
    repos = api.get_user_repos(per_page=5)
    if isinstance(repos, list) and repos:
        print(f"✅ 找到 {len(repos)} 个仓库:")
        for repo in repos:
            print(f"   - {repo.get('full_name')} ({repo.get('private') and '私有' or '公开'})")

    # 测试爬取代码文件
    print("\n📥 测试爬取代码文件...")
    crawler = GiteeCrawler(api)

    owner = input("\n请输入要爬取的仓库所有者 (留空跳过): ").strip()
    if owner:
        repo = input("请输入仓库名称: ").strip()
        if repo:
            files = crawler.crawl_repo_files(
                owner=owner,
                repo=repo,
                max_files=10,
                file_extensions=[".py", ".md"],
            )

            if files:
                print(f"\n✅ 成功爬取 {len(files)} 个文件")
                for file_path in list(files.keys())[:3]:
                    print(f"   - {file_path}")

    print("\n" + "=" * 60)
    print("✅ OAuth 授权演示完成!")
    print("\n💡 提示:")
    print("   - 令牌已保存到 .gitee_token.json")
    print("   - 下次运行时会自动加载令牌")
    print("   - 令牌过期时会自动刷新")
