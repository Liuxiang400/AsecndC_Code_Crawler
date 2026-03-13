#!/usr/bin/env python3
"""
Gitee API 客户端核心模块
提供基础的 API 请求和仓库信息获取功能
"""

import requests
from typing import Dict, List, Optional
from gitee_oauth import GiteeOAuth


class GiteeAPI:
    """Gitee API 客户端"""

    BASE_URL = "https://gitee.com/api/v5"

    def __init__(self, access_token: Optional[str] = None, oauth: Optional[GiteeOAuth] = None):
        """
        初始化 Gitee API 客户端

        Args:
            access_token: 可选的访问令牌，用于提高API调用限制
            oauth: 可选的 OAuth 对象，支持自动刷新令牌
        """
        self.access_token = access_token
        self.oauth = oauth
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Gitee-API-Demo/1.0",
                "Content-Type": "application/json",
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

        # 如果有token，添加到参数中
        if token:
            params["access_token"] = token

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}")
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

    def get_repo_contents(
        self, owner: str, repo: str, path: str = "", branch: str = "master"
    ) -> List[Dict]:
        """
        获取仓库目录内容（文件和文件夹列表）

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            path: 目录路径，空字符串表示根目录
            branch: 分支名，默认master

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
        self, owner: str, repo: str, path: str, branch: str = "master"
    ) -> Optional[Dict]:
        """
        获取单个文件的内容（解码base64）

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            path: 文件路径
            branch: 分支名，默认master

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
                # Gitee API 返回的是 base64 编码的内容
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
            per_page: 每页结果数量

        Returns:
            仓库列表
        """
        print(f"\n=== 搜索仓库: {query} ===")

        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": per_page
        }

        if language:
            params["q"] = f"{params['q']} language:{language}"

        endpoint = "/search/repositories"
        return self._get(endpoint, params)

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
