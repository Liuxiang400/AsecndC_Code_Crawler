#!/usr/bin/env python3
"""
GitHub API 客户端模块
提供基础的 API 请求和仓库信息获取功能
"""

import requests
from typing import Dict, List, Optional
from core.base_api import BaseAPI
from adapters.github.oauth import GitHubOAuth


class GitHubAPI(BaseAPI):
    """GitHub API 客户端"""

    BASE_URL = "https://api.github.com"

    def __init__(self, access_token: Optional[str] = None, oauth: Optional[GitHubOAuth] = None):
        """
        初始化 GitHub API 客户端

        Args:
            access_token: 可选的访问令牌（Personal Access Token）
            oauth: 可选的 OAuth 对象，支持自动刷新令牌
        """
        self.access_token = access_token
        self.oauth = oauth
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "GitHub-API-Demo/1.0",
                "Content-Type": "application/json",
                "Accept": "application/vnd.github.v3+json",
            }
        )

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        发送GET请求

        Args:
            endpoint: API端点
            params: 请求参数

        Returns:
            响应JSON数据
        """
        url = f"{self.BASE_URL}{endpoint}"

        if params is None:
            params = {}

        # 准备请求头
        headers = {}
        # 优先使用 OAuth 令牌，支持自动刷新
        token = None
        if self.oauth:
            if self.oauth.is_token_expired():
                print("⚠️  令牌已过期，正在刷新...")
                if self.oauth.refresh_access_token():
                    token = self.oauth.access_token
            else:
                token = self.oauth.access_token
        elif self.access_token:
            token = self.access_token

        # GitHub 使用 Bearer token
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            # 搜索接口可能需要更长的超时时间
            timeout = 30 if 'search' in endpoint else 10
            response = self.session.get(url, params=params, headers=headers, timeout=timeout)

            # 检查速率限制
            if response.status_code == 403:
                remaining = response.headers.get('X-RateLimit-Remaining', '0')
                reset_time = response.headers.get('X-RateLimit-Reset', '')
                print("❌ GitHub API 速率限制已超出!")
                print(f"   剩余请求次数: {remaining}")
                if reset_time:
                    import datetime
                    reset_time_str = datetime.datetime.fromtimestamp(int(reset_time)).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"   重置时间: {reset_time_str}")
                print("   建议:")
                print("   1. 等待一段时间后重试（通常1小时后重置）")
                print("   2. 使用 Personal Access Token 提高限制")
                print("   3. 检查 https://github.com/settings/tokens")
                return {}

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                print(f"❌ 请求参数错误: {e}")
                print(f"   URL: {url}")
                print(f"   参数: {params}")
                print("   建议: 检查搜索关键词是否包含特殊字符")
            elif e.response.status_code == 401:
                print("❌ 认证失败: Access Token 无效或已过期")
                print("   建议: 更新 .env 文件中的 GITHUB_ACCESS_TOKEN")
            elif e.response.status_code == 404:
                print(f"❌ 资源未找到: {endpoint}")
            else:
                print(f"❌ HTTP 错误: {e}")
            return {}
        except requests.exceptions.Timeout as e:
            print(f"❌ 请求超时: {e}")
            print(f"   URL: {url}")
            print("   建议: GitHub API 响应较慢，请稍后重试")
            return {}
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求失败: {e}")
            return {}

    def get_repo(self, owner: str, repo: str) -> Dict:
        """
        获取仓库信息

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            仓库信息字典
        """
        print(f"\n=== 获取仓库信息: {owner}/{repo} ===")
        endpoint = f"/repos/{owner}/{repo}"
        return self._get(endpoint)

    def get_repo_readme(self, owner: str, repo: str) -> Dict:
        """
        获取仓库的README内容

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            README内容
        """
        print(f"\n=== 获取README: {owner}/{repo} ===")
        endpoint = f"/repos/{owner}/{repo}/readme"
        return self._get(endpoint)

    def get_repo_issues(self, owner: str, repo: str, state: str = "open") -> List[Dict]:
        """
        获取仓库的Issues

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            state: 状态，open或closed

        Returns:
            Issue列表
        """
        print(f"\n=== 获取Issues: {owner}/{repo} ({state}) ===")
        endpoint = f"/repos/{owner}/{repo}/issues"
        return self._get(endpoint, params={"state": state, "per_page": 50})

    def get_issue_comments(
        self, owner: str, repo: str, issue_number: int
    ) -> List[Dict]:
        """
        获取指定 Issue 的评论

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            issue_number: Issue 编号

        Returns:
            评论列表
        """
        print(f"\n=== 获取 Issue #{issue_number} 的评论: {owner}/{repo} ===")
        endpoint = f"/repos/{owner}/{repo}/issues/{issue_number}/comments"
        result = self._get(endpoint, params={"per_page": 100})

        # 确保返回列表
        if isinstance(result, list):
            return result
        elif isinstance(result, dict) and not result:
            return []
        else:
            return [result] if result else []

    def get_repo_contents(
        self, owner: str, repo: str, path: str = "", branch: str = "main"
    ) -> List[Dict]:
        """
        获取仓库目录内容（文件和文件夹列表）

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            path: 目录路径，空字符串表示根目录
            branch: 分支名，默认main（GitHub默认分支）

        Returns:
            文件/目录列表
        """
        print(f"\n=== 获取目录内容: {owner}/{repo}/{path} ===")
        if path:
            endpoint = f"/repos/{owner}/{repo}/contents/{path}"
        else:
            endpoint = f"/repos/{owner}/{repo}/contents"
        return self._get(endpoint, params={"ref": branch})

    def get_file_content(
        self, owner: str, repo: str, path: str, branch: str = "main"
    ) -> Optional[Dict]:
        """
        获取单个文件的内容（解码base64）

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            path: 文件路径
            branch: 分支名，默认main

        Returns:
            包含文件信息的字典（含解码后的content字段）
        """
        print(f"\n=== 获取文件内容: {owner}/{repo}/{path} ===")
        endpoint = f"/repos/{owner}/{repo}/contents/{path}"

        result = self._get(endpoint, params={"ref": branch})
        if not result:
            return None

        # 解码base64内容
        if "content" in result:
            try:
                # GitHub API 返回的是 base64 编码的内容
                encoded_content = result["content"]
                # 移除可能的换行符
                encoded_content = encoded_content.replace("\n", "")
                # 解码
                import base64
                decoded_content = base64.b64decode(encoded_content).decode("utf-8")
                result["decoded_content"] = decoded_content
            except Exception as e:
                print(f"解码文件内容失败: {e}")
                result["decoded_content"] = None

        return result

    def get_repo_readme_decoded(self, owner: str, repo: str) -> Optional[Dict]:
        """
        获取仓库的README内容（解码后）

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            README内容（含解码后的text字段）
        """
        print(f"\n=== 获取README内容: {owner}/{repo} ===")
        endpoint = f"/repos/{owner}/{repo}/readme"

        result = self._get(endpoint)
        if not result:
            return None

        # 解码base64内容
        if "content" in result:
            try:
                encoded_content = result["content"]
                encoded_content = encoded_content.replace("\n", "")
                import base64
                decoded_content = base64.b64decode(encoded_content).decode("utf-8")
                result["text"] = decoded_content
            except Exception as e:
                print(f"解码README失败: {e}")
                result["text"] = None

        return result

    def search_repositories(
        self,
        query: str,
        language: Optional[str] = None,
        sort: str = "stars",
        order: str = "desc",
        per_page: int = 10
    ) -> List[Dict]:
        """
        搜索仓库

        Args:
            query: 搜索关键词
            language: 编程语言过滤
            sort: 排序方式 (stars, forks, updated)
            order: 排序顺序 (desc, asc)
            per_page: 每页结果数量 (最大100)

        Returns:
            仓库列表
        """
        print(f"\n=== 搜索仓库: {query} ===")

        # 限制 per_page 在合理范围内
        per_page = min(per_page, 100)

        # 构建搜索查询
        search_query = query
        if language:
            search_query = f"{query} language:{language}"

        params = {
            "q": search_query,
            "sort": sort,
            "order": order,
            "per_page": per_page
        }

        endpoint = "/search/repositories"

        try:
            result = self._get(endpoint, params)
            # GitHub 搜索 API 返回 {"items": [...]}
            if isinstance(result, dict) and 'items' in result:
                return result['items']
            return result if result else []
        except Exception as e:
            print(f"搜索请求异常: {e}")
            return []

    def get_user_info(self) -> Optional[Dict]:
        """
        获取当前用户信息

        Returns:
            用户信息字典
        """
        print(f"\n=== 获取用户信息 ===")
        return self._get("/user")

    def get_user_repos(self, per_page: int = 20) -> List[Dict]:
        """
        获取当前用户的仓库列表

        Args:
            per_page: 每页结果数量

        Returns:
            仓库列表
        """
        print(f"\n=== 获取用户仓库 ===")
        return self._get("/user/repos", params={"per_page": per_page})
