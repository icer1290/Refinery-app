"""Web search service using DuckDuckGo (free, no API key required)."""

import json
from typing import Optional
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from app.config import get_settings
from app.core import get_logger
from app.core.exceptions import ExternalServiceError

logger = get_logger(__name__)
settings = get_settings()


class WebSearchResult:
    """Represents a web search result."""

    def __init__(
        self,
        title: str,
        url: str,
        snippet: str,
    ):
        self.title = title
        self.url = url
        self.snippet = snippet

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
        }


class WebSearchService:
    """Service for performing web searches using DuckDuckGo."""

    def __init__(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.provider = provider or getattr(settings, "web_search_provider", "duckduckgo")
        self.api_key = api_key or getattr(settings, "web_search_api_key", None)
        self.timeout = 30.0

        logger.info(
            "Web search service initialized",
            provider=self.provider,
        )

    async def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[WebSearchResult]:
        """Perform a web search.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of search results

        Raises:
            ExternalServiceError: If search fails
        """
        if self.provider == "tavily" and self.api_key:
            return await self._search_tavily(query, max_results)
        else:
            return await self._search_duckduckgo(query, max_results)

    async def _search_duckduckgo(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[WebSearchResult]:
        """Search using DuckDuckGo HTML version.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of search results
        """
        encoded_query = quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers, follow_redirects=True)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            results = []

            # Find all result divs
            result_divs = soup.find_all("div", class_="result")

            for div in result_divs[:max_results]:
                try:
                    # Get title and link
                    title_elem = div.find("a", class_="result__a")
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    href = title_elem.get("href", "")

                    # DuckDuckGo uses redirect URLs, extract actual URL
                    if "uddg=" in href:
                        href = href.split("uddg=")[-1].split("&")[0]
                        from urllib.parse import unquote
                        href = unquote(href)

                    # Get snippet
                    snippet_elem = div.find("a", class_="result__snippet")
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                    if title and href:
                        results.append(WebSearchResult(
                            title=title,
                            url=href,
                            snippet=snippet,
                        ))

                except Exception as e:
                    logger.debug(f"Failed to parse result: {e}")
                    continue

            logger.info(
                "DuckDuckGo search completed",
                query=query[:50],
                results_count=len(results),
            )

            return results

        except httpx.TimeoutException:
            logger.error("DuckDuckGo search timeout", query=query[:50])
            raise ExternalServiceError(
                "Web search timeout",
                {"query": query, "error": "timeout"},
            )
        except Exception as e:
            logger.error("DuckDuckGo search failed", error=str(e), query=query[:50])
            raise ExternalServiceError(
                f"Web search failed: {str(e)}",
                {"query": query, "error": str(e)},
            )

    async def _search_tavily(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[WebSearchResult]:
        """Search using Tavily API.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of search results
        """
        url = "https://api.tavily.com/search"

        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
        }

        headers = {
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()

            data = response.json()
            results = []

            for item in data.get("results", [])[:max_results]:
                results.append(WebSearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                ))

            logger.info(
                "Tavily search completed",
                query=query[:50],
                results_count=len(results),
            )

            return results

        except Exception as e:
            logger.error("Tavily search failed", error=str(e), query=query[:50])
            raise ExternalServiceError(
                f"Tavily search failed: {str(e)}",
                {"query": query, "error": str(e)},
            )

    async def fetch_page_content(self, url: str) -> str:
        """Fetch and extract text content from a URL.

        Args:
            url: URL to fetch

        Returns:
            Extracted text content
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers, follow_redirects=True)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Get text
            text = soup.get_text(separator="\n", strip=True)

            # Limit length
            if len(text) > 2000:
                text = text[:2000] + "..."

            return text

        except Exception as e:
            logger.warning("Failed to fetch page content", url=url, error=str(e))
            return ""


# Singleton instance
_web_search_service: Optional[WebSearchService] = None


def get_web_search_service() -> WebSearchService:
    """Get or create web search service instance."""
    global _web_search_service
    if _web_search_service is None:
        _web_search_service = WebSearchService()
    return _web_search_service