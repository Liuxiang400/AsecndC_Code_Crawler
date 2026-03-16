#!/usr/bin/env python3
"""
Gitee API 客户端模块
提供基础的 API 请求和仓库信息获取功能
"""

import requests
from typing import Dict, List, Optional
from core.base_api import BaseAPI
from adapters.gitee.oauth import GiteeOAuth


class GiteeAPI(BaseAPI):
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
            # 搜索接口可能需要更长的超时时间
            timeout = 30 if 'search' in endpoint else 10
            response = self.session.get(url, params=params, timeout=timeout)

            # 检查速率限制
            if response.status_code == 403:
                print("❌ API 速率限制已超出!")
                print("   建议:")
                print("   1. 等待一段时间后重试（通常1小时后重置）")
                print("   2. 使用 Access Token 提高限制")
                print("   3. 检查 https://gitee.com/profile/personal_access_tokens")
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
                print("   建议: 更新 .env 文件中的 GITEE_ACCESS_TOKEN")
            elif e.response.status_code == 404:
                print(f"❌ 资源未找到: {endpoint}")
            else:
                print(f"❌ HTTP 错误: {e}")
            return {}
        except requests.exceptions.Timeout as e:
            print(f"❌ 请求超时: {e}")
            print(f"   URL: {url}")
            print("   建议: Gitee API 搜索接口响应较慢，请稍后重试")
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

        result = self._get(endpoint, params={"ref": branch})

        # 如果返回空字典或404错误，尝试其他分支
        if not result or (isinstance(result, dict) and not result.get('type')):
            # 尝试 main 分支
            if branch == "master":
                print(f"⚠️  master 分支未找到内容，尝试 main 分支...")
                result = self._get(endpoint, params={"ref": "main"})

        # 确保返回列表格式
        if isinstance(result, list):
            return result
        elif isinstance(result, dict) and result.get('type') == 'file':
            # 如果是单个文件，包装成列表
            return [result]
        else:
            # 返回空列表而不是None
            print(f"⚠️  无法获取目录内容，返回空列表")
            return []

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

        由于 Gitee API 搜索功能已失效，现在使用网页搜索

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

        try:
            # 使用网页搜索器
            from .search import GiteeWebSearcher

            searcher = GiteeWebSearcher(headless=True, timeout=30000)

            # 默认翻页以获取更多结果（max_results=per_page*10）
            max_results = per_page * 10
            results = searcher.search(query, language, sort, order, per_page, max_results)

            if results:
                print(f"✅ 找到 {len(results)} 个仓库")

                # 如果需要排序，手动排序
                if sort and results:
                    reverse = (order == 'desc')
                    results.sort(key=lambda x: x.get(sort, 0), reverse=reverse)

            return results if results else []

        except ImportError as e:
            print(f"❌ 未安装搜索依赖: {e}")
            print("   请运行: pip install playwright && playwright install chromium")
            return []
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            # 降级：尝试使用原有的 API 搜索（可能失败）
            print("   尝试使用 API 搜索...")
            return self._search_via_api(query, language, sort, order, per_page)

    def _search_via_api(
        self,
        query: str,
        language: Optional[str] = None,
        sort: str = "stars",
        order: str = "desc",
        per_page: int = 10
    ) -> List[Dict]:
        """
        通过 API 搜索仓库（已失效，作为降级方案）

        Args:
            query: 搜索关键词
            language: 编程语言过滤
            sort: 排序方式 (stars, forks, updated)
            order: 排序顺序 (desc, asc)
            per_page: 每页结果数量 (最大100)

        Returns:
            仓库列表
        """
        # 构建搜索查询
        search_query = query
        if language:
            search_query = f"{query} language:{language}"

        # Gitee API 不支持 sort 和 order 参数
        # 如果需要排序，会在获取结果后手动排序
        params = {
            "q": search_query,
            "per_page": per_page
        }

        endpoint = "/search/repositories"

        try:
            result = self._get(endpoint, params)
            # 确保返回列表
            if isinstance(result, dict):
                # 如果返回的是字典，可能包含错误信息
                if 'message' in result or 'error' in result:
                    print(f"⚠️  API 返回错误: {result}")
                    return []
                # 有些情况可能返回 {'items': [...]}
                if 'items' in result:
                    items = result['items']
                    print(f"✅ API 找到 {len(items)} 个仓库")
                    return items
                print(f"⚠️  API 返回未知格式: {result}")
                return []

            if result:
                print(f"✅ API 找到 {len(result)} 个仓库")
            return result if result else []
        except Exception as e:
            print(f"❌ API 搜索请求异常: {e}")
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
