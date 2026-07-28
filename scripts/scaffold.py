import os

base_dir = "c:/projects/mycodingmaster"

# ---------------------------------------------------------------------
# PURPOSE AND FUTURE USE:
# This script is a "Project Generator" (Scaffold). 
# Its sole purpose is to quickly bootstrap the entire project structure 
# from scratch on a new machine or reset it. 
# 
# How it works in the app:
# 1. It holds the source code for all the base files as strings.
# 2. When run, it creates the folders and writes the files to the hard drive.
# 
# Once the project is generated and we are actively coding in the actual 
# files (like main.py, ui/, etc.), this script is no longer used for 
# day-to-day development. It serves purely as a backup or a way to 
# reproduce the project structure elsewhere.
# ---------------------------------------------------------------------

files = {
    "main.py": '''"""
Application entry point for MyCodingMaster.

Initializes core systems (logging, event bus) and starts the main event loop.
"""

from core.logger import setup_logger
from core.event_bus import EventBus
from ui.main_window import MainWindow

logger = setup_logger(__name__)

def main():
    """
    Main execution function.
    """
    logger.info("Initializing MyCodingMaster core systems...")
    
    # Initialize the global event bus
    event_bus = EventBus()
    
    logger.info("Starting UI event loop...")
    app = MainWindow(event_bus)
    app.run()

if __name__ == "__main__":
    main()
''',
    "core/__init__.py": "",
    "core/logger.py": '''"""
Centralized structured logging system.

Ensures all application components log errors uniformly, making debugging trivial.
"""

import logging
import sys

def setup_logger(name: str) -> logging.Logger:
    """
    Creates and configures a standard logger for a module.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    if not logger.handlers:
        # Console handler for development
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s | %(name)-15s | %(levelname)-8s | %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
    return logger
''',
    "core/event_bus.py": '''"""
Event Bus for asynchronous communication.

Decouples UI from heavy AI processing. Prevents UI freezes and delays by
allowing components to subscribe to and publish events asynchronously.
"""

from core.logger import setup_logger
import threading

logger = setup_logger(__name__)

class EventBus:
    """
    Manages pub/sub event distribution across the app.
    """
    def __init__(self):
        self.subscribers = {}
        
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
        Executes callbacks in a separate thread to prevent blocking the UI.
        """
        logger.debug(f"Publishing event: {event_type}")
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                threading.Thread(target=callback, args=(data,), daemon=True).start()
''',
    "core/exceptions.py": '''"""
Custom application exceptions.

Provides clear, recognizable error types for easier debugging and crash reporting.
"""

class MyCodingMasterError(Exception):
    """Base exception for all application errors."""
    pass

class ModelTimeoutError(MyCodingMasterError):
    """Raised when an AI model takes too long to respond."""
    pass

class ToolExecutionError(MyCodingMasterError):
    """Raised when a tool (e.g., terminal, file) fails to execute."""
    pass
''',
    "ai/agents/base_agent.py": '''"""
Base Agent class.

Provides common functionality for all agents like logging, error handling,
and event bus integration.
"""

from core.logger import setup_logger

class BaseAgent:
    """
    Abstract base class for all AI agents.
    """
    def __init__(self, name: str, event_bus):
        self.name = name
        self.event_bus = event_bus
        self.logger = setup_logger(f"agent.{name}")
        self.logger.info(f"{name} agent initialized.")
        
    def handle_error(self, error: Exception):
        """
        Standardized error handling to prevent silent failures.
        """
        self.logger.error(f"Error in {self.name}: {str(error)}", exc_info=True)
''',
    "ai/agents/planner.py": '''"""
Project planning and roadmap generation agent.
"""

from ai.agents.base_agent import BaseAgent

class PlannerAgent(BaseAgent):
    def __init__(self, event_bus):
        super().__init__("planner", event_bus)
        
    def create_plan(self, goal: str) -> list:
        self.logger.info(f"Creating plan for goal: {goal}")
        return []
''',
    "ai/agents/coder.py": '''"""
Code generation and modification agent.
"""

from ai.agents.base_agent import BaseAgent

class CoderAgent(BaseAgent):
    def __init__(self, event_bus):
        super().__init__("coder", event_bus)
        
    def implement_task(self, task_description: str):
        self.logger.info(f"Implementing task: {task_description}")
        pass
''',
    "ai/agents/debugger.py": '''"""
Debugging and error fixing agent.
"""

from ai.agents.base_agent import BaseAgent

class DebuggerAgent(BaseAgent):
    def __init__(self, event_bus):
        super().__init__("debugger", event_bus)
        
    def analyze_error(self, error_message: str, context: str):
        self.logger.info("Analyzing error...")
        pass
''',
    "ai/models/base_model.py": '''"""
Base Model interface.

Ensures all models implement standard methods and uniform error handling.
"""

from core.logger import setup_logger
from core.exceptions import ModelTimeoutError

class BaseModel:
    """
    Abstract base class for AI models.
    """
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.logger = setup_logger(f"model.{provider_name}")
        
    def generate_response(self, prompt: str) -> str:
        raise NotImplementedError("Subclasses must implement generate_response")
''',
    "ai/models/router.py": '''"""
Model selection and routing logic.
"""

from core.logger import setup_logger

logger = setup_logger(__name__)

class ModelRouter:
    def __init__(self):
        logger.info("ModelRouter initialized.")
        pass
        
    def select_model(self, task_type: str):
        logger.debug(f"Routing task of type: {task_type}")
        pass
''',
    "ai/models/gemini.py": '''"""
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
''',
    "ai/models/qwen.py": '''"""
Local Qwen integration.
"""

from ai.models.base_model import BaseModel

class QwenModel(BaseModel):
    def __init__(self, endpoint: str):
        super().__init__("qwen")
        self.endpoint = endpoint
        
    def generate_response(self, prompt: str) -> str:
        self.logger.info("Sending prompt to Qwen...")
        return ""
''',
    "ai/models/deepseek.py": '''"""
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
''',
    "ai/tools/base_tool.py": '''"""
Base Tool class.
"""

from core.logger import setup_logger

class BaseTool:
    """
    Abstract base class for tools with common security checks and logging.
    """
    def __init__(self, name: str):
        self.name = name
        self.logger = setup_logger(f"tool.{name}")
''',
    "ai/tools/file_tool.py": '''"""
File operations tool.
"""

from ai.tools.base_tool import BaseTool

class FileTool(BaseTool):
    def __init__(self, workspace_root: str):
        super().__init__("file")
        self.workspace_root = workspace_root
        
    def read_file(self, path: str) -> str:
        self.logger.debug(f"Reading file: {path}")
        return ""
        
    def write_file(self, path: str, content: str):
        self.logger.debug(f"Writing to file: {path}")
        pass
''',
    "ai/tools/terminal_tool.py": '''"""
Terminal command execution tool.
"""

from ai.tools.base_tool import BaseTool

class TerminalTool(BaseTool):
    def __init__(self, workspace_root: str):
        super().__init__("terminal")
        self.workspace_root = workspace_root
        
    def run_command(self, command: str) -> str:
        self.logger.info(f"Running command: {command}")
        return ""
''',
    "ai/tools/git_tool.py": '''"""
Git operations tool.
"""

from ai.tools.base_tool import BaseTool

class GitTool(BaseTool):
    def __init__(self, repo_path: str):
        super().__init__("git")
        self.repo_path = repo_path
        
    def get_status(self) -> str:
        self.logger.debug("Checking git status...")
        return ""
''',
    "ai/tools/browser_tool.py": '''"""
Web search tool.
"""

from ai.tools.base_tool import BaseTool

class BrowserTool(BaseTool):
    def __init__(self):
        super().__init__("browser")
        
    def search(self, query: str) -> list:
        self.logger.info(f"Searching web for: {query}")
        return []
''',
    "ai/memory/project_memory.py": '''"""
Project information storage.
"""

from core.logger import setup_logger

logger = setup_logger(__name__)

class ProjectMemory:
    def __init__(self):
        logger.info("ProjectMemory initialized.")
        pass
''',
    "ai/memory/decision_memory.py": '''"""
User and project decision storage.
"""

from core.logger import setup_logger

logger = setup_logger(__name__)

class DecisionMemory:
    def __init__(self):
        logger.info("DecisionMemory initialized.")
        pass
''',
    "safety/delete_guard.py": '''"""
Deletion confirmation and protection layer.
"""

from core.logger import setup_logger

logger = setup_logger(__name__)

class DeleteGuard:
    def __init__(self):
        logger.info("DeleteGuard initialized.")
        pass
''',
    "config/settings.py": '''"""
Configuration management.
"""

from core.logger import setup_logger

logger = setup_logger(__name__)

class SettingsManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.settings = {}
        logger.info(f"SettingsManager initialized with config at {config_path}")
''',
    "ui/main_window.py": '''"""
Main window component for the desktop UI.
"""

from core.logger import setup_logger
from ui.chat_panel import ChatPanel
from ui.project_panel import ProjectPanel
from ui.settings_panel import SettingsPanel

logger = setup_logger(__name__)

class MainWindow:
    def __init__(self, event_bus):
        logger.debug("Initializing MainWindow UI components...")
        self.event_bus = event_bus
        self.chat_panel = ChatPanel(event_bus)
        self.project_panel = ProjectPanel(event_bus)
        self.settings_panel = SettingsPanel(event_bus)
        
    def run(self):
        logger.info("MainWindow event loop started. (Press Ctrl+C to exit in terminal)")
''',
    "ui/chat_panel.py": '''"""
Chat panel component for the desktop UI.
"""

from core.logger import setup_logger

logger = setup_logger(__name__)

class ChatPanel:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        logger.debug("ChatPanel initialized.")
        
    def send_message(self, message: str):
        logger.info("Sending message via event bus...")
        self.event_bus.publish("user_message", {"message": message})
''',
    "ui/project_panel.py": '''"""
Project panel component for the desktop UI.
"""

from core.logger import setup_logger

logger = setup_logger(__name__)

class ProjectPanel:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        logger.debug("ProjectPanel initialized.")
''',
    "ui/settings_panel.py": '''"""
Settings panel component for the desktop UI.
"""

from core.logger import setup_logger

logger = setup_logger(__name__)

class SettingsPanel:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        logger.debug("SettingsPanel initialized.")
'''
}

for path, content in files.items():
    full_path = os.path.join(base_dir, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print(f"Successfully generated scaffold at {base_dir}")
