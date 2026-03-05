"""Web content extraction service using trafilatura."""

import asyncio
from typing import Optional

import httpx
import trafilatura
from bs4 import BeautifulSoup

from app.core import get_logger
from app.core.exceptions import WebExtractionError

logger = get_logger(__name__)


class WebExtractor:
    """Extract main content from web pages."""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; TechNewsAggregator/0.1.0)"
        }

    async def extract_content(self, url: str) -> str:
        """Extract main content from a web page.

        Args:
            url: URL of the web page

        Returns:
            Extracted text content

        Raises:
            WebExtractionError: If extraction fails
        """
        try:
            # Fetch the page
            html_content = await self._fetch_page(url)

            # Extract text using trafilatura
            content = self._extract_with_trafilatura(html_content, url)

            if not content:
                # Fallback to BeautifulSoup extraction
                content = self._extract_with_beautifulsoup(html_content)

            if not content:
                raise WebExtractionError(
                    "Could not extract content from page",
                    {"url": url},
                )

            logger.info(
                "Extracted web content",
                url=url,
                content_length=len(content),
            )

            return content

        except WebExtractionError:
            raise
        except Exception as e:
            raise WebExtractionError(
                f"Failed to extract content: {str(e)}",
                {"url": url, "error": str(e)},
            )

    async def _fetch_page(self, url: str) -> str:
        """Fetch page HTML content.

        Args:
            url: URL to fetch

        Returns:
            HTML content as string
        """
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.text

    def _extract_with_trafilatura(
        self, html_content: str, url: str
    ) -> Optional[str]:
        """Extract content using trafilatura.

        Args:
            html_content: Raw HTML
            url: Source URL for context

        Returns:
            Extracted text or None
        """
        try:
            content = trafilatura.extract(
                html_content,
                url=url,
                include_comments=False,
                include_tables=True,
                include_images=False,
                include_links=False,
                favor_precision=True,
            )
            return content
        except Exception as e:
            logger.debug(
                "Trafilatura extraction failed",
                url=url,
                error=str(e),
            )
            return None

    def _extract_with_beautifulsoup(self, html_content: str) -> str:
        """Fallback extraction using BeautifulSoup.

        Args:
            html_content: Raw HTML

        Returns:
            Extracted text
        """
        soup = BeautifulSoup(html_content, "html.parser")

        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "header", "footer"]):
            element.decompose()

        # Try to find main content
        main_content = (
            soup.find("article")
            or soup.find("main")
            or soup.find("div", class_="content")
            or soup.find("div", class_="article")
            or soup.body
        )

        if not main_content:
            return ""

        # Extract text
        text = main_content.get_text(separator="\n", strip=True)

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return "\n".join(chunk for chunk in chunks if chunk)

    async def extract_batch(self, urls: list[str]) -> dict[str, str]:
        """Extract content from multiple URLs concurrently.

        Args:
            urls: List of URLs to extract

        Returns:
            Dict mapping URLs to extracted content
        """
        results = {}

        async def extract_one(url: str) -> tuple[str, str]:
            try:
                content = await self.extract_content(url)
                return url, content
            except WebExtractionError as e:
                logger.warning(
                    "Failed to extract URL",
                    url=url,
                    error=e.message,
                )
                return url, ""

        # Run extractions concurrently
        tasks = [extract_one(url) for url in urls]
        for url, content in await asyncio.gather(*tasks):
            results[url] = content

        return results


# Singleton instance
web_extractor = WebExtractor()