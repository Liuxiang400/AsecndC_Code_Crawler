#!/usr/bin/env python3
"""
Gitee 网页搜索模块
由于 Gitee API 搜索功能已失效，使用浏览器自动化工具进行网页搜索
"""

import asyncio
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class GiteeWebSearcher:
    """Gitee 网页搜索器 - 使用 Playwright 进行浏览器自动化"""

    SEARCH_URL = "https://search.gitee.com/"

    def __init__(self, headless: bool = True, timeout: int = 30000, use_system_chrome: bool = True):
        """
        初始化搜索器

        Args:
            headless: 是否使用无头模式（不显示浏览器窗口）
            timeout: 页面加载超时时间（毫秒）
            use_system_chrome: 是否使用系统已安装的 Chrome（优先于 Playwright Chromium）
        """
        self.headless = headless
        self.timeout = timeout
        self.use_system_chrome = use_system_chrome
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

    def search(
        self,
        query: str,
        language: Optional[str] = None,
        sort: str = "stars",
        order: str = "desc",
        per_page: int = 10,
        max_results: Optional[int] = None
    ) -> List[Dict]:
        """
        同步搜索接口

        Args:
            query: 搜索关键词
            language: 编程语言过滤
            sort: 排序方式（stars, forks, updated）
            order: 排序顺序（desc, asc）
            per_page: 每页结果数量
            max_results: 最大结果数量（用于自动翻页，None 表示不翻页）

        Returns:
            仓库列表，每个仓库包含标准格式的字典
        """
        try:
            # 如果没有指定 max_results，默认使用 per_page（不翻页）
            if max_results is None:
                max_results = per_page

            return asyncio.run(self._search_async(query, language, sort, order, per_page, max_results))
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []

    async def _search_async(
        self,
        query: str,
        language: Optional[str] = None,
        sort: str = "stars",
        order: str = "desc",
        per_page: int = 10,
        max_results: int = 100
    ) -> List[Dict]:
        """异步搜索实现（支持自动翻页）"""
        try:
            from playwright.async_api import async_playwright, Page
        except ImportError:
            logger.error("未安装 playwright，请运行: pip install playwright && playwright install chromium")
            return []

        async with async_playwright() as p:
            # 启动浏览器
            if self.use_system_chrome:
                # 尝试使用系统已安装的 Chrome
                try:
                    # 在 macOS 上，Chrome 通常在 /Applications/Google Chrome.app/Contents/MacOS/Google Chrome
                    browser = await p.chromium.launch(
                        headless=self.headless,
                        channel="chrome",  # 使用系统 Chrome
                        args=[
                            '--disable-blink-features=AutomationControlled',
                            '--no-sandbox',
                            '--disable-setuid-sandbox'
                        ]
                    )
                    logger.info("使用系统 Chrome 浏览器")
                except Exception as e:
                    logger.warning(f"无法启动系统 Chrome: {e}，尝试使用 Playwright Chromium")
                    browser = await p.chromium.launch(headless=self.headless)
            else:
                browser = await p.chromium.launch(headless=self.headless)

            page = await browser.new_page()

            # 设置用户代理
            await page.set_extra_http_headers({
                "User-Agent": self.user_agent,
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
            })

            try:
                # 构建搜索 URL
                url = self._build_search_url(query, language)
                logger.info(f"正在搜索: {url}")
                logger.info(f"目标结果数: {max_results}（启用自动翻页）")

                # 访问搜索页面
                await page.goto(url, wait_until="networkidle", timeout=self.timeout)

                # 等待搜索结果加载
                await self._wait_for_results(page)

                # 收集所有结果（支持翻页）
                results = await self._parse_search_results_with_pagination(
                    page, per_page, max_results
                )

                logger.info(f"✅ 共找到 {len(results)} 个仓库")
                return results

            except Exception as e:
                logger.error(f"搜索过程出错: {e}", exc_info=True)
                return []

            finally:
                await browser.close()

    def _build_search_url(self, query: str, language: Optional[str] = None) -> str:
        """构建搜索 URL"""
        params = {
            "skin": "rec",
            "type": "repository",
            "q": query
        }
        param_str = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.SEARCH_URL}?{param_str}"

    async def _wait_for_results(self, page):
        """等待搜索结果加载"""
        # 等待搜索结果容器出现
        # 多种可能的选择器，按优先级尝试
        selectors = [
            ".search-result-item",      # 可能的选择器1
            ".repo-list-item",          # 可能的选择器2
            "[class*='repo-item']",     # 可能的选择器3
            "[class*='search-item']",   # 可能的选择器4
            ".repo-item",               # 可能的选择器5
            "[class*='item']",          # 可能的选择器6
        ]

        for selector in selectors:
            try:
                await page.wait_for_selector(selector, timeout=5000)
                logger.debug(f"使用选择器: {selector}")
                return
            except:
                continue

        # 如果所有选择器都失败，使用固定等待
        logger.warning("未找到明确的搜索结果选择器，使用固定等待时间")
        await asyncio.sleep(3)

    async def _parse_search_results(self, page, per_page: int) -> List[Dict]:
        """解析搜索结果"""
        results = []

        # Gitee 搜索页面使用 Bootstrap 卡片布局
        # 选择器：.card
        selectors = [
            ".card",  # Bootstrap 卡片（最常用）
        ]

        items = None
        for selector in selectors:
            try:
                items = await page.query_selector_all(selector)
                if items:
                    logger.info(f"使用选择器 '{selector}' 找到 {len(items)} 个结果")
                    break
            except Exception as e:
                logger.debug(f"选择器 '{selector}' 失败: {e}")
                continue

        if not items:
            logger.warning("未找到搜索结果，可能页面结构已变化")

            # 尝试获取页面文本进行调试
            try:
                page_text = await page.inner_text("body")
                logger.debug(f"页面内容预览: {page_text[:500]}...")
            except:
                pass

            return []

        # 解析每个结果项
        for i, item in enumerate(items[:per_page]):
            try:
                repo_data = await self._parse_repo_item(item, i)
                if repo_data:
                    results.append(repo_data)
            except Exception as e:
                logger.warning(f"解析第 {i+1} 个结果失败: {e}")
                continue

        return results

    async def _parse_repo_item(self, item, index: int) -> Optional[Dict]:
        """
        解析单个仓库项

        Args:
            item: Playwright 元素对象
            index: 结果索引（用于调试）

        Returns:
            仓库信息字典，如果解析失败返回 None
        """
        try:
            # 从卡片中提取标题链接
            # Gitee 搜索页面的卡片结构：
            # <div class="card">
            #   <a class="title" href="/owner/repo">仓库名</a>
            #   <div class="outline">描述</div>
            # </div>

            link_elem = await item.query_selector("a.title")
            if not link_elem:
                # 备选方案：查找第一个链接
                link_elem = await item.query_selector("a")

            if not link_elem:
                logger.debug(f"卡片 {index}: 未找到链接元素")
                return None

            href = await link_elem.get_attribute("href")
            name_text = await link_elem.inner_text()

            if not href or not name_text:
                logger.debug(f"卡片 {index}: 链接或文本为空")
                return None

            # 清理数据
            href = href.strip()
            name_text = name_text.strip()

            # 提取描述
            description = await self._extract_description_from_card(item)

            # 构建标准格式的仓库数据
            repo_data = {
                "full_name": self._extract_full_name_from_href(href),
                "name": self._extract_repo_name_from_text(name_text),
                "description": description,
                "stargazers_count": 0,  # Gitee 搜索页面不显示 stars
                "forks_count": 0,  # Gitee 搜索页面不显示 forks
                "html_url": self._build_html_url(href),
                "updated_at": "",  # Gitee 搜索页面不显示更新时间
            }

            logger.debug(f"解析仓库: {repo_data['full_name']}")
            return repo_data

        except Exception as e:
            logger.warning(f"解析仓库项失败 (索引 {index}): {e}")
            return None

    def _extract_full_name_from_href(self, href: str) -> str:
        """从 href 中提取完整仓库名"""
        # href 格式：/owner/repo 或 https://gitee.com/owner/repo
        if href.startswith("http"):
            # 从完整 URL 中提取
            parts = href.rstrip("/").split("/")
            if len(parts) >= 2:
                return f"{parts[-2]}/{parts[-1]}"
        else:
            # 从相对路径中提取 /owner/repo
            parts = href.strip("/").split("/")
            if len(parts) >= 2:
                return f"{parts[0]}/{parts[1]}"

        return href

    def _extract_repo_name_from_text(self, name_text: str) -> str:
        """从文本中提取仓库名（不含所有者）"""
        # name_text 可能包含所有者，格式如 "owner/repo" 或 "repo"
        if "/" in name_text:
            return name_text.split("/")[-1].strip()
        return name_text.strip()

    def _build_html_url(self, href: str) -> str:
        """构建完整的 HTML URL"""
        if href.startswith("http"):
            return href
        return f"https://gitee.com{href}"

    async def _extract_description_from_card(self, item) -> str:
        """从卡片中提取仓库描述"""
        try:
            # Gitee 搜索页面使用 .outline 类来显示描述
            desc_elem = await item.query_selector(".outline")
            if desc_elem:
                text = await desc_elem.inner_text()
                if text and text.strip():
                    return text.strip()

            # 备选方案：查找卡片中的文本段落
            text_elem = await item.query_selector(".card-text")
            if text_elem:
                text = await text_elem.inner_text()
                if text and text.strip():
                    return text.strip()

        except Exception as e:
            logger.debug(f"提取描述失败: {e}")

    async def _parse_search_results_with_pagination(
        self, page, per_page: int, max_results: int
    ) -> List[Dict]:
        """
        解析搜索结果（支持自动翻页）

        Args:
            page: Playwright 页面对象
            per_page: 每页结果数量
            max_results: 最大结果数量

        Returns:
            仓库列表
        """
        all_results = []
        page_num = 1
        has_next_page = True
        seen_urls = set()  # 用于去重

        while has_next_page and len(all_results) < max_results:
            logger.info(f"正在解析第 {page_num} 页...")

            # 解析当前页的结果
            page_results = await self._parse_search_results(page, per_page)

            # 去重：只添加未见过的新结果
            new_results = []
            for result in page_results:
                result_url = result.get('html_url', '')
                if result_url and result_url not in seen_urls:
                    seen_urls.add(result_url)
                    new_results.append(result)

            all_results.extend(new_results)
            logger.info(f"第 {page_num} 页找到 {len(new_results)} 个新结果（累计: {len(all_results)}）")

            # 检查是否已达到最大结果数
            if len(all_results) >= max_results:
                logger.info(f"已达到最大结果数 {max_results}，停止翻页")
                break

            # 尝试点击"下一页"按钮
            has_next_page = await self._click_next_page(page)

            if has_next_page:
                page_num += 1
                # 等待新页面加载
                await asyncio.sleep(1)
                await self._wait_for_results(page)
            else:
                logger.info(f"没有更多页面了，共搜索了 {page_num} 页")

        return all_results[:max_results]

    async def _click_next_page(self, page) -> bool:
        """
        尝试点击"下一页"按钮

        Args:
            page: Playwright 页面对象

        Returns:
            是否成功点击到下一页
        """
        try:
            # Gitee 可能的"下一页"按钮选择器
            next_button_selectors = [
                'a[aria-label="Next"]',  # 常见的 Next 按钮
                'a.next',  # 简单的 next 类
                'li.next a',  # Bootstrap 风格的分页
                'a[rel="next"]',  # 标准 rel="next"
                '.pagination .next:not(.disabled)',  # Bootstrap 分页
                '.page-next',  # 自定义类名
            ]

            for selector in next_button_selectors:
                try:
                    # 查找"下一页"按钮
                    next_button = await page.query_selector(selector)

                    if not next_button:
                        continue

                    # 检查按钮是否可点击（没有 disabled 类）
                    is_disabled = await page.evaluate(
                        '''(element) => {
                            return element.classList.contains('disabled') ||
                                   element.hasAttribute('disabled') ||
                                   element.style.display === 'none' ||
                                   element.style.visibility === 'hidden';
                        }''',
                        next_button
                    )

                    if is_disabled:
                        logger.debug(f"下一页按钮已禁用: {selector}")
                        continue

                    # 滚动到按钮位置
                    await next_button.scroll_into_view_if_needed()
                    await asyncio.sleep(0.5)

                    # 点击按钮
                    await next_button.click(timeout=5000)
                    logger.info(f"成功点击下一页按钮（使用选择器: {selector}）")
                    return True

                except Exception as e:
                    logger.debug(f"尝试选择器 '{selector}' 失败: {e}")
                    continue

            # 如果所有选择器都失败，尝试通过查找页码来翻页
            logger.debug("尝试通过页码翻页")
            return await self._click_page_number(page)

        except Exception as e:
            logger.debug(f"点击下一页失败: {e}")
            return False

    async def _click_page_number(self, page) -> bool:
        """
        尝试通过点击页码来翻页
        查找当前激活的页码，然后点击下一个页码

        Args:
            page: Playwright 页面对象

        Returns:
            是否成功翻页
        """
        try:
            # 查找所有页码按钮
            page_number_selectors = [
                '.pagination a.page-link',
                '.pagination li a',
                '.pager a',
            ]

            for selector in page_number_selectors:
                try:
                    page_links = await page.query_selector_all(selector)
                    if not page_links:
                        continue

                    # 查找当前激活的页码
                    current_page_num = None
                    next_page_link = None

                    for link in page_links:
                        text = await link.inner_text()
                        text = text.strip()

                        # 检查是否是激活状态
                        is_active = await page.evaluate(
                            '''(element) => {
                                return element.classList.contains('active') ||
                                       element.parentElement.classList.contains('active');
                            }''',
                            link
                        )

                        if is_active and text.isdigit():
                            current_page_num = int(text)
                            # 下一个页码应该是当前页码 + 1
                            break

                    if current_page_num is not None:
                        # 查找下一页的链接
                        for link in page_links:
                            text = await link.inner_text()
                            text = text.strip()

                            if text.isdigit() and int(text) == current_page_num + 1:
                                await link.scroll_into_view_if_needed()
                                await asyncio.sleep(0.5)
                                await link.click(timeout=5000)
                                logger.info(f"成功点击页码 {text}")
                                return True

                except Exception as e:
                    logger.debug(f"通过页码翻页失败: {e}")
                    continue

        except Exception as e:
            logger.debug(f"页码翻页失败: {e}")

        return False
