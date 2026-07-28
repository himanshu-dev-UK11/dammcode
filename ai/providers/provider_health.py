"""
Provider Health.

Tracks operational status and reliability of providers,
including Health Score calculation (Part 16).
"""

import threading
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from core.logger import setup_logger

from ai.providers.base_provider import ProviderStatus


logger = setup_logger(__name__)


@dataclass
class ProviderHealthMetrics:
    """
    Health metrics for a single provider, including health score (Part 16).
    """
    provider_name: str
    status: ProviderStatus = ProviderStatus.UNKNOWN
    last_tested: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    last_ping: Optional[datetime] = None
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    consecutive_failures: int = 0
    total_timeouts: int = 0
    average_latency_ms: float = 0.0
    current_availability: float = 1.0  # 1.0 = 100% available
    available_models_count: int = 0
    is_streaming_available: bool = True
    recent_errors: List[str] = field(default_factory=list)
    cached_models: Optional[List[Dict[str, Any]]] = None
    cached_valid_api_key: bool = False
    last_config_change: Optional[datetime] = None
    last_sync: Optional[datetime] = None
    requests_today: int = 0
    failures_today: int = 0
    
    def record_request(self, success: bool, latency_ms: float = 0.0, is_timeout: bool = False) -> None:
        """Record a request result."""
        self.total_requests += 1
        self.requests_today += 1
        self.last_tested = datetime.utcnow()
        
        if success:
            self.successful_requests += 1
            self.last_success = self.last_tested
            self.consecutive_failures = 0
            self.current_availability = min(1.0, self.current_availability + 0.05)
            
            # Update moving average latency
            if self.average_latency_ms == 0.0:
                self.average_latency_ms = latency_ms
            else:
                self.average_latency_ms = (self.average_latency_ms * 0.9) + (latency_ms * 0.1)
        else:
            self.failed_requests += 1
            self.failures_today +=1
            self.last_failure = self.last_tested
            self.consecutive_failures += 1
            
            if is_timeout:
                self.total_timeouts += 1
            
            # Decrease availability on failures
            self.current_availability = max(0.0, self.current_availability - 0.1)
            
            # Mark as offline after 3 consecutive failures
            if self.consecutive_failures >= 3:
                self.current_availability = 0.0

    def get_availability_score(self) -> float:
        """Calculate availability score (0.0 to 1.0)."""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    
    def calculate_health_score(self) -> int:
        """
        Calculate overall health percentage (0-100) (Part 16).
        Considers:
        - Connection status
        - Authentication/API key validity
        - Latency (lower is better)
        - Successful requests ratio
        - Consecutive failures
        - Available models
        """
        score = 100
        
        # Factor 1: Status
        if self.status in [
            ProviderStatus.DISCONNECTED,
            ProviderStatus.OFFLINE,
            ProviderStatus.API_MISSING,
            ProviderStatus.AUTHENTICATION_FAILED,
            ProviderStatus.UNAVAILABLE
        ]:
            score -= 60
        elif self.status in [ProviderStatus.CHECKING, ProviderStatus.CONNECTING]:
            score -= 30
        
        # Factor 2: API key
        if not self.cached_valid_api_key:
            score -= 30
        
        # Factor3: Consecutive failures
        if self.consecutive_failures > 0:
            score -= min(self.consecutive_failures * 10, 40)
        
        # Factor4: Latency (penalize >500ms)
        if self.average_latency_ms > 500:
            score -= min((self.average_latency_ms / 100), 30)
        
        # Factor5: Availability score
        score *= self.get_availability_score()
        
        # Cap between 0-100, integer
        return max(0, min(100, int(score)))
    
    def get_health_info(self) -> Dict[str, Any]:
        """Get health info as dict for display (Part16, Part21)"""
        return {
            "status": self.status.value,
            "health_score": self.calculate_health_score(),
            "latency_ms": round(self.average_latency_ms, 1),
            "last_ping": self.last_ping.isoformat() if self.last_ping else None,
            "available_models": self.available_models_count,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "requests_today": self.requests_today,
            "failures_today": self.failures_today,
            "recent_errors": self.recent_errors[-5:],
        }


class ProviderHealth:
    """
    Monitors health of all providers.
    
    Tracks:
    - Connection status
    - Request success/failure rates
    - Latency metrics
    - Automatic reconnection triggers
    """
    
    def __init__(self, registry: Any):
        self.registry = registry
        self._metrics: Dict[str, ProviderHealthMetrics] = {}
        self._last_reconnect: Dict[str, datetime] = {}
        self._lock = threading.Lock()
        logger.info("ProviderHealth initialized")

    def get_metrics(self, provider_name: str) -> Optional[ProviderHealthMetrics]:
        """Get health metrics for a provider."""
        return self._metrics.get(provider_name)

    def get_all_health(self) -> Dict[str, Dict[str, Any]]:
        """
        Get health status for all providers.
        
        Returns:
            Dict mapping provider names to health info
        """
        result = {}
        for name, metrics in self._metrics.items():
            result[name] = {
                "status": metrics.status.value,
                "last_tested": metrics.last_tested.isoformat() if metrics.last_tested else None,
                "last_success": metrics.last_success.isoformat() if metrics.last_success else None,
                "last_failure": metrics.last_failure.isoformat() if metrics.last_failure else None,
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "consecutive_failures": metrics.consecutive_failures,
                "total_timeouts": metrics.total_timeouts,
                "average_latency_ms": round(metrics.average_latency_ms, 2),
                "current_availability": round(metrics.current_availability, 2),
                "availability_score": round(metrics.get_availability_score(), 2),
            }
        return result

    def record_status(self, provider_name: str, status: ProviderStatus) -> None:
        """Record provider status change."""
        with self._lock:
            if provider_name not in self._metrics:
                self._metrics[provider_name] = ProviderHealthMetrics(provider_name=provider_name)
            
            self._metrics[provider_name].status = status
    
    def record_request(
        self,
        provider_name: str,
        success: bool,
        latency_ms: float = 0.0,
        is_timeout: bool = False
    ) -> None:
        """Record a request result."""
        with self._lock:
            if provider_name not in self._metrics:
                self._metrics[provider_name] = ProviderHealthMetrics(provider_name=provider_name)
            
            self._metrics[provider_name].record_request(success, latency_ms, is_timeout)

    def record_attempt(self, provider_name: str) -> None:
        """Record a reconnection attempt."""
        with self._lock:
            self._last_reconnect[provider_name] = datetime.utcnow()

    def get_last_attempt(self, provider_name: str) -> Optional[datetime]:
        """Get last reconnection attempt time."""
        return self._last_reconnect.get(provider_name)

    def get_unavailable_providers(self) -> List[str]:
        """Get list of unavailable providers."""
        unavailable = []
        for name, metrics in self._metrics.items():
            if metrics.current_availability <= 0.0:
                unavailable.append(name)
        return unavailable

    def get_recommended_provider(self) -> Optional[str]:
        """
        Get the recommended provider based on health metrics.
        
        Returns:
            Provider name with best availability score, or None
        """
        best_provider = None
        best_score = -1.0
        
        for name, metrics in self._metrics.items():
            score = metrics.get_availability_score()
            if score > best_score:
                best_score = score
                best_provider = name
        
        return best_provider

    def clear(self, provider_name: Optional[str] = None) -> None:
        """Clear health metrics."""
        with self._lock:
            if provider_name:
                if provider_name in self._metrics:
                    del self._metrics[provider_name]
                if provider_name in self._last_reconnect:
                    del self._last_reconnect[provider_name]
            else:
                self._metrics.clear()
                self._last_reconnect.clear()
