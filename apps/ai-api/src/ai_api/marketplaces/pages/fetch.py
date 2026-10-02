"""Fetching pages with Crawl4AI: robots.txt honoured, a host's requests spaced out."""
from __future__ import annotations

import asyncio
import logging

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilterLXML
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from ... import config
from ..limiter import HostLimiter
from .page import Page

logger = logging.getLogger("ai_api.marketplaces")


class PageFetcher:
    """Fetches pages in one browser per call, waiting on the limiter before each request."""

    def __init__(self, limiter: HostLimiter) -> None:
        self._limiter = limiter

    def __call__(self, urls: list[str]) -> list[Page]:
        if not urls:
            return []
        return asyncio.run(self._fetch(urls))

    async def _fetch(self, urls: list[str]) -> list[Page]:
        run = _run_config()
        pages: list[Page] = []
        async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
            for url in urls:
                await asyncio.to_thread(self._limiter.wait, url)
                result = await crawler.arun(url=url, config=run)
                if not result.success:
                    logger.info("marketplaces: %s was not read: %s", url, result.error_message)
                    continue
                pages.append(Page(url=url, html=result.html or "", markdown=_text(result),
                                  links=_links(result)))
        return pages


def _run_config() -> CrawlerRunConfig:
    return CrawlerRunConfig(
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilterLXML(threshold=0.45, threshold_type="dynamic"),
            options={"ignore_links": True, "ignore_images": True},
        ),
        cache_mode=CacheMode.BYPASS,
        check_robots_txt=True,
        page_timeout=config.ALTERNATIVES_PAGE_TIMEOUT_S * 1000,
        remove_consent_popups=True,
        remove_overlay_elements=True,
        verbose=False,
    )


def _text(result) -> str:
    markdown = result.markdown
    if markdown is None:
        return ""
    return (markdown.fit_markdown or markdown.raw_markdown or "").strip()


def _links(result) -> tuple[str, ...]:
    links = (result.links or {}).get("internal", [])
    return tuple(link.get("href", "") for link in links if link.get("href"))
