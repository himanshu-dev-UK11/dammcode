"""
Model Capabilities definitions.

Standardizes capability tags and maps them to known models,
including icons for each capability (Part 15).
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class CapabilityInfo:
    """Info about a single capability, including its icon (Part 15)."""
    name: str
    icon: str

class ModelCapabilities:
    """
    Constants for ALL standard model capabilities, with icons (Part 15).
    """
    # Core capabilities (Part 15)
    CODING = "Coding"
    GENERAL_CHAT = "General Chat"
    REASONING = "Reasoning"
    VISION = "Vision"
    IMAGE_GENERATION = "Image Generation"
    AUDIO = "Audio"
    SPEECH_TO_TEXT = "Speech-to-Text"
    TEXT_TO_SPEECH = "Text-to-Speech"
    VIDEO = "Video"
    TOOL_CALLING = "Tool Calling"
    FUNCTION_CALLING = "Function Calling"
    JSON_MODE = "JSON Mode"
    STRUCTURED_OUTPUT = "Structured Output"
    STREAMING = "Streaming"
    EMBEDDINGS = "Embeddings"
    LONG_CONTEXT = "Long Context"
    THINKING_MODE = "Thinking Mode"
    MULTI_MODAL = "Multi-modal"
    OFFLINE = "Offline"
    
    @classmethod
    def get_icon(cls, capability: str) -> str:
        """Get the icon for a capability (Part 15)."""
        icon_map = {
            cls.CODING: "💻",
            cls.GENERAL_CHAT: "💬",
            cls.REASONING: "🧠",
            cls.VISION: "👁",
            cls.IMAGE_GENERATION: "🖼",
            cls.AUDIO: "🎵",
            cls.SPEECH_TO_TEXT: "🎤",
            cls.TEXT_TO_SPEECH: "🔊",
            cls.VIDEO: "🎬",
            cls.TOOL_CALLING: "🛠",
            cls.FUNCTION_CALLING: "⚙",
            cls.JSON_MODE: "📄",
            cls.STRUCTURED_OUTPUT: "📋",
            cls.STREAMING: "⚡",
            cls.EMBEDDINGS: "🔍",
            cls.LONG_CONTEXT: "📚",
            cls.THINKING_MODE: "🤔",
            cls.MULTI_MODAL: "📷",
            cls.OFFLINE: "🔌",
        }
        return icon_map.get(capability, "❓")

# Pre-defined capability mappings (Heuristics)
DEFAULT_CAPABILITIES = {
    "gemini": [
        ModelCapabilities.CODING,
        ModelCapabilities.GENERAL_CHAT,
        ModelCapabilities.REASONING,
        ModelCapabilities.VISION,
        ModelCapabilities.LONG_CONTEXT,
        ModelCapabilities.MULTI_MODAL,
        ModelCapabilities.STREAMING,
    ],
    "qwen": [
        ModelCapabilities.CODING,
        ModelCapabilities.GENERAL_CHAT,
        ModelCapabilities.REASONING,
        ModelCapabilities.OFFLINE,
        ModelCapabilities.LONG_CONTEXT,
        ModelCapabilities.STREAMING,
    ],
    "deepseek": [
        ModelCapabilities.CODING,
        ModelCapabilities.REASONING,
        ModelCapabilities.THINKING_MODE,
        ModelCapabilities.LONG_CONTEXT,
        ModelCapabilities.STREAMING,
    ],
    "claude": [
        ModelCapabilities.CODING,
        ModelCapabilities.REASONING,
        ModelCapabilities.VISION,
        ModelCapabilities.TOOL_CALLING,
        ModelCapabilities.LONG_CONTEXT,
        ModelCapabilities.STREAMING,
    ],
    "llama": [
        ModelCapabilities.GENERAL_CHAT,
        ModelCapabilities.REASONING,
        ModelCapabilities.LONG_CONTEXT,
        ModelCapabilities.STREAMING,
    ]
}
