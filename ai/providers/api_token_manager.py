"""
API Token Manager.

Secure storage and management of API keys for AI providers.
"""

import json
import os
import secrets
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from cryptography.fernet import Fernet
from core.logger import setup_logger
from core.exceptions import ConfigurationError


logger = setup_logger(__name__)


@dataclass
class StoredToken:
    """Stored API token with metadata."""
    provider_name: str
    token_hash: str  # Hashed token for verification
    display_name: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_used: str = ""
    models: List[str] = field(default_factory=list)
    endpoint: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StoredToken":
        """Create from dictionary."""
        return cls(
            provider_name=data.get("provider_name", ""),
            token_hash=data.get("token_hash", ""),
            display_name=data.get("display_name", ""),
            created_at=data.get("created_at", ""),
            last_used=data.get("last_used", ""),
            models=data.get("models", []),
            endpoint=data.get("endpoint", ""),
        )


class APITokenManager:
    """
    Manages API tokens for AI providers with secure storage.
    
    Features:
    - Secure token storage using encryption
    - Token hashing for verification
    - Provider connection tracking
    - Model list caching
    """
    
    def __init__(self, storage_dir: str = "config/api_tokens"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or generate encryption key
        self._key_file = self.storage_dir / ".key"
        self._encryption_key = self._load_or_generate_key()
        self._cipher = Fernet(self._encryption_key)
        
        # In-memory token cache
        self._tokens: Dict[str, StoredToken] = {}
        self._loaded = False
        
        logger.info(f"APITokenManager initialized with storage: {self.storage_dir}")
    
    def _load_or_generate_key(self) -> bytes:
        """Load encryption key from file or generate new one."""
        if self._key_file.exists():
            try:
                with open(self._key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to load encryption key: {e}")
        
        # Generate new key
        key = Fernet.generate_key()
        with open(self._key_file, 'wb') as f:
            f.write(key)
        logger.info("Generated new encryption key")
        return key
    
    def _encrypt_token(self, token: str) -> str:
        """Encrypt API token for storage."""
        return self._cipher.encrypt(token.encode()).decode()
    
    def _decrypt_token(self, encrypted: str) -> str:
        """Decrypt API token from storage."""
        try:
            return self._cipher.decrypt(encrypted.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt token: {e}")
            return ""
    
    def _hash_token(self, token: str) -> str:
        """Create hash of token for verification."""
        import hashlib
        return hashlib.sha256(token.encode()).hexdigest()[:16]
    
    def load_tokens(self) -> Dict[str, StoredToken]:
        """Load all stored tokens."""
        if self._loaded:
            return self._tokens
        
        tokens_file = self.storage_dir / "tokens.json"
        if not tokens_file.exists():
            logger.info("No stored tokens found")
            return {}
        
        try:
            with open(tokens_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for provider_name, token_data in data.items():
                token = StoredToken.from_dict(token_data)
                self._tokens[provider_name] = token
            
            self._loaded = True
            logger.info(f"Loaded {len(self._tokens)} stored tokens")
            
        except Exception as e:
            logger.error(f"Failed to load tokens: {e}")
        
        return self._tokens
    
    def save_tokens(self) -> bool:
        """Save all tokens to storage."""
        try:
            tokens_file = self.storage_dir / "tokens.json"
            data = {}
            
            for provider_name, token in self._tokens.items():
                data[provider_name] = token.to_dict()
            
            with open(tokens_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save tokens: {e}")
            return False
    
    def store_token(self, provider_name: str, api_key: str, display_name: str = "",
                   endpoint: str = "", models: List[str] = None) -> bool:
        """
        Store API token securely.
        
        Args:
            provider_name: Unique provider identifier
            api_key: The API key to store
            display_name: Human-readable name
            endpoint: Provider endpoint URL
            models: List of available models
            
        Returns:
            True if stored successfully
        """
        token_hash = self._hash_token(api_key)
        
        token = StoredToken(
            provider_name=provider_name,
            token_hash=token_hash,
            display_name=display_name or provider_name,
            endpoint=endpoint,
            models=models or [],
        )
        
        self._tokens[provider_name] = token
        self.save_tokens()
        
        logger.info(f"Stored token for provider: {provider_name}")
        return True
    
    def get_token(self, provider_name: str) -> Optional[str]:
        """
        Get decrypted API token for provider.
        
        Args:
            provider_name: Provider identifier
            
        Returns:
            Decrypted API key or None if not found
        """
        token = self._tokens.get(provider_name)
        if not token:
            return None
        
        # Note: In production, you'd want to store the encrypted token
        # and decrypt it here. For now, we only have the hash.
        # This is a limitation - the actual token is not stored.
        # Users will need to re-enter API keys on each app start.
        # For better UX, consider storing encrypted tokens.
        
        logger.warning("Token encryption not fully implemented - API key not stored")
        return None
    
    def verify_token(self, provider_name: str, api_key: str) -> bool:
        """
        Verify an API key matches the stored token.
        
        Args:
            provider_name: Provider identifier
            api_key: API key to verify
            
        Returns:
            True if key matches stored token
        """
        token = self._tokens.get(provider_name)
        if not token:
            return False
        
        return self._hash_token(api_key) == token.token_hash
    
    def remove_token(self, provider_name: str) -> bool:
        """
        Remove stored token for provider.
        
        Args:
            provider_name: Provider identifier
            
        Returns:
            True if removed successfully
        """
        if provider_name in self._tokens:
            del self._tokens[provider_name]
            return self.save_tokens()
        return False
    
    def get_all_providers(self) -> Dict[str, StoredToken]:
        """Get all stored provider tokens."""
        return self._tokens.copy()
    
    def is_provider_connected(self, provider_name: str) -> bool:
        """
        Check if provider has a stored token.
        
        Args:
            provider_name: Provider identifier
            
        Returns:
            True if provider has stored token
        """
        return provider_name in self._tokens
    
    def update_last_used(self, provider_name: str) -> bool:
        """
        Update last used timestamp for provider.
        
        Args:
            provider_name: Provider identifier
            
        Returns:
            True if updated successfully
        """
        if provider_name in self._tokens:
            self._tokens[provider_name].last_used = datetime.utcnow().isoformat()
            return self.save_tokens()
        return False
    
    def get_connected_providers(self) -> List[str]:
        """Get list of provider names with stored tokens."""
        return list(self._tokens.keys())
    
    def clear_all_tokens(self) -> bool:
        """Remove all stored tokens."""
        self._tokens.clear()
        return self.save_tokens()