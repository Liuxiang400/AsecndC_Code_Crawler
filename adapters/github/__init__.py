#!/usr/bin/env python3
"""
GitHub 平台适配器模块
提供 GitHub API 和爬虫的实现
"""

from .api import GitHubAPI
from .crawler import GitHubCrawler
from .oauth import GitHubOAuth

__all__ = ['GitHubAPI', 'GitHubCrawler', 'GitHubOAuth']
