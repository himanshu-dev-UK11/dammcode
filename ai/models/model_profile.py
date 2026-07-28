"""
Model Profile dataclass.

Describes the specifications and abilities of an AI model,
including full capabilities (Part 15), quality profile (Part 23).
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class ModelQualityProfile:
    """Model quality scores for Part 23: displays stars for Coding/Reasoning/Speed/Creativity"""
    coding: int = 5  # 1-5 stars
    reasoning: int = 5  # 1-5 stars
    speed: int = 5  # 1-5 stars
    creativity: int = 5  # 1-5 stars
    
    def to_stars(self, score: int) -> str:
        """Convert a 1-5 score to star string for display"""
        full = "★" * score
        empty = "☆" * (5 - score)
        return full + empty

@dataclass
class ModelProfile:
    """
    Metadata and capabilities of a specific AI model.
    """
    name: str
    provider: str
    version: str
    is_local: bool
    context_window: int
    max_output_tokens: int
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    supported_languages: List[str] = field(default_factory=list)
    coding_ability: int = 1  # 1 to 10 (for scoring)
    reasoning_ability: int = 1  # 1 to 10 (for scoring)
    cost_per_1k_tokens: float = 0.0
    average_response_time_ms: float = 0.0
    availability_score: float = 1.0  # 0.0 to 1.0
    
    # --- Capabilities (Part 15) ---
    supports_streaming: bool = True
    supports_vision: bool = False
    supports_tool_calling: bool = False
    supports_function_calling: bool = False
    supports_json_mode: bool = False
    supports_structured_output: bool = False
    supports_embeddings: bool = False
    supports_image_generation: bool = False
    supports_audio: bool = False
    supports_speech_to_text: bool = False
    supports_text_to_speech: bool = False
    supports_video: bool = False
    supports_thinking_mode: bool = False
    supports_multi_modal: bool = False
    capabilities: List[str] = field(default_factory=list)  # for icon display
    
    # --- Quality Profile (Part 23) ---
    quality: ModelQualityProfile = field(default_factory=ModelQualityProfile)
    
    # --- Cache Info (Part 19) ---
    last_verified: Optional[datetime] = None
