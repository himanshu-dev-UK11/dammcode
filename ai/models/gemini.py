"""
Gemini model integration.
"""

from ai.models.base_model import BaseModel

class GeminiModel(BaseModel):
    def __init__(self, api_key: str):
        super().__init__("gemini")
        self.api_key = api_key
        
    def generate_response(self, prompt: str) -> str:
        self.logger.info("Sending prompt to Gemini...")
        return ""
