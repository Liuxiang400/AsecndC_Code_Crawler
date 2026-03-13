#!/usr/bin/env python3
"""
AscendC 代码爬虫入口程序
支持命令行参数、配置文件、断点续传等功能
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Optional
from datetime import datetime
from crawl_ascendC import AscendCCrawler, setup_logger, logger


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='AscendC 代码爬虫 - 从 Gitee/GitHub 爬取 AscendC 相关代码',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # 平台选择
    parser.add_argument(
        '--platform',
        '-p',
        type=str,
        choices=['gitee', 'github'],
        default='gitee',
        help='选择平台 (gitee/github, 默认: gitee)'
    )

    # 搜索选项
    parser.add_argument(
        '--keywords',
        type=str,
        help='搜索关键词,逗号分隔 (默认: AscendC,CANN,算子开发,Ascend,昇腾)'
    )
    parser.add_argument(
        '--language',
        type=str,
        help='编程语言过滤 (例如: python, cpp)'
    )
    parser.add_argument(
        '--min-stars',
        type=int,
        default=0,
        help='最小 stars 数 (默认: 0)'
    )
    parser.add_argument(
        '--min-forks',
        type=int,
        default=0,
        help='最小 forks 数 (默认: 0)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=365,
        help='最近N天内更新 (默认: 365)'
    )

    # 爬取选项
    parser.add_argument(
        '--max-repos',
        type=int,
        default=10,
        help='最大爬取仓库数 (默认: 10)'
    )
    parser.add_argument(
        '--max-files',
        type=int,
        default=100,
        help='每个仓库最大文件数 (默认: 100)'
    )
    parser.add_argument(
        '--branch',
        type=str,
        default='master',
        help='Git 分支名 (默认: master)'
    )
    parser.add_argument(
        '--extensions',
        type=str,
        help='文件扩展名过滤,逗号分隔 (例如: .py,.cpp,.h)'
    )

    # 输出选项
    parser.add_argument(
        '--output-dir',
        type=str,
        default='output/ascendc',
        help='输出目录 (默认: output/ascendc)'
    )
    parser.add_argument(
        '--results-dir',
        type=str,
        default='output/results',
        help='结果目录 (默认: output/results)'
    )

    # 运行模式
    parser.add_argument(
        '--search-only',
        action='store_true',
        help='只搜索不下载'
    )
    parser.add_argument(
        '--resume',
        type=str,
        metavar='FILE',
        help='从指定的进度文件恢复'
    )
    parser.add_argument(
        '--config',
        type=str,
        metavar='FILE',
        help='从配置文件加载设置'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='模拟运行,不实际下载'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='显示详细日志'
    )

    return parser.parse_args()


def load_config_file(config_file: str) -> dict:
    """从文件加载配置"""
    config_path = Path(config_file)
    if not config_path.exists():
        logger.error(f"配置文件不存在: {config_file}")
        sys.exit(1)

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        sys.exit(1)


def load_resume_file(resume_file: str) -> tuple:
    """从进度文件恢复"""
    resume_path = Path(resume_file)
    if not resume_path.exists():
        logger.error(f"进度文件不存在: {resume_file}")
        sys.exit(1)

    try:
        with open(resume_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('repos_info', []), data.get('stats', {})
    except Exception as e:
        logger.error(f"加载进度文件失败: {e}")
        sys.exit(1)


def build_config_from_args(args) -> dict:
    """从命令行参数构建配置"""
    config = {
        'platform': args.platform,  # 添加平台配置
        'max_repos': args.max_repos,
        'max_files_per_repo': args.max_files,
        'min_stars': args.min_stars,
        'min_forks': args.min_forks,
        'days_since_update': args.days,
        'output_dir': args.output_dir,
        'results_dir': args.results_dir,
        'branch': args.branch
    }

    # 解析文件扩展名
    if args.extensions:
        extensions = [ext.strip() for ext in args.extensions.split(',')]
        config['file_extensions'] = extensions

    return config


def print_banner(platform: str = 'gitee'):
    """打印程序横幅"""
    platform_name = platform.upper()
    print("\n" + "=" * 70)
    print(" " * 15 + "AscendC 代码爬虫 v1.0")
    print(" " * 10 + f"从 {platform_name} 爬取 AscendC 相关代码仓库")
    print("=" * 70)


def print_summary(crawler: AscendCCrawler, repos: list, results: dict):
    """打印爬取摘要"""
    print("\n" + "=" * 70)
    print("爬取完成摘要")
    print("=" * 70)

    # 统计信息
    stats = crawler.stats
    print(f"\n📊 统计信息:")
    print(f"   搜索仓库数: {stats['repos_searched']}")
    print(f"   爬取仓库数: {stats['repos_crawled']}")
    print(f"   获取文件数: {stats['files_crawled']}")

    # 计算执行时长（处理字符串格式的 datetime）
    try:
        start_time = stats.get('start_time')
        end_time = stats.get('end_time')

        if start_time and end_time:
            # 如果是字符串格式，转换为 datetime 对象
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time)

            duration = (end_time - start_time).total_seconds()
            print(f"   执行时长: {duration:.2f} 秒")
        else:
            print("   执行时长: N/A")
    except Exception as e:
        print(f"   执行时长: 计算失败 ({e})")

    if stats['errors']:
        print(f"\n⚠️  错误数量: {len(stats['errors'])}")
        for error in stats['errors'][:5]:
            print(f"   - {error}")

    # 仓库列表
    print(f"\n📦 爬取的仓库:")
    for i, (repo_name, files) in enumerate(results.items(), 1):
        print(f"   {i}. {repo_name} ({len(files)} 个文件)")


def main():
    """主函数"""
    args = parse_args()
    print_banner(args.platform)

    # 设置日志级别
    if args.verbose:
        import logging
        logging.getLogger('AscendCCrawler').setLevel(logging.DEBUG)

    # 加载配置
    if args.config:
        logger.info(f"从配置文件加载: {args.config}")
        config = load_config_file(args.config)
    else:
        config = build_config_from_args(args)

    # 创建爬虫实例
    crawler = AscendCCrawler(config=config)

    # 恢复模式
    if args.resume:
        logger.info(f"从进度文件恢复: {args.resume}")
        repos, saved_stats = load_resume_file(args.resume)
        crawler.stats.update(saved_stats)
    else:
        # 搜索仓库
        keywords = None
        if args.keywords:
            keywords = [k.strip() for k in args.keywords.split(',')]

        logger.info("开始搜索 AscendC 相关仓库...")
        repos = crawler.search_ascendc_repos(
            keywords=keywords,
            language=args.language,
            sort='stars',
            order='desc'
        )

        if not repos:
            print("\n❌ 未找到符合条件的仓库")
            sys.exit(1)

        print(f"\n✅ 找到 {len(repos)} 个仓库:")
        for i, repo in enumerate(repos[:10], 1):
            stars = repo.get('stargazers_count', 0)
            full_name = repo.get('full_name', '')
            description = repo.get('description') or 'N/A'
            description = str(description)[:50] if description else 'N/A'
            print(f"   {i:2d}. {full_name} ⭐ {stars}")
            print(f"       {description}...")

    # 只搜索模式
    if args.search_only or args.dry_run:
        print("\n✅ 搜索完成 (--search-only 或 --dry-run 模式)")
        return

    # 确认开始爬取
    print(f"\n准备爬取 {len(repos)} 个仓库...")
    response = input("是否继续? (y/n): ").strip().lower()
    if response != 'y':
        print("已取消")
        sys.exit(0)

    # 批量爬取
    print("\n📥 开始爬取代码文件...")
    results = crawler.crawl_multiple_repos(
        repos=repos,
        output_dir=args.output_dir,
        save_progress=True
    )

    # 记录结束时间
    crawler.stats['end_time'] = datetime.now()

    # 生成报告
    print("\n📊 生成爬取报告...")
    report_file = crawler.generate_report(results)
    print(f"   报告已保存: {report_file}")

    # 打印摘要
    print_summary(crawler, repos, results)

    print("\n✅ 全部完成!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(130)
    except Exception as e:
        logger.error(f"程序异常: {e}", exc_info=True)
        sys.exit(1)
