"""
Event Bus for asynchronous communication — v1.7.2

Decouples UI from heavy processing. Ensures UI callbacks ALWAYS execute on the
Qt main thread, preventing cross-thread errors and crashes.
"""

from PySide6.QtCore import QObject, Signal, Qt
from core.logger import setup_logger

logger = setup_logger(__name__)


class EventBus(QObject):
    """
    Manages pub/sub event distribution across the app.
    Uses Qt's thread-safe signal system to ensure UI updates happen on main thread.
    """

    event_signal = Signal(str, dict)  # event_type, data

    def __init__(self):
        super().__init__()
        self.subscribers = {}
        self.event_signal.connect(self._dispatch_event, Qt.QueuedConnection)
        
    def subscribe(self, event_type: str, callback):
        """
        Register a callback for a specific event type.
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        logger.debug(f"New subscriber added for event: {event_type}")
        
    def publish(self, event_type: str, data: dict = None):
        """
        Broadcast an event to all subscribers.
        Uses Qt's QueuedConnection to ensure callbacks run in the main thread when needed.
        """
        logger.debug(f"Publishing event: {event_type}")
        self.event_signal.emit(event_type, data or {})
        
    def _dispatch_event(self, event_type: str, data: dict):
        """
        Internal dispatch method that runs in the main thread.
        """
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in event callback for {event_type}: {e}", exc_info=True)
