"""
DeepSeek integration.
"""

from ai.models.base_model import BaseModel

class DeepSeekModel(BaseModel):
    def __init__(self, api_key: str):
        super().__init__("deepseek")
        self.api_key = api_key
        
    def generate_response(self, prompt: str) -> str:
        self.logger.info("Sending prompt to DeepSeek...")
        return ""
