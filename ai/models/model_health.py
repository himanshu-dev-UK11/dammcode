"""
Model Health monitoring.

Tracks the operational status and reliability of models.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class ModelHealth:
    """
    Health metrics for a single model.
    """
    model_name: str
    is_online: bool = True
    average_latency_ms: float = 0.0
    last_successful_request: Optional[datetime] = None
    consecutive_failures: int = 0
    current_availability: float = 1.0  # 1.0 = healthy, 0.0 = offline

    def record_success(self, latency_ms: float):
        """Record a successful execution."""
        self.is_online = True
        self.consecutive_failures = 0
        self.last_successful_request = datetime.utcnow()
        if self.average_latency_ms == 0.0:
            self.average_latency_ms = latency_ms
        else:
            self.average_latency_ms = (self.average_latency_ms * 0.9) + (latency_ms * 0.1)
        self.current_availability = 1.0

    def record_failure(self):
        """Record a failed execution."""
        self.consecutive_failures += 1
        if self.consecutive_failures >= 3:
            self.is_online = False
            self.current_availability = 0.0
        else:
            self.current_availability = max(0.0, 1.0 - (self.consecutive_failures * 0.3))
