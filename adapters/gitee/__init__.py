#!/usr/bin/env python3
"""
Gitee 平台适配器模块
提供 Gitee API 和爬虫的实现
"""

from .api import GiteeAPI
from .crawler import GiteeCrawler
from .oauth import GiteeOAuth
from .search import GiteeWebSearcher

__all__ = ['GiteeAPI', 'GiteeCrawler', 'GiteeOAuth', 'GiteeWebSearcher']
