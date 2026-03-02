"""
Health check routes
"""

from fastapi import APIRouter
from datetime import datetime
from src.api.schemas.news import HealthResponse
from src.vector_store import get_vector_store
from src.llm import get_llm_client

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    qdrant_connected = False
    llm_configured = False

    # Check Qdrant connection
    try:
        store = get_vector_store()
        qdrant_connected = store.test_connection()
    except Exception:
        pass

    # Check LLM configuration
    try:
        llm = get_llm_client()
        llm_configured = llm.api_key is not None
    except Exception:
        pass

    return HealthResponse(
        status="healthy" if qdrant_connected else "degraded",
        qdrant_connected=qdrant_connected,
        llm_configured=llm_configured,
        timestamp=datetime.now().isoformat()
    )
