#!/usr/bin/env python3
"""
API 基类模块
定义所有平台 API 客户端的统一接口
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class BaseAPI(ABC):
    """
    API 客户端基类
    所有平台 API 客户端都应该继承此类并实现抽象方法
    """

    @abstractmethod
    def get_repo(self, owner: str, repo: str) -> Dict:
        """
        获取仓库信息

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            仓库信息字典
        """
        pass

    @abstractmethod
    def get_repo_readme(self, owner: str, repo: str) -> Dict:
        """
        获取仓库的README内容

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            README内容
        """
        pass

    @abstractmethod
    def get_repo_issues(
        self, owner: str, repo: str, state: str = "open"
    ) -> List[Dict]:
        """
        获取仓库的Issues

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            state: 状态，open或closed

        Returns:
            Issue列表
        """
        pass

    @abstractmethod
    def get_repo_contents(
        self, owner: str, repo: str, path: str = "", branch: str = "master"
    ) -> List[Dict]:
        """
        获取仓库目录内容（文件和文件夹列表）

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            path: 目录路径，空字符串表示根目录
            branch: 分支名

        Returns:
            文件/目录列表
        """
        pass

    @abstractmethod
    def get_file_content(
        self, owner: str, repo: str, path: str, branch: str = "master"
    ) -> Optional[Dict]:
        """
        获取单个文件的内容

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            path: 文件路径
            branch: 分支名

        Returns:
            包含文件信息的字典
        """
        pass

    @abstractmethod
    def search_repositories(
        self,
        query: str,
        language: Optional[str] = None,
        sort: str = "stars",
        order: str = "desc",
        per_page: int = 10,
    ) -> List[Dict]:
        """
        搜索仓库

        Args:
            query: 搜索关键词
            language: 编程语言过滤
            sort: 排序方式
            order: 排序顺序
            per_page: 每页结果数量

        Returns:
            仓库列表
        """
        pass

    def get_repo_readme_decoded(self, owner: str, repo: str) -> Optional[Dict]:
        """
        获取仓库的README内容（解码后）

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            README内容（含解码后的字段）
        """
        result = self.get_repo_readme(owner, repo)
        if result and "content" in result:
            # 默认实现，子类可以覆盖
            return result
        return result
