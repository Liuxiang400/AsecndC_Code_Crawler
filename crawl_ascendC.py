#!/usr/bin/env python3
"""
AscendC 专用爬虫模块
提供增强的搜索、批量爬取、进度跟踪等功能
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from adapters.gitee import GiteeAPI
from adapters.gitee import GiteeCrawler
from adapters.gitee import GiteeOAuth
from adapters.github import GitHubAPI
from adapters.github import GitHubCrawler
from adapters.github import GitHubOAuth


# 配置日志
def setup_logger(name: str, log_file: str, level=logging.INFO) -> logging.Logger:
    """配置日志记录器"""
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# 创建日志目录
os.makedirs('logs', exist_ok=True)
logger = setup_logger('AscendCCrawler', 'logs/ascendc_crawler.log')


class AscendCCrawler:
    """AscendC 专用爬虫类"""

    # AscendC 相关搜索关键词
    SEARCH_KEYWORDS = ['AscendC', 'CANN', '算子开发', 'Ascend', '昇腾']

    # 支持的文件扩展名
    FILE_EXTENSIONS = ['.py', '.md', '.txt', '.cpp', '.c', '.h', '.hpp',
                       '.json', '.yaml', '.yml', '.ascendc']

    # 默认配置
    DEFAULT_CONFIG = {
        'max_repos': 10,
        'max_files_per_repo': 100,
        'min_stars': 0,
        'min_forks': 0,
        'days_since_update': 365,
        'output_dir': 'output/ascendc',
        'results_dir': 'output/results',
        'file_extensions': FILE_EXTENSIONS,
        'branch': 'master'
    }

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化爬虫

        Args:
            config: 配置字典,覆盖默认配置
        """
        load_dotenv()

        # 合并配置
        self.config = self.DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)

        # 根据平台调整默认分支名
        platform = self.config.get('platform', 'gitee').lower()
        if 'branch' not in config or not config.get('branch'):
            # 如果用户没有指定分支,则根据平台设置默认分支
            if platform == 'github':
                self.config['branch'] = 'main'
                logger.info("使用 GitHub 平台,默认分支: main")
            else:
                self.config['branch'] = 'master'
                logger.info("使用 Gitee 平台,默认分支: master")

        # 初始化 API 客户端
        self.api = self._init_api()

        # 根据平台初始化对应的 Crawler
        if platform == 'github':
            self.crawler = GitHubCrawler(self.api)
            logger.info("使用 GitHub Crawler")
        else:
            self.crawler = GiteeCrawler(self.api)
            logger.info("使用 Gitee Crawler")

        # 统计信息
        self.stats = {
            'repos_searched': 0,
            'repos_crawled': 0,
            'files_crawled': 0,
            'errors': [],
            'start_time': datetime.now().isoformat(),  # 存储为字符串避免序列化问题
            'platform': platform
        }

        logger.info(f"AscendC 爬虫初始化完成 (平台: {platform})")

    def _init_api(self):
        """根据平台配置初始化对应的 API 客户端"""
        platform = self.config.get('platform', 'gitee').lower()

        if platform == 'github':
            return self._init_github_api()
        else:
            return self._init_gitee_api()

    def _init_gitee_api(self) -> GiteeAPI:
        """初始化 Gitee API 客户端"""
        # 优先使用 OAuth
        client_id = os.getenv('GITEE_CLIENT_ID')
        client_secret = os.getenv('GITEE_CLIENT_SECRET')

        if client_id and client_secret:
            oauth = GiteeOAuth(
                client_id=client_id,
                client_secret=client_secret,
                scopes=['user_info', 'projects', 'pull_requests', 'issues', 'notes']
            )
            if oauth.load_from_file():
                logger.info("使用 Gitee OAuth 令牌")
                return GiteeAPI(oauth=oauth)

        # 使用 Access Token
        access_token = os.getenv('GITEE_ACCESS_TOKEN')
        if access_token:
            logger.info("使用 Gitee Access Token")
            return GiteeAPI(access_token=access_token)

        # 无认证
        logger.warning("未配置 Gitee 认证,使用匿名访问(速率限制较低)")
        return GiteeAPI()

    def _init_github_api(self) -> GitHubAPI:
        """初始化 GitHub API 客户端"""
        # 优先使用 OAuth
        client_id = os.getenv('GITHUB_CLIENT_ID')
        client_secret = os.getenv('GITHUB_CLIENT_SECRET')

        if client_id and client_secret:
            oauth = GitHubOAuth(
                client_id=client_id,
                client_secret=client_secret
            )
            if oauth.load_from_file():
                logger.info("使用 GitHub OAuth 令牌")
                return GitHubAPI(oauth=oauth)

        # 使用 Access Token
        access_token = os.getenv('GITHUB_ACCESS_TOKEN')
        if access_token:
            logger.info("使用 GitHub Access Token")
            return GitHubAPI(access_token=access_token)

        # 无认证
        logger.warning("未配置 GitHub 认证,使用匿名访问(速率限制较低)")
        return GitHubAPI()

    def search_ascendc_repos(
        self,
        keywords: Optional[List[str]] = None,
        language: Optional[str] = None,
        sort: str = 'stars',
        order: str = 'desc'
    ) -> List[Dict]:
    
        keywords = keywords or self.SEARCH_KEYWORDS
        all_repos = []

        logger.info(f"开始搜索 AscendC 相关仓库,关键词: {keywords}")

        for keyword in keywords:
            logger.info(f"搜索关键词: {keyword}")

            # 搜索仓库
            results = self.api.search_repositories(
                query=keyword,
                language=language,
                sort=sort,
                order=order,
                per_page=100
            )

            if isinstance(results, list):
                # 过滤符合条件的仓库
                filtered = self._filter_repos(results)
                all_repos.extend(filtered)
                logger.info(f"关键词 '{keyword}' 找到 {len(filtered)} 个符合条件的仓库")

        # 去重(基于 full_name)
        unique_repos = {}
        for repo in all_repos:
            full_name = repo.get('full_name')
            if full_name and full_name not in unique_repos:
                unique_repos[full_name] = repo

        # 按排序字段重新排序
        sorted_repos = sorted(
            unique_repos.values(),
            key=lambda x: x.get(sort, 0),
            reverse=(order == 'desc')
        )

        # 限制数量
        final_repos = sorted_repos[:self.config['max_repos']]

        self.stats['repos_searched'] = len(final_repos)
        logger.info(f"搜索完成,共找到 {len(final_repos)} 个仓库")

        return final_repos

    def _filter_repos(self, repos: List[Dict]) -> List[Dict]:
        """
        过滤仓库列表

        Args:
            repos: 仓库列表

        Returns:
            过滤后的仓库列表
        """
        filtered = []
        min_stars = self.config['min_stars']
        min_forks = self.config['min_forks']
        days_threshold = timedelta(days=self.config['days_since_update'])
        cutoff_date = datetime.now() - days_threshold

        for repo in repos:
            # 检查 stars
            if repo.get('stargazers_count', 0) < min_stars:
                continue

            # 检查 forks
            if repo.get('forks_count', 0) < min_forks:
                continue

            # 检查更新时间
            updated_str = repo.get('updated_at', '')
            if updated_str:
                try:
                    updated_date = datetime.fromisoformat(updated_str.replace('Z', '+00:00'))
                    if updated_date < cutoff_date:
                        continue
                except (ValueError, TypeError) as e:
                    logger.debug(f"无法解析更新时间 {updated_str}: {e}")

            filtered.append(repo)

        return filtered

    def crawl_single_repo(
        self,
        owner: str,
        repo: str,
        output_dir: Optional[str] = None
    ) -> Optional[Dict[str, str]]:

        output_dir = output_dir or self.config['output_dir']

        logger.info(f"开始爬取仓库: {owner}/{repo}")

        try:
            # 首先获取仓库信息以确定默认分支
            repo_info = self.api.get_repo(owner, repo)
            if not repo_info:
                logger.warning(f"⚠️  无法获取仓库信息: {owner}/{repo}")
                return None

            # 尝试检测默认分支
            default_branch = repo_info.get('default_branch') or self.config['branch']
            logger.info(f"仓库默认分支: {default_branch}")

            # 尝试使用配置的分支
            saved_files = self.crawler.save_repo_files(
                owner=owner,
                repo=repo,
                output_dir=output_dir,
                branch=self.config['branch'],
                max_files=self.config['max_files_per_repo'],
                file_extensions=self.config['file_extensions']
            )

            # 如果配置的分支失败，尝试使用默认分支
            if not saved_files and self.config['branch'] != default_branch:
                logger.info(f"配置的分支 {self.config['branch']} 未找到文件，尝试默认分支 {default_branch}")
                saved_files = self.crawler.save_repo_files(
                    owner=owner,
                    repo=repo,
                    output_dir=output_dir,
                    branch=default_branch,
                    max_files=self.config['max_files_per_repo'],
                    file_extensions=self.config['file_extensions']
                )

            if saved_files:
                self.stats['repos_crawled'] += 1
                self.stats['files_crawled'] += len(saved_files)
                logger.info(f"✅ 成功爬取 {owner}/{repo},获取 {len(saved_files)} 个文件")
            else:
                logger.warning(f"⚠️  仓库 {owner}/{repo} 未获取到文件")

            return saved_files

        except Exception as e:
            error_msg = f"爬取 {owner}/{repo} 失败: {str(e)}"
            logger.error(error_msg)
            self.stats['errors'].append(error_msg)
            return None

    def crawl_multiple_repos(
        self,
        repos: List[Dict],
        output_dir: Optional[str] = None,
        save_progress: bool = True
    ) -> Dict[str, Dict[str, str]]:

        output_dir = output_dir or self.config['output_dir']
        all_results = {}

        logger.info(f"开始批量爬取 {len(repos)} 个仓库")

        for i, repo in enumerate(repos, 1):
            full_name = repo.get('full_name', '')
            logger.info(f"[{i}/{len(repos)}] 处理仓库: {full_name}")

            # 解析 owner 和 repo
            parts = full_name.split('/')
            if len(parts) != 2:
                logger.warning(f"无效的仓库名: {full_name}")
                continue

            owner, repo_name = parts

            # 爬取仓库
            saved_files = self.crawl_single_repo(owner, repo_name, output_dir)

            if saved_files:
                all_results[full_name] = saved_files

            # 定期保存进度
            if save_progress and i % 5 == 0:
                self._save_progress(all_results, repos)

        # 最终保存进度
        if save_progress:
            self._save_progress(all_results, repos)

        logger.info(f"批量爬取完成,共处理 {len(repos)} 个仓库")
        return all_results

    def _save_progress(self, results: Dict, repos: List[Dict]):
        """保存爬取进度"""
        # 确保 stats 中的 datetime 对象转换为字符串
        stats_to_save = {}
        for key, value in self.stats.items():
            if isinstance(value, datetime):
                stats_to_save[key] = value.isoformat()
            else:
                stats_to_save[key] = value

        progress_data = {
            'timestamp': datetime.now().isoformat(),
            'stats': stats_to_save,
            'repos_info': repos,
            'results_summary': {
                repo_name: len(files)
                for repo_name, files in results.items()
            }
        }

        # 创建结果目录
        os.makedirs(self.config['results_dir'], exist_ok=True)

        # 保存进度文件
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        progress_file = os.path.join(
            self.config['results_dir'],
            f'crawl_progress_{timestamp_str}.json'
        )

        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)

        logger.info(f"进度已保存: {progress_file}")

    def generate_report(self, results: Dict[str, Dict[str, str]]) -> str:

        # 确保时间数据是字符串格式
        start_time = self.stats.get('start_time')
        end_time = self.stats.get('end_time')

        if isinstance(start_time, datetime):
            start_time = start_time.isoformat()
        if isinstance(end_time, datetime):
            end_time = end_time.isoformat()

        # 计算时长
        duration_seconds = 0
        if 'start_time' in self.stats:
            try:
                start = self.stats['start_time']
                if isinstance(start, str):
                    start = datetime.fromisoformat(start)
                end = self.stats.get('end_time', datetime.now())
                if isinstance(end, str):
                    end = datetime.fromisoformat(end)
                duration_seconds = (end - start).total_seconds()
            except Exception as e:
                logger.warning(f"计算时长失败: {e}")

        # 确保 stats 中的所有值都可以序列化
        stats_for_report = {}
        for key, value in self.stats.items():
            if isinstance(value, datetime):
                stats_for_report[key] = value.isoformat()
            else:
                stats_for_report[key] = value

        report_data = {
            'crawl_time': datetime.now().isoformat(),
            'configuration': self.config,
            'statistics': {
                'total_repos_searched': self.stats['repos_searched'],
                'total_repos_crawled': self.stats['repos_crawled'],
                'total_files_crawled': self.stats['files_crawled'],
                'duration_seconds': duration_seconds,
                'start_time': start_time,
                'end_time': end_time,
                'errors': self.stats['errors']
            },
            'repositories': []
        }

        # 添加每个仓库的详细信息
        for repo_name, files in results.items():
            repo_report = {
                'name': repo_name,
                'files_count': len(files),
                'file_types': self._analyze_file_types(files),
                'total_size': sum(
                    os.path.getsize(path)
                    for path in files.values()
                    if os.path.exists(path)
                )
            }
            report_data['repositories'].append(repo_report)

        # 保存报告
        os.makedirs(self.config['results_dir'], exist_ok=True)
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(
            self.config['results_dir'],
            f'crawl_report_{timestamp_str}.json'
        )

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        logger.info(f"报告已生成: {report_file}")
        return report_file

    def _analyze_file_types(self, files: Dict[str, str]) -> Dict[str, int]:
        """分析文件类型分布"""
        type_counts = {}
        for file_path in files.values():
            ext = os.path.splitext(file_path)[1].lower()
            type_counts[ext] = type_counts.get(ext, 0) + 1
        return type_counts

