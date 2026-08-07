"""
AI Chat Engine — v1.5

First Working AI implementation.
Handles real AI communication with Ollama and Gemini providers.
Supports streaming, model switching, and chat history management.
"""

import threading
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from core.logger import setup_logger
from core.event_bus import EventBus

from ai.providers.provider_registry import ProviderRegistry
from ai.providers.provider_manager import ProviderManager
from ai.models.model_center import ModelCenter
from ai.models.model_registry import ModelRegistry


logger = setup_logger(__name__)


@dataclass
class ChatMessage:
    """A single chat message."""
    role: str  # user, assistant, system
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    model_id: Optional[str] = None
    message_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "model_id": self.model_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatMessage":
        msg = cls(
            role=data["role"],
            content=data["content"],
            model_id=data.get("model_id"),
        )
        if data.get("timestamp"):
            from datetime import datetime
            msg.timestamp = datetime.fromisoformat(data["timestamp"])
        return msg


@dataclass
class ChatSession:
    """A chat session with a model."""
    session_id: str
    title: str
    model_id: str
    provider_name: str
    messages: List[ChatMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    is_pinned: bool = False
    
    def add_message(self, message: ChatMessage) -> None:
        self.messages.append(message)
        self.last_activity = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "title": self.title,
            "model_id": self.model_id,
            "provider_name": self.provider_name,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "is_pinned": self.is_pinned,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatSession":
        session = cls(
            session_id=data["session_id"],
            title=data["title"],
            model_id=data["model_id"],
            provider_name=data["provider_name"],
        )
        if data.get("messages"):
            session.messages = [ChatMessage.from_dict(m) for m in data["messages"]]
        if data.get("created_at"):
            from datetime import datetime
            session.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("last_activity"):
            session.last_activity = datetime.fromisoformat(data["last_activity"])
        session.is_pinned = data.get("is_pinned", False)
        return session


class AIChatEngine:
    """
    AI Chat Engine for real AI communication.
    
    Features:
    - Real AI model communication (Ollama, Gemini)
    - Streaming responses with token-by-token delivery
    - Model switching during runtime
    - Chat history management
    - Session persistence
    - Error handling with helpful messages
    """
    
    def __init__(self, event_bus: EventBus,
                 provider_registry: ProviderRegistry,
                 provider_manager: ProviderManager,
                 model_center: ModelCenter,
                 model_registry: ModelRegistry):
        self.event_bus = event_bus
        self.provider_registry = provider_registry
        self.provider_manager = provider_manager
        self.model_center = model_center
        self.model_registry = model_registry
        
        self._sessions: Dict[str, ChatSession] = {}
        self._current_session_id: Optional[str] = None
        self._current_provider: Optional[str] = None
        self._current_model: Optional[str] = None
        self._streaming_active: bool = False
        self._cancel_stream: bool = False
        
        self._logger = logger
        
        # Load sessions from storage
        self._load_sessions()
        
        # Initialize model router for auto-selection
        from ai.models.router import ModelRouter
        self._model_router = ModelRouter(self.model_registry, self.provider_manager)
        
        # Auto-select best available model on startup if no session exists
        if not self._current_model:
            self._auto_select_initial_model()
        
        # Subscribe to events
        event_bus.subscribe("ai_chat_send", self._on_chat_send)
        event_bus.subscribe("ai_chat_switch_model", self._on_switch_model)
        event_bus.subscribe("ai_chat_cancel", self._on_cancel_stream)
        event_bus.subscribe("ai_chat_new_session", self._on_new_session)
        event_bus.subscribe("ai_chat_delete_session", self._on_delete_session)
        event_bus.subscribe("ai_chat_rename_session", self._on_rename_session)
        event_bus.subscribe("ai_chat_pin_session", self._on_pin_session)
        event_bus.subscribe("ai_chat_export", self._on_export_session)
        event_bus.subscribe("ai_chat_import", self._on_import_session)
    
    def _auto_select_initial_model(self) -> None:
        """Auto-select the best available model on startup."""
        try:
            from ai.models.router import TaskType
            self._logger.info("Auto-selecting best available model on startup...")
            best_model = self._model_router.select_best_model(TaskType.SIMPLE_CHAT)
            if best_model:
                self._current_model = best_model
                self._update_current_provider(best_model)
                self._logger.info(f"✓ Auto-selected initial model: {best_model} (can reply and is active)")
                self.event_bus.publish("ai_model_auto_selected", {
                    "model_id": best_model,
                    "reason": "automatic_startup_selection"
                })
            else:
                self._logger.warning("⚠ No active models available for auto-selection on startup")
                self.event_bus.publish("ai_model_selection_failed", {
                    "reason": "no_active_models_available"
                })
        except Exception as e:
            self._logger.error(f"Failed to auto-select initial model: {e}", exc_info=True)
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Session Management
    # ─────────────────────────────────────────────────────────────────────────────

    def _load_sessions(self) -> None:
        """Load sessions from storage."""
        try:
            import json
            from pathlib import Path
            
            storage_file = Path("config/chat_sessions.json")
            if storage_file.exists():
                with open(storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for session_data in data.get("sessions", []):
                        session = ChatSession.from_dict(session_data)
                        self._sessions[session.session_id] = session
                
                self._logger.info(f"Loaded {len(self._sessions)} chat sessions")
                
                # Set current session if available
                if data.get("current_session_id"):
                    self._current_session_id = data["current_session_id"]
                    self._current_model = self._sessions[self._current_session_id].model_id
                    self._current_provider = self._sessions[self._current_session_id].provider_name
                    
        except Exception as e:
            self._logger.error(f"Failed to load sessions: {e}")
    
    def _save_sessions(self) -> None:
        """Save sessions to storage."""
        try:
            import json
            from pathlib import Path
            
            storage_file = Path("config/chat_sessions.json")
            
            data = {
                "sessions": [s.to_dict() for s in self._sessions.values()],
                "current_session_id": self._current_session_id,
                "saved_at": datetime.utcnow().isoformat(),
            }
            
            storage_file.parent.mkdir(parents=True, exist_ok=True)
            with open(storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self._logger.error(f"Failed to save sessions: {e}")
    
    def create_session(self, model_id: Optional[str] = None,
                       title: Optional[str] = None) -> str:
        """Create a new chat session."""
        import uuid
        
        session_id = str(uuid.uuid4())[:8]
        
        # Auto-select best model if not provided
        if not model_id:
            from ai.models.router import TaskType
            model_id = self._model_router.select_best_model(TaskType.SIMPLE_CHAT)
            if not model_id:
                # Fallback to current model if router fails
                model_id = self._current_model
                if not model_id:
                    self._logger.error("No models available for new chat session")
                    raise RuntimeError("No active AI models available. Please connect a provider first.")
        
        model = model_id
        
        # Update current model
        self._current_model = model
        self._update_current_provider(model)
        
        provider = self._current_provider or "ollama"
        
        if not title:
            title = f"Chat {len(self._sessions) + 1}"
        
        session = ChatSession(
            session_id=session_id,
            title=title,
            model_id=model,
            provider_name=provider,
        )
        
        self._sessions[session_id] = session
        self._current_session_id = session_id
        
        self._save_sessions()
        
        self._logger.info(f"Created session {session_id} with model {model}")
        self.event_bus.publish("ai_chat_session_created", {
            "session_id": session_id,
            "model_id": model,
            "title": title,
        })
        
        return session_id
    
    def _update_current_provider(self, model_id: str) -> None:
        """Update current provider based on model."""
        model = self.model_center.get_model(model_id)
        if model:
            self._current_provider = model.provider
            self._current_model = model_id
            self._logger.info(f"Updated current provider to {model.provider} for model {model_id}")
    
    def get_current_session(self) -> Optional[ChatSession]:
        """Get the current chat session."""
        if self._current_session_id:
            return self._sessions.get(self._current_session_id)
        return None
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a specific session."""
        return self._sessions.get(session_id)
    
    def get_all_sessions(self) -> List[ChatSession]:
        """Get all sessions."""
        return list(self._sessions.values())
    
    def switch_session(self, session_id: str) -> bool:
        """Switch to a different session."""
        if session_id not in self._sessions:
            return False
        
        self._current_session_id = session_id
        session = self._sessions[session_id]
        self._current_model = session.model_id
        self._current_provider = session.provider_name
        
        self._save_sessions()
        
        self._logger.info(f"Switched to session {session_id}")
        self.event_bus.publish("ai_chat_session_switched", {
            "session_id": session_id,
            "model_id": session.model_id,
        })
        
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id not in self._sessions:
            return False
        
        del self._sessions[session_id]
        
        if self._current_session_id == session_id:
            if self._sessions:
                self._current_session_id = list(self._sessions.keys())[0]
            else:
                self._current_session_id = None
        
        self._save_sessions()
        
        self._logger.info(f"Deleted session {session_id}")
        self.event_bus.publish("ai_chat_session_deleted", {"session_id": session_id})
        
        return True
    
    def rename_session(self, session_id: str, new_title: str) -> bool:
        """Rename a session."""
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        session.title = new_title
        self._save_sessions()
        
        self._logger.info(f"Renamed session {session_id} to {new_title}")
        self.event_bus.publish("ai_chat_session_renamed", {
            "session_id": session_id,
            "title": new_title,
        })
        
        return True
    
    def pin_session(self, session_id: str, pinned: bool) -> bool:
        """Pin/unpin a session."""
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        session.is_pinned = pinned
        self._save_sessions()
        
        self._logger.info(f"Session {session_id} {'pinned' if pinned else 'unpinned'}")
        self.event_bus.publish("ai_chat_session_pinned", {
            "session_id": session_id,
            "pinned": pinned,
        })
        
        return True
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Message Sending
    # ─────────────────────────────────────────────────────────────────────────────

    def send_message(self, message: str,
                     model_id: Optional[str] = None,
                     on_chunk: Optional[Callable[[str], None]] = None,
                     on_complete: Optional[Callable[[str], None]] = None) -> str:
        """
        Send a message and get a streamed response.
        
        Args:
            message: The user message
            model_id: Model to use (optional, uses current)
            on_chunk: Callback for each streamed chunk
            on_complete: Callback when complete
            
        Returns:
            Message ID
        """
        session = self.get_current_session()
        if not session:
            session_id = self.create_session(model_id=model_id)
            session = self.get_session(session_id)
        
        if model_id:
            session.model_id = model_id
            session.provider_name = self._current_provider or "ollama"
            self._current_model = model_id
        
        # Create user message
        user_msg = ChatMessage(
            role="user",
            content=message,
            model_id=session.model_id,
        )
        session.add_message(user_msg)
        
        self.event_bus.publish("ai_chat_message_added", {
            "session_id": session.session_id,
            "role": "user",
            "content": message,
        })
        
        # Start background thread for AI response
        thread = threading.Thread(
            target=self._generate_response_sync,
            args=(session, message, on_chunk, on_complete),
            daemon=True
        )
        thread.start()
        
        self._logger.info(f"Sent message to {session.model_id} in session {session.session_id}")
        return user_msg.message_id or user_msg.timestamp.isoformat()
    
    def _generate_response_sync(self, session: ChatSession,
                                user_message: str,
                                on_chunk: Optional[Callable[[str], None]],
                                on_complete: Optional[Callable[[str], None]]) -> None:
        """
        Generate AI response in background thread.
        
        Resolves the provider in this order:
        1. Extract provider name from model_id prefix  (e.g. "ollama:qwen2.5-coder:7b")
        2. Look up via model_center if step 1 fails
        3. Fall back to the router's best available model
        
        Auto-reconnects the provider if it is not yet connected (handles cold start).
        """
        self._streaming_active = True
        self._cancel_stream = False
        
        current_model_id = session.model_id
        self._logger.info(f"_generate_response_sync: model='{current_model_id}'")
        
        # ── Step 1: Resolve provider + actual model name ──────────────────────
        provider = None
        actual_model_id = current_model_id   # what we pass to the API

        # Model IDs from the combo are stored as  "providerName:model_name"
        # e.g. "ollama:qwen2.5-coder:7b"  or  "ollama:llama3:8b"
        # Split on first ":" to get provider key, keep the rest as model name.
        if ":" in current_model_id:
            provider_key, actual_model_id = current_model_id.split(":", 1)
            provider = self.provider_registry.get_provider(provider_key)
            if provider:
                self._logger.info(f"Resolved provider '{provider_key}' from model ID prefix")
        
        # Fallback: look up via model_center
        if not provider:
            model_info = self.model_center.get_model(current_model_id)
            if model_info:
                provider = self.provider_registry.get_provider(model_info.provider)
                actual_model_id = current_model_id   # model_center stores full id
                if ":" in current_model_id:
                    actual_model_id = current_model_id.split(":", 1)[1]
        
        # Final fallback: use router to find any working model
        if not provider:
            self._logger.warning(
                f"Could not resolve provider for '{current_model_id}'. "
                "Asking router for best available model."
            )
            best = self._model_router.select_best_model()
            if best:
                current_model_id = best
                if ":" in best:
                    pkey, actual_model_id = best.split(":", 1)
                    provider = self.provider_registry.get_provider(pkey)
                    session.model_id = best
                    self._update_current_provider(best)
                    self.event_bus.publish("ai_chat_failover", {
                        "old_model": session.model_id,
                        "new_model": best,
                        "reason": "Original model provider not found"
                    })
        
        if not provider:
            self._handle_error(
                "No AI provider available. Make sure Ollama is running (`ollama serve`) "
                "or connect a cloud provider in Settings.",
                on_chunk, on_complete
            )
            return
        
        # ── Step 2: Ensure provider is connected (auto-reconnect) ─────────────
        if not provider.is_connected():
            self._logger.info(f"Provider '{provider.config.provider_name}' not connected, attempting to connect…")
            try:
                connected = provider.connect()
                if not connected:
                    self._handle_error(
                        f"Cannot connect to '{provider.config.provider_name}'. "
                        "Please make sure Ollama is running: open a terminal and run `ollama serve`.",
                        on_chunk, on_complete
                    )
                    return
                self._logger.info(f"Provider '{provider.config.provider_name}' connected successfully")
            except Exception as ce:
                self._handle_error(
                    f"Connection failed for '{provider.config.provider_name}': {ce}",
                    on_chunk, on_complete
                )
                return
        
        # ── Step 3: Stream the response ───────────────────────────────────────
        self._logger.info(
            f"Streaming from provider='{provider.config.provider_name}' "
            f"model='{actual_model_id}'"
        )
        
        current_message = ChatMessage(
            role="assistant",
            content="",
            model_id=current_model_id,
        )
        
        self.event_bus.publish("ai_chat_streaming_started", {
            "session_id": session.session_id,
            "model_id": current_model_id,
        })
        
        try:
            response = provider.stream_response(
                prompt=user_message,
                model_id=actual_model_id,
                on_chunk=lambda chunk: self._handle_chunk(chunk, current_message, on_chunk),
            )
            
            # stream_response returns the full accumulated text
            full_response = response if response else current_message.content
            current_message.content = full_response
            session.add_message(current_message)
            self._streaming_active = False
            
            self.event_bus.publish("ai_chat_streaming_complete", {
                "session_id": session.session_id,
                "content_length": len(full_response),
            })
            
            if on_complete:
                on_complete(full_response)
            
            self._logger.info(
                f"Response complete: {len(full_response)} chars from '{actual_model_id}'"
            )
            
        except Exception as e:
            self._streaming_active = False
            self._logger.error(f"Streaming failed: {e}", exc_info=True)
            
            # Try failover to another model
            best = self._model_router.select_best_model()
            if best and best != current_model_id:
                self._logger.info(f"Failing over to '{best}'")
                self.event_bus.publish("ai_chat_failover", {
                    "old_model": current_model_id,
                    "new_model": best,
                    "reason": str(e)
                })
                session.model_id = best
                self._update_current_provider(best)
                # Re-enter with new model
                self._generate_response_sync(session, user_message, on_chunk, on_complete)
            else:
                self._handle_error(str(e), on_chunk, on_complete)
    
    def _handle_chunk(self, chunk: str, message: ChatMessage,
                      on_chunk: Optional[Callable[[str], None]]) -> None:
        """Handle a streaming chunk."""
        if self._cancel_stream:
            raise Exception("Streaming cancelled")
        
        message.content += chunk
        
        if on_chunk:
            on_chunk(chunk)
        
        self.event_bus.publish("ai_chat_chunk", {
            "chunk": chunk,
            "message_id": message.message_id,
        })
    
    def _handle_error(self, error: str,
                      on_chunk: Optional[Callable[[str], None]],
                      on_complete: Optional[Callable[[str], None]]) -> None:
        """Handle an error during streaming."""
        self._streaming_active = False
        
        self.event_bus.publish("ai_chat_error", {
            "error": error,
        })
        
        if on_chunk:
            on_chunk(f"\n\n**Error:** {error}")
        
        if on_complete:
            on_complete(f"\n\n**Error:** {error}")
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Event Handlers
    # ─────────────────────────────────────────────────────────────────────────────

    def _on_chat_send(self, data: dict) -> None:
        """Handle chat send event."""
        message = data.get("message", "")
        model_id = data.get("model_id")
        on_chunk = data.get("on_chunk")
        on_complete = data.get("on_complete")
        
        if message:
            self.send_message(message, model_id, on_chunk, on_complete)
    
    def _on_switch_model(self, data: dict) -> None:
        """Handle model switch event."""
        model_id = data.get("model_id")
        session_id = data.get("session_id", self._current_session_id)
        
        if model_id:
            session = self._sessions.get(session_id)
            if session:
                session.model_id = model_id
                self._update_current_provider(model_id)
                self._save_sessions()
                self.event_bus.publish("ai_chat_model_switched", {
                    "session_id": session_id,
                    "model_id": model_id,
                })
    
    def _on_cancel_stream(self, data: dict) -> None:
        """Handle cancel stream event."""
        self._cancel_stream = True
        self._streaming_active = False
        self.event_bus.publish("ai_chat_stream_cancelled", {})
    
    def _on_new_session(self, data: dict) -> None:
        """Handle new session event."""
        title = data.get("title", "New Chat")
        model_id = data.get("model_id")
        self.create_session(model_id=model_id, title=title)
    
    def _on_delete_session(self, data: dict) -> None:
        """Handle delete session event."""
        session_id = data.get("session_id")
        if session_id:
            self.delete_session(session_id)
    
    def _on_rename_session(self, data: dict) -> None:
        """Handle rename session event."""
        session_id = data.get("session_id")
        new_title = data.get("title")
        if session_id and new_title:
            self.rename_session(session_id, new_title)
    
    def _on_pin_session(self, data: dict) -> None:
        """Handle pin session event."""
        session_id = data.get("session_id")
        pinned = data.get("pinned", True)
        if session_id:
            self.pin_session(session_id, pinned)
    
    def _on_export_session(self, data: dict) -> Optional[str]:
        """Handle export session event."""
        session_id = data.get("session_id")
        if not session_id:
            return None
        
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        import json
        export_data = {
            "session": session.to_dict(),
            "exported_at": datetime.utcnow().isoformat(),
        }
        
        return json.dumps(export_data, indent=2)
    
    def _on_import_session(self, data: dict) -> str:
        """Handle import session event."""
        import json
        from pathlib import Path
        
        content = data.get("content")
        if not content:
            return "No content provided"
        
        try:
            data = json.loads(content)
            session_data = data.get("session")
            
            if session_data:
                session = ChatSession.from_dict(session_data)
                self._sessions[session.session_id] = session
                self._save_sessions()
                return f"Imported session: {session.title}"
            else:
                return "Invalid session format"
                
        except json.JSONDecodeError as e:
            return f"Failed to import: {str(e)}"
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Utility Methods
    # ─────────────────────────────────────────────────────────────────────────────

    def get_available_models(self) -> Dict[str, str]:
        """Get available models for selection (returns all models regardless of provider availability)."""
        try:
            # Get all models, not just enabled ones
            all_models = self.model_center.get_all_models()
            return {m.model_id: m.display_name for m in all_models.values()}
        except Exception as e:
            self._logger.error(f"Failed to get available models: {e}")
            return {}
    
    def get_current_provider(self) -> Optional[str]:
        """Get current provider name."""
        return self._current_provider
    
    def get_current_model(self) -> Optional[str]:
        """Get current model ID."""
        return self._current_model
    
    def is_streaming(self) -> bool:
        """Check if streaming is active."""
        return self._streaming_active
    
    def test_provider_connection(self, provider_name: str) -> Dict[str, Any]:
        """Test provider connection."""
        provider = self.provider_registry.get_provider(provider_name)
        if not provider:
            return {"success": False, "error": "Provider not found"}
        
        try:
            success = provider.test_connection()
            return {
                "success": success,
                "status": provider.get_status().value,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global instance
_ai_chat_engine = None


def get_ai_chat_engine() -> AIChatEngine:
    """Get the global AI chat engine."""
    global _ai_chat_engine
    if _ai_chat_engine is None:
        raise RuntimeError("AIChatEngine not initialized")
    return _ai_chat_engine


def initialize_ai_chat_engine(event_bus, provider_registry, provider_manager,
                               model_center, model_registry) -> AIChatEngine:
    """Initialize the global AI chat engine."""
    global _ai_chat_engine
    _ai_chat_engine = AIChatEngine(
        event_bus=event_bus,
        provider_registry=provider_registry,
        provider_manager=provider_manager,
        model_center=model_center,
        model_registry=model_registry,
    )
    return _ai_chat_engine


def reset_ai_chat_engine():
    """Reset the global AI chat engine."""
    global _ai_chat_engine
    _ai_chat_engine = None
