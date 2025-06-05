import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import aiohttp
from fastapi import HTTPException

logger = logging.getLogger(__name__)


@dataclass
class SearxngSearchOptions:
    """Search options for SearXNG API"""

    categories: Optional[List[str]] = None
    engines: Optional[List[str]] = None
    language: Optional[str] = None
    pageno: Optional[int] = None
    time_range: Optional[str] = None  # day, week, month, year
    safesearch: Optional[int] = None  # 0=off, 1=moderate, 2=strict


@dataclass
class SearxngSearchResult:
    """Single search result from SearXNG"""

    title: str
    url: str
    img_src: Optional[str] = None
    thumbnail_src: Optional[str] = None
    thumbnail: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    iframe_src: Optional[str] = None
    engine: Optional[str] = None
    score: Optional[float] = None
    category: Optional[str] = None


@dataclass
class SearxngResponse:
    """Complete response from SearXNG API"""

    results: List[SearxngSearchResult]
    suggestions: List[str]
    query: str
    number_of_results: int


class SearxngClient:
    """Async SearXNG client optimized for FastAPI"""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._session:
            await self._session.close()

    @property
    def session(self) -> aiohttp.ClientSession:
        """Get or create session"""
        if self._session is None:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session

    async def close(self):
        """Close the HTTP session"""
        if self._session:
            await self._session.close()
            self._session = None

    def _build_search_params(
        self, query: str, options: Optional[SearxngSearchOptions] = None
    ) -> Dict[str, str]:
        """Build search parameters for API request"""
        params = {'q': query, 'format': 'json'}

        if options:
            if options.categories:
                params['categories'] = ','.join(options.categories)
            if options.engines:
                params['engines'] = ','.join(options.engines)
            if options.language:
                params['language'] = options.language
            if options.pageno is not None:
                params['pageno'] = str(options.pageno)
            if options.time_range:
                params['time_range'] = options.time_range
            if options.safesearch is not None:
                params['safesearch'] = str(options.safesearch)

        return params

    def _parse_result(self, result_data: Dict[str, Any]) -> SearxngSearchResult:
        """Parse a single search result"""
        return SearxngSearchResult(
            title=result_data.get('title', ''),
            url=result_data.get('url', ''),
            img_src=result_data.get('img_src'),
            thumbnail_src=result_data.get('thumbnail_src'),
            thumbnail=result_data.get('thumbnail'),
            content=result_data.get('content'),
            author=result_data.get('author'),
            iframe_src=result_data.get('iframe_src'),
            engine=result_data.get('engine'),
            score=result_data.get('score'),
            category=result_data.get('category'),
        )

    async def search(
        self, query: str, options: Optional[SearxngSearchOptions] = None
    ) -> SearxngResponse:
        """
        Perform search using SearXNG API

        Args:
            query: Search query string
            options: Search options (categories, engines, etc.)

        Returns:
            SearxngResponse containing results and suggestions

        Raises:
            HTTPException: If API request fails
        """
        if not query.strip():
            raise HTTPException(status_code=400, detail='Query cannot be empty')

        params = self._build_search_params(query, options)
        search_url = f'{self.base_url}/search'

        try:
            async with self.session.get(search_url, params=params) as response:
                if response.status != 200:
                    logger.error(f'SearXNG API error: {response.status}')
                    raise HTTPException(
                        status_code=502,
                        detail=f'Search service unavailable (HTTP {response.status})',
                    )

                data = await response.json()

                # Parse results
                results = [
                    self._parse_result(result) for result in data.get('results', [])
                ]

                return SearxngResponse(
                    results=results,
                    suggestions=data.get('suggestions', []),
                    query=query,
                    number_of_results=len(results),
                )

        except aiohttp.ClientError as e:
            logger.error(f'Network error during search: {str(e)}')
            raise HTTPException(
                status_code=502, detail='Failed to connect to search service'
            )
        except Exception as e:
            logger.error(f'Unexpected error during search: {str(e)}')
            raise HTTPException(
                status_code=500, detail='Internal server error during search'
            )


# Singleton instance for reuse across FastAPI app
_searxng_client: Optional[SearxngClient] = None


def get_searxng_client(base_url: str) -> SearxngClient:
    """Get singleton SearXNG client instance"""
    global _searxng_client
    if _searxng_client is None:
        _searxng_client = SearxngClient(base_url)
    return _searxng_client


async def cleanup_searxng_client():
    """Cleanup function to close client session"""
    global _searxng_client
    if _searxng_client:
        await _searxng_client.close()
        _searxng_client = None


# Convenience function for quick searches
async def search_searxng(
    query: str, base_url: str, options: Optional[SearxngSearchOptions] = None
) -> SearxngResponse:
    """
    Convenience function for performing SearXNG search

    Args:
        query: Search query
        base_url: SearXNG instance URL
        options: Search options

    Returns:
        Search response with results
    """
    client = get_searxng_client(base_url)
    return await client.search(query, options)
