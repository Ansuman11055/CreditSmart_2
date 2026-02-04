"""Cache statistics endpoint for monitoring.

Phase 3E: Production Readiness
- Provides cache hit rate and statistics
- Used for performance monitoring
- Safe for production (no sensitive data)
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
import structlog

from app.core.prediction_cache import get_prediction_cache

router = APIRouter()
logger = structlog.get_logger(__name__)


class CacheStatsResponse(BaseModel):
    """Cache statistics response schema.
    
    Provides insights into prediction caching performance.
    """
    
    hits: int = Field(
        description="Number of cache hits"
    )
    
    misses: int = Field(
        description="Number of cache misses"
    )
    
    evictions: int = Field(
        description="Number of LRU evictions"
    )
    
    expirations: int = Field(
        description="Number of TTL expirations"
    )
    
    high_risk_bypasses: int = Field(
        description="Number of high-risk predictions not cached"
    )
    
    current_size: int = Field(
        description="Current number of entries in cache"
    )
    
    max_size: int = Field(
        description="Maximum cache size"
    )
    
    hit_rate: float = Field(
        description="Cache hit rate (0.0-1.0)"
    )
    
    total_requests: int = Field(
        description="Total cache lookup requests"
    )


@router.get("/cache/stats", response_model=CacheStatsResponse, tags=["monitoring"])
def get_cache_stats() -> CacheStatsResponse:
    """Get prediction cache statistics.
    
    Phase 3E: Production Monitoring
    - No authentication required (stats only, no data)
    - Fast response (<10ms)
    - Used for Prometheus/Datadog monitoring
    
    Returns:
        CacheStatsResponse with cache performance metrics
        
    Example:
        ```
        GET /api/v1/cache/stats
        
        {
          "hits": 245,
          "misses": 55,
          "evictions": 12,
          "expirations": 8,
          "high_risk_bypasses": 15,
          "current_size": 188,
          "max_size": 1000,
          "hit_rate": 0.817,
          "total_requests": 300
        }
        ```
    """
    cache = get_prediction_cache()
    stats = cache.get_stats()
    
    logger.debug(
        "cache_stats_requested",
        hit_rate=stats["hit_rate"],
        current_size=stats["current_size"]
    )
    
    return CacheStatsResponse(**stats)


@router.post("/cache/clear", tags=["monitoring"])
def clear_cache() -> dict:
    """Clear all cache entries.
    
    Phase 3E: Production Operations
    - Use when model is updated
    - Use when cache becomes stale
    - Safe operation (no data loss, just clears memory)
    
    Returns:
        Confirmation message
        
    Example:
        ```
        POST /api/v1/cache/clear
        
        {
          "status": "success",
          "message": "Cache cleared successfully",
          "previous_size": 188
        }
        ```
    """
    cache = get_prediction_cache()
    stats = cache.get_stats()
    previous_size = stats["current_size"]
    
    cache.clear()
    
    logger.info(
        "cache_cleared",
        previous_size=previous_size
    )
    
    return {
        "status": "success",
        "message": "Cache cleared successfully",
        "previous_size": previous_size
    }
