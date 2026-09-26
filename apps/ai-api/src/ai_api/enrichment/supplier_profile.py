"""What a supplier sells, from its own website when that is known or can be found, from search snippets otherwise."""
from __future__ import annotations

import json
import logging
from typing import Callable, NamedTuple
from urllib.parse import urlsplit

import json_repair

from web_api.website import host_is_supplier_name

from .. import config
from ..web_context import ddg_search, ddg_site_search, read_cache, summarize_supplier, write_cache
from .site.discovery import find_website

logger = logging.getLogger("ai_api.enrichment")


class SupplierProfile(NamedTuple):
    description: str
    website: str | None


class SiteVerdict(NamedTuple):
    is_supplier_site: bool
    description: str


NO_VERDICT = SiteVerdict(False, "")


def describe_supplier(
    name: str,
    country_code: str | None = None,
    website: str | None = None,
    *,
    search_fn: Callable[[str], list[dict]] = ddg_search,
    site_search_fn: Callable[[str], list[dict]] = ddg_site_search,
    crawl_fn: Callable[[str], str] | None = None,
    summarize_site_fn: Callable[[str, str | None, str], SiteVerdict] | None = None,
    summarize_snippets_fn: Callable[[str, str], str] = summarize_supplier,
    cache_dir: str | None = None,
) -> SupplierProfile:
    """The supplier's description and website.

    A stated `website` (the supplier's own, or the one its invoices print) is crawled as it is and
    kept whatever it yields; without one, the site is looked for among the search results for the
    name and kept only when the description came from it.
    """
    if not (name or "").strip():
        return SupplierProfile("", website)
    if summarize_site_fn is None:
        summarize_site_fn = summarize_site

    if crawl_fn is not None:
        site = website
        if site is None:
            site = find_website(
                name, search_supplier_site(name, search_fn=site_search_fn, cache_dir=cache_dir)
            )
        if site is not None:
            verdict = _judge_site(name, country_code, site, crawl_fn, summarize_site_fn)
            if verdict.is_supplier_site and verdict.description:
                return SupplierProfile(verdict.description, site)

    results = search_supplier(name, country_code, search_fn=search_fn, cache_dir=cache_dir)
    snippets = " | ".join(result.get("body", "") for result in results if result.get("body"))
    return SupplierProfile(summarize_snippets_fn(name, snippets), website)


def locate_website(
    name: str,
    country_code: str | None = None,
    website: str | None = None,
    *,
    search_fn: Callable[[str], list[dict]] = ddg_search,
    site_search_fn: Callable[[str], list[dict]] = ddg_site_search,
    crawl_fn: Callable[[str], str] | None = None,
    summarize_site_fn: Callable[[str, str | None, str], SiteVerdict] | None = None,
    cache_dir: str | None = None,
) -> str | None:
    """The supplier's website: a known one as it is, else one found for its name.

    A found site whose domain is exactly the supplier's name is taken as it is; any other must be
    confirmed by reading it, so without a crawler only those are returned.
    """
    if website is not None:
        return website
    if not (name or "").strip():
        return None
    if summarize_site_fn is None:
        summarize_site_fn = summarize_site
    site = find_website(name, search_supplier_site(name, search_fn=site_search_fn, cache_dir=cache_dir))
    if site is None:
        return None
    if host_is_supplier_name(urlsplit(site).hostname or "", name):
        return site
    if crawl_fn is None:
        return None
    if _judge_site(name, country_code, site, crawl_fn, summarize_site_fn).is_supplier_site:
        return site
    return None


def search_supplier(
    name: str,
    country_code: str | None,
    *,
    search_fn: Callable[[str], list[dict]],
    cache_dir: str | None = None,
) -> list[dict]:
    """The web search results for the supplier, with their links, cached by query."""
    cache_dir = config.WEB_CONTEXT_CACHE_DIR if cache_dir is None else cache_dir
    query = " ".join(part for part in (name, country_code, "company what they sell") if part)
    key = f"supplier-results-{query}"
    cached = read_cache(cache_dir, key)
    if cached is not None:
        return json.loads(cached)
    results = search_fn(query)
    write_cache(cache_dir, key, json.dumps(results))
    return results


def search_supplier_site(
    name: str,
    *,
    search_fn: Callable[[str], list[dict]],
    cache_dir: str | None = None,
) -> list[dict]:
    """The web search results for the supplier's own website, cached by query."""
    cache_dir = config.WEB_CONTEXT_CACHE_DIR if cache_dir is None else cache_dir
    query = f"{name} official website"
    key = f"supplier-site-results-{query}"
    cached = read_cache(cache_dir, key)
    if cached is not None:
        return json.loads(cached)
    results = search_fn(query)
    write_cache(cache_dir, key, json.dumps(results))
    return results


def summarize_site(name: str, country_code: str | None, text: str) -> SiteVerdict:
    """Ask the LLM whether the text is the supplier's own site and, if so, what the supplier sells."""
    where = f" (based in {country_code})" if country_code else ""
    prompt = (
        f"Below is text from a website. Decide whether it is the own website of the "
        f"company '{name}'{where}. The main site of the brand or group the company "
        "belongs to counts, even when the company is one of its legal entities. A "
        "site for just one of its products or services does not count. If it is the "
        "company's own website, state in one or two sentences, in English, what the "
        "company sells or does: its industry and its main products or services. "
        "Write nothing about any customer of theirs.\n\n"
        "Reply with only a JSON object and nothing else:\n"
        '{"is_supplier_site": true or false, "description": "..."}\n'
        'When it is not the company\'s own website, use an empty description.\n\n'
        f"{text[:config.SUPPLIER_CRAWL_MAX_CHARS]}"
    )
    try:
        reply = config.get_llm().call(messages=[{"role": "user", "content": prompt}])
    except Exception as exc:  # noqa: BLE001
        logger.warning("could not summarize the site of %s: %s", name, exc)
        return NO_VERDICT
    return read_site_answer(reply or "")


def read_site_answer(reply: str) -> SiteVerdict:
    """The LLM's verdict on a site; not the supplier's when the answer is unreadable."""
    answer = json_repair.loads(reply)
    if not isinstance(answer, dict) or answer.get("is_supplier_site") is not True:
        return NO_VERDICT
    description = answer.get("description")
    if not isinstance(description, str):
        return SiteVerdict(True, "")
    return SiteVerdict(True, description.strip())


def _judge_site(
    name: str,
    country_code: str | None,
    website: str,
    crawl_fn: Callable[[str], str],
    summarize_site_fn: Callable[[str, str | None, str], SiteVerdict],
) -> SiteVerdict:
    try:
        text = crawl_fn(website)
    except Exception as exc:  # noqa: BLE001
        logger.warning("could not crawl %s for %s: %s", website, name, exc)
        return NO_VERDICT
    if not text.strip():
        return NO_VERDICT
    return summarize_site_fn(name, country_code, text)
