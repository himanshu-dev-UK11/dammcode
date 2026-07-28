"""
ai.context — Intelligent Context Engine

Public surface:

    ContextEngine      — main orchestrator (entry point)
    ContextPackage     — the result object passed to the Model Manager
    SelectedFile       — one file selected for inclusion in context
"""

from ai.context.context_engine import ContextEngine
from ai.context.context_engine import ContextPackage, SelectedFile

__all__ = ["ContextEngine", "ContextPackage", "SelectedFile"]
