#!/usr/bin/env python3
"""
爬虫基类模块
定义所有平台爬虫的统一接口
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from core.base_api import BaseAPI


class BaseCrawler(ABC):
    """
    爬虫基类
    所有平台爬虫都应该继承此类并实现抽象方法
    """

    def __init__(self, api: BaseAPI):
        """
        初始化爬虫

        Args:
            api: API 客户端实例
        """
        self.api = api

    @abstractmethod
    def crawl_repo_files(
        self,
        owner: str,
        repo: str,
        path: str = "",
        branch: str = "master",
        max_files: int = 100,
        file_extensions: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        递归爬取仓库中的所有代码文件

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            path: 起始路径，空字符串表示根目录
            branch: 分支名
            max_files: 最大文件数量限制
            file_extensions: 文件扩展名过滤列表

        Returns:
            字典，键为文件路径，值为文件内容
        """
        pass

    @abstractmethod
    def save_repo_files(
        self,
        owner: str,
        repo: str,
        output_dir: str = "./repo_files",
        path: str = "",
        branch: str = "master",
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
        pass
