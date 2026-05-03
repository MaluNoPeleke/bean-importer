import logging
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import httpx
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

BLOCKED_DOMAINS = {"facebook.com", "instagram.com", "twitter.com", "youtube.com", "tiktok.com"}


def search_web(query: str, max_results: int = 5) -> list[dict]:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, region="de-de", max_results=max_results))
        results = [r for r in results if not _is_blocked(r.get("href", ""))]
        logger.info("Search '%s' → %d results", query, len(results))
        return results
    except Exception as e:
        logger.warning("Search failed for '%s': %s", query, e)
        return []


def _is_blocked(url: str) -> bool:
    try:
        host = urlparse(url).hostname or ""
        return any(d in host for d in BLOCKED_DOMAINS)
    except Exception:
        return False


async def fetch_page_text(url: str, max_chars: int = 8000) -> str:
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            resp = await client.get(url, headers={"User-Agent": USER_AGENT})
            if resp.status_code != 200:
                return ""
        soup = BeautifulSoup(resp.text, "lxml")
        for tag in soup.find_all(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return text[:max_chars]
    except Exception as e:
        logger.warning("Failed to fetch %s: %s", url, e)
        return ""


async def research_coffee(product_name: str, shop_domain: str | None = None) -> str:
    queries = [
        f'"{product_name}" Kaffee Röster Herkunft Varietät',
        f'"{product_name}" coffee espresso recipe brew ratio',
        f'"{product_name}" Kaffee Geschmack Aufbereitung Region',
    ]

    all_snippets = []
    seen_urls = set()

    for query in queries:
        results = search_web(query, max_results=5)
        for r in results:
            url = r.get("href", "")
            snippet = f"Quelle: {url}\nTitel: {r.get('title', '')}\n{r.get('body', '')}"
            all_snippets.append(snippet)

            if url and url not in seen_urls and len(seen_urls) < 4:
                if shop_domain and shop_domain in url:
                    continue
                seen_urls.add(url)

    for url in seen_urls:
        text = await fetch_page_text(url)
        if text:
            all_snippets.append(f"=== Volltext: {url} ===\n{text}")

    combined = "\n\n---\n\n".join(all_snippets)
    logger.info("Research for '%s' → %d chars context from %d sources", product_name, len(combined), len(seen_urls))
    return combined
