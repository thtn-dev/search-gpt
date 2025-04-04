from fastapi import APIRouter, HTTPException
from services.search_service import SearchService
search_router = APIRouter(prefix="/search", tags=["search"])

search_service = SearchService()

@search_router.get("/get-search-url", tags=["search"])
async def get_search_url(query: str) -> list[str]:
    """
    Get search URL from query string
    """
    try:
        results = search_service.get_search_url(query)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))