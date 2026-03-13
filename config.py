#!/usr/bin/env python3
"""
配置管理模块
提供配置加载、验证和管理功能
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any


class Config:
    """配置管理类"""

    # 默认配置
    DEFAULTS = {
        # 平台设置 (新增)
        'platform': 'gitee',  # 可选值: 'gitee', 'github'

        # 认证设置
        'gitee_access_token': None,
        'gitee_client_id': None,
        'gitee_client_secret': None,
        'github_access_token': None,
        'github_client_id': None,
        'github_client_secret': None,

        # 爬取限制
        'max_repos': 10,
        'max_files_per_repo': 100,

        # 仓库过滤
        'min_stars': 0,
        'min_forks': 0,
        'days_since_update': 365,

        # 文件设置
        'file_extensions': [
            '.py', '.md', '.txt', '.cpp',
            '.c', '.h', '.hpp', '.json',
            '.yaml', '.yml'
        ],
        'branch': 'master',  # GitHub 默认使用 'main'

        # 输出设置
        'output_dir': 'output/ascendc',
        'results_dir': 'output/results',

        # 搜索设置
        'search_keywords': ['AscendC', 'CANN', '算子开发', 'Ascend', '昇腾'],
        'search_language': None,
        'search_sort': 'stars',
        'search_order': 'desc',

        # 性能设置
        'request_timeout': 10,
        'retry_times': 3,
        'request_delay': 0.5,

        # 日志设置
        'log_level': 'INFO',
        'log_file': 'logs/ascendc_crawler.log',
    }

    def __init__(self, config_dict: Optional[Dict] = None):
     
        self.config = self.DEFAULTS.copy()

        if config_dict:
            self._validate_and_update(config_dict)

        # 创建必要的目录
        self._create_directories()

    def _validate_and_update(self, config_dict: Dict):
        """验证并更新配置"""
        # 验证平台设置
        if 'platform' in config_dict:
            if config_dict['platform'] not in ['gitee', 'github']:
                raise ValueError("platform 必须是 'gitee' 或 'github'")
            self.config['platform'] = config_dict['platform']

        # 验证数值范围
        numeric_fields = {
            'max_repos': (1, 1000),
            'max_files_per_repo': (1, 10000),
            'min_stars': (0, 100000),
            'min_forks': (0, 100000),
            'days_since_update': (1, 3650),
            'request_timeout': (1, 120),
            'retry_times': (0, 10),
        }

        for field, (min_val, max_val) in numeric_fields.items():
            if field in config_dict:
                value = config_dict[field]
                if not isinstance(value, int) or not (min_val <= value <= max_val):
                    raise ValueError(
                        f"配置项 {field} 必须在 {min_val}-{max_val} 之间"
                    )
                self.config[field] = value

        # 验证字符串字段
        string_fields = ['branch', 'search_language', 'search_sort', 'search_order', 'log_level']
        for field in string_fields:
            if field in config_dict:
                value = config_dict[field]
                if value is not None and not isinstance(value, str):
                    raise ValueError(f"配置项 {field} 必须是字符串")
                self.config[field] = value

        # 验证列表字段
        list_fields = ['file_extensions', 'search_keywords']
        for field in list_fields:
            if field in config_dict:
                value = config_dict[field]
                if not isinstance(value, list):
                    raise ValueError(f"配置项 {field} 必须是列表")
                self.config[field] = value

        # 验证路径字段
        path_fields = ['output_dir', 'results_dir', 'log_file']
        for field in path_fields:
            if field in config_dict:
                value = config_dict[field]
                if not isinstance(value, str):
                    raise ValueError(f"配置项 {field} 必须是字符串路径")
                self.config[field] = value

    def _create_directories(self):
        """创建必要的目录"""
        directories = [
            self.config['output_dir'],
            self.config['results_dir'],
            os.path.dirname(self.config['log_file'])
        ]

        for directory in directories:
            if directory:
                Path(directory).mkdir(parents=True, exist_ok=True)

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """
        设置配置项

        Args:
            key: 配置键
            value: 配置值
        """
        self.config[key] = value

    def to_dict(self) -> Dict:
        """转换为字典"""
        return self.config.copy()

    def save(self, file_path: str):
        """
        保存配置到文件

        Args:
            file_path: 配置文件路径
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, file_path: str) -> 'Config':
        """
        从文件加载配置

        Args:
            file_path: 配置文件路径

        Returns:
            Config 实例
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        return cls(config_dict)

    @classmethod
    def from_env(cls) -> 'Config':
        """
        从环境变量加载配置

        支持的环境变量:
        平台设置:
        - CRAWL_PLATFORM: 平台选择 (gitee/github)

        Gitee 认证:
        - GITEE_ACCESS_TOKEN: Gitee 访问令牌
        - GITEE_CLIENT_ID: Gitee OAuth 客户端ID
        - GITEE_CLIENT_SECRET: Gitee OAuth 客户端密钥

        GitHub 认证:
        - GITHUB_ACCESS_TOKEN: GitHub 访问令牌
        - GITHUB_CLIENT_ID: GitHub OAuth 客户端ID
        - GITHUB_CLIENT_SECRET: GitHub OAuth 客户端密钥

        爬虫设置:
        - ASCENDC_MAX_REPOS: 最大仓库数
        - ASCENDC_MAX_FILES: 每个仓库最大文件数
        - ASCENDC_MIN_STARS: 最小 stars 数
        - ASCENDC_OUTPUT_DIR: 输出目录
        - ASCENDC_LOG_LEVEL: 日志级别

        Returns:
            Config 实例
        """
        config_dict = {}

        # 平台设置
        platform = os.getenv('CRAWL_PLATFORM', '').lower()
        if platform in ['gitee', 'github']:
            config_dict['platform'] = platform

        # 认证设置
        if os.getenv('GITEE_ACCESS_TOKEN'):
            config_dict['gitee_access_token'] = os.getenv('GITEE_ACCESS_TOKEN')
        if os.getenv('GITEE_CLIENT_ID'):
            config_dict['gitee_client_id'] = os.getenv('GITEE_CLIENT_ID')
        if os.getenv('GITEE_CLIENT_SECRET'):
            config_dict['gitee_client_secret'] = os.getenv('GITEE_CLIENT_SECRET')
        if os.getenv('GITHUB_ACCESS_TOKEN'):
            config_dict['github_access_token'] = os.getenv('GITHUB_ACCESS_TOKEN')
        if os.getenv('GITHUB_CLIENT_ID'):
            config_dict['github_client_id'] = os.getenv('GITHUB_CLIENT_ID')
        if os.getenv('GITHUB_CLIENT_SECRET'):
            config_dict['github_client_secret'] = os.getenv('GITHUB_CLIENT_SECRET')

        # 爬虫设置
        env_mappings = {
            'ASCENDC_MAX_REPOS': 'max_repos',
            'ASCENDC_MAX_FILES': 'max_files_per_repo',
            'ASCENDC_MIN_STARS': 'min_stars',
            'ASCENDC_MIN_FORKS': 'min_forks',
            'ASCENDC_OUTPUT_DIR': 'output_dir',
            'ASCENDC_LOG_LEVEL': 'log_level',
        }

        for env_key, config_key in env_mappings.items():
            value = os.getenv(env_key)
            if value:
                # 尝试转换为整数
                try:
                    config_dict[config_key] = int(value)
                except ValueError:
                    config_dict[config_key] = value

        return cls(config_dict)

    def __getitem__(self, key: str) -> Any:
        """支持字典式访问"""
        return self.config[key]

    def __setitem__(self, key: str, value: Any):
        """支持字典式设置"""
        self.config[key] = value

    def __repr__(self) -> str:
        """字符串表示"""
        return f"Config({json.dumps(self.config, ensure_ascii=False)})"


def create_default_config(output_file: str = 'config.json'):
    """
    创建默认配置文件

    Args:
        output_file: 输出文件路径
    """
    config = Config()
    config.save(output_file)
    print(f"默认配置已保存到: {output_file}")


if __name__ == '__main__':
    # 创建示例配置文件
    example_config = {
        'max_repos': 20,
        'max_files_per_repo': 200,
        'min_stars': 5,
        'min_forks': 2,
        'days_since_update': 180,
        'file_extensions': ['.py', '.cpp', '.h', '.md', '.ascendc'],
        'output_dir': 'output/ascendc',
        'results_dir': 'output/results',
        'search_keywords': ['AscendC', 'CANN', '算子开发'],
        'log_level': 'INFO'
    }

    config = Config(example_config)
    config.save('config_example.json')
    print("示例配置文件已创建: config_example.json")
