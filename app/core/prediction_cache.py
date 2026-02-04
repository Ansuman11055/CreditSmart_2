"""Production-grade prediction caching with LRU eviction and TTL expiration.

This module provides in-memory caching for ML predictions to reduce:
- Inference latency for repeated queries
- Computational load on ML models
- API response times

FEATURES:
- LRU eviction (least recently used items removed first)
- TTL-based expiration (cache entries expire after configured time)
- Input hash-based keys (content-addressable storage)
- Model version tracking (cache invalidation on model updates)
- High-risk bypass (never cache high-risk predictions)
- Thread-safe operations

SAFETY:
- No PII stored in cache (only sanitized input hashes)
- Automatic cleanup of expired entries
- Configurable max cache size
- Cache statistics for monitoring
"""

import time
import hashlib
import json
from typing import Optional, Dict, Any
from collections import OrderedDict
from threading import Lock
import structlog

from app.schemas.response import CreditRiskResponse

logger = structlog.get_logger(__name__)


class PredictionCache:
    """Thread-safe LRU cache with TTL for ML predictions.
    
    This cache uses a combination of LRU (Least Recently Used) eviction
    and TTL (Time To Live) expiration to manage memory efficiently.
    
    Cache Key Format:
        SHA256(sanitized_input + model_version)
        
    Cache Entry Format:
        {
            "response": CreditRiskResponse,
            "timestamp": float,
            "model_version": str,
            "input_hash": str,
            "explanation": Dict (Phase 4D Explainability - optional)
        }
    
    Thread Safety:
        All operations are protected by a threading lock to ensure
        safe concurrent access from multiple request handlers.
    """
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """Initialize prediction cache.
        
        Args:
            max_size: Maximum number of entries in cache (LRU eviction)
            ttl_seconds: Time-to-live for cache entries in seconds (default: 1 hour)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._lock = Lock()
        
        # Statistics for monitoring
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0,
            "high_risk_bypasses": 0,
        }
        
        logger.info(
            "prediction_cache_initialized",
            max_size=max_size,
            ttl_seconds=ttl_seconds
        )
    
    def _compute_cache_key(self, input_dict: Dict[str, Any], model_version: str) -> str:
        """Compute cache key from sanitized input and model version.
        
        Args:
            input_dict: Sanitized input dictionary (no PII)
            model_version: Model version string
            
        Returns:
            SHA256 hash as hex string
        """
        # Sort keys for consistent hashing
        sorted_input = json.dumps(input_dict, sort_keys=True)
        cache_input = f"{sorted_input}|{model_version}"
        
        # SHA256 hash for collision resistance
        return hashlib.sha256(cache_input.encode()).hexdigest()
    
    def _sanitize_input(self, request_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Remove PII and normalize input for cache key generation.
        
        Args:
            request_dict: Raw request dictionary
            
        Returns:
            Sanitized dictionary with only feature values
        """
        # Extract only ML features (no PII, no metadata)
        sanitized = {
            "annual_income": request_dict.get("annual_income"),
            "monthly_debt": request_dict.get("monthly_debt"),
            "credit_score": request_dict.get("credit_score"),
            "loan_amount": request_dict.get("loan_amount"),
            "loan_term_months": request_dict.get("loan_term_months"),
            "employment_length_years": request_dict.get("employment_length_years"),
            "home_ownership": request_dict.get("home_ownership"),
            "purpose": request_dict.get("purpose"),
            "number_of_open_accounts": request_dict.get("number_of_open_accounts"),
            "delinquencies_2y": request_dict.get("delinquencies_2y"),
            "inquiries_6m": request_dict.get("inquiries_6m"),
        }
        
        # Round float values to reduce cache key variation
        for key, value in sanitized.items():
            if isinstance(value, float):
                sanitized[key] = round(value, 2)
        
        return sanitized
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry has exceeded TTL.
        
        Args:
            entry: Cache entry with timestamp
            
        Returns:
            True if expired, False otherwise
        """
        age_seconds = time.time() - entry["timestamp"]
        return age_seconds > self.ttl_seconds
    
    def _is_high_risk(self, response: CreditRiskResponse) -> bool:
        """Check if prediction is high-risk (should not be cached).
        
        High-risk predictions are never cached to ensure fresh
        re-evaluation on subsequent requests.
        
        Args:
            response: Prediction response
            
        Returns:
            True if high-risk, False otherwise
        """
        return response.risk_score >= 0.7
    
    def get(
        self,
        request_dict: Dict[str, Any],
        model_version: str
    ) -> Optional[CreditRiskResponse]:
        """Retrieve prediction from cache if available and valid.
        
        Args:
            request_dict: Request dictionary (will be sanitized)
            model_version: Current model version
            
        Returns:
            Cached CreditRiskResponse or None if not found/expired
        """
        sanitized = self._sanitize_input(request_dict)
        cache_key = self._compute_cache_key(sanitized, model_version)
        
        with self._lock:
            # Check if key exists in cache
            if cache_key not in self._cache:
                self._stats["misses"] += 1
                return None
            
            entry = self._cache[cache_key]
            
            # Check if entry is expired
            if self._is_expired(entry):
                self._stats["expirations"] += 1
                self._stats["misses"] += 1
                del self._cache[cache_key]
                
                logger.debug(
                    "cache_entry_expired",
                    cache_key=cache_key[:16],
                    age_seconds=round(time.time() - entry["timestamp"], 2)
                )
                return None
            
            # Check model version match
            if entry["model_version"] != model_version:
                self._stats["misses"] += 1
                del self._cache[cache_key]
                
                logger.debug(
                    "cache_model_version_mismatch",
                    cache_key=cache_key[:16],
                    cached_version=entry["model_version"],
                    current_version=model_version
                )
                return None
            
            # Cache hit - move to end (LRU)
            self._cache.move_to_end(cache_key)
            self._stats["hits"] += 1
            
            logger.debug(
                "cache_hit",
                cache_key=cache_key[:16],
                age_seconds=round(time.time() - entry["timestamp"], 2)
            )
            
            return entry["response"]
    
    def put(
        self,
        request_dict: Dict[str, Any],
        model_version: str,
        response: CreditRiskResponse
    ) -> None:
        """Store prediction in cache.
        
        Args:
            request_dict: Request dictionary (will be sanitized)
            model_version: Model version string
            response: Prediction response to cache
        """
        # Never cache high-risk predictions
        if self._is_high_risk(response):
            self._stats["high_risk_bypasses"] += 1
            logger.debug(
                "cache_bypass_high_risk",
                risk_score=response.risk_score
            )
            return
        
        sanitized = self._sanitize_input(request_dict)
        cache_key = self._compute_cache_key(sanitized, model_version)
        
        with self._lock:
            # Check if cache is full - evict LRU item
            if len(self._cache) >= self.max_size and cache_key not in self._cache:
                evicted_key, _ = self._cache.popitem(last=False)  # Remove oldest
                self._stats["evictions"] += 1
                
                logger.debug(
                    "cache_eviction",
                    evicted_key=evicted_key[:16],
                    cache_size=len(self._cache)
                )
            
            # Store entry
            entry = {
                "response": response,
                "timestamp": time.time(),
                "model_version": model_version,
                "input_hash": cache_key[:16],  # First 16 chars for logging
            }
            
            self._cache[cache_key] = entry
            
            logger.debug(
                "cache_put",
                cache_key=cache_key[:16],
                cache_size=len(self._cache)
            )
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            
            logger.info(
                "cache_cleared",
                entries_removed=count
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            hit_rate = 0.0
            total_requests = self._stats["hits"] + self._stats["misses"]
            if total_requests > 0:
                hit_rate = self._stats["hits"] / total_requests
            
            return {
                **self._stats,
                "current_size": len(self._cache),
                "max_size": self.max_size,
                "hit_rate": round(hit_rate, 3),
                "total_requests": total_requests,
            }
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if self._is_expired(entry)
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.info(
                    "cache_cleanup_expired",
                    removed_count=len(expired_keys),
                    remaining_size=len(self._cache)
                )
            
            return len(expired_keys)
    
    # Phase 4D Explainability - Store explanation with prediction
    def put_explanation(
        self,
        request_id: str,
        explanation_data: Dict[str, Any]
    ) -> None:
        """Store explanation data by request ID.
        
        Phase 4D Explainability - Cache explanations separately by request_id
        
        Args:
            request_id: Unique request identifier
            explanation_data: Explanation dictionary to cache
        """
        explanation_key = f"explanation:{request_id}"
        
        with self._lock:
            # Store with same TTL as predictions
            entry = {
                "data": explanation_data,
                "timestamp": time.time(),
            }
            
            self._cache[explanation_key] = entry
            
            logger.debug(
                "explanation_cached",
                request_id=request_id,
                cache_size=len(self._cache)
            )
    
    # Phase 4D Explainability - Retrieve explanation by request ID
    def get_explanation(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve explanation data by request ID.
        
        Phase 4D Explainability - Fetch cached explanation
        
        Args:
            request_id: Unique request identifier
            
        Returns:
            Explanation dictionary or None if not found/expired
        """
        explanation_key = f"explanation:{request_id}"
        
        with self._lock:
            if explanation_key not in self._cache:
                return None
            
            entry = self._cache[explanation_key]
            
            # Check if expired
            if self._is_expired(entry):
                del self._cache[explanation_key]
                logger.debug(
                    "explanation_expired",
                    request_id=request_id
                )
                return None
            
            # Move to end (LRU)
            self._cache.move_to_end(explanation_key)
            
            return entry["data"]


# Global cache instance (singleton)
_prediction_cache: Optional[PredictionCache] = None


def get_prediction_cache() -> PredictionCache:
    """Get global prediction cache instance.
    
    Returns:
        Singleton PredictionCache instance
    """
    global _prediction_cache
    
    if _prediction_cache is None:
        # Initialize with production-safe defaults
        _prediction_cache = PredictionCache(
            max_size=1000,      # 1000 predictions in memory
            ttl_seconds=3600    # 1 hour expiration
        )
    
    return _prediction_cache
