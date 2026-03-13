#!/usr/bin/env python3
"""
核心抽象层模块
提供 API 和爬虫的基类定义
"""

from .base_api import BaseAPI
from .base_crawler import BaseCrawler

__all__ = ['BaseAPI', 'BaseCrawler']
