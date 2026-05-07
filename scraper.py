import logging
from typing import Optional
from bs4 import BeautifulSoup
import httpx
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

STRIP_TAGS = {"script", "style", "nav", "footer", "header", "noscript", "svg", "iframe"}
CONTENT_TAGS = ["main", "article"]
MIN_HTML_LENGTH = 500


async def fetch_html(url: str) -> Optional[str]:
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            resp = await client.get(url, headers={"User-Agent": USER_AGENT})
            if resp.status_code != 200:
                logger.warning("httpx returned status %d for %s", resp.status_code, url)
                return None
            html = resp.text
            if len(html) < MIN_HTML_LENGTH:
                logger.warning("httpx response too short (%d chars) for %s", len(html), url)
                return None
            soup = BeautifulSoup(html, "lxml")
            if not soup.body or not soup.body.get_text(strip=True):
                logger.warning("httpx response has no body content for %s", url)
                return None
            return html
    except httpx.HTTPError as e:
        logger.warning("httpx error for %s: %s", url, e)
        return None


async def fetch_with_playwright(url: str) -> str:
    logger.info("Playwright fallback for %s", url)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent=USER_AGENT)
        await page.goto(url, wait_until="networkidle", timeout=30000)
        html = await page.content()
        await browser.close()
    return html


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup.find_all(STRIP_TAGS):
        tag.decompose()

    for container_tag in CONTENT_TAGS:
        content = soup.find(container_tag)
        if content and len(content.get_text(strip=True)) > 100:
            return str(content)

    return str(soup.body) if soup.body else str(soup)


async def scrape(url: str) -> str:
    html = await fetch_html(url)
    if html is None:
        html = await fetch_with_playwright(url)
    cleaned = clean_html(html)
    logger.info("Scraped %s → %d chars cleaned HTML", url, len(cleaned))
    return cleaned
