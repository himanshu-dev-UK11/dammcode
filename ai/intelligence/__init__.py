"""
Project Intelligence Engine.

This package provides the core intelligence layer for MyCodingMaster.
It automatically understands every project before any AI model is asked
to generate code.

Key capabilities:
- Project architecture detection
- Dependency graph building
- Symbol indexing
- Entry point detection
- Impact analysis
- Health scoring
- Documentation indexing
"""

from ai.intelligence.project_analyzer import ProjectAnalyzer
from ai.intelligence.architecture_detector import ArchitectureDetector
from ai.intelligence.dependency_graph import DependencyGraph
from ai.intelligence.symbol_indexer import SymbolIndexer
from ai.intelligence.reference_index import ReferenceIndex
from ai.intelligence.impact_analyzer import ImpactAnalyzer
from ai.intelligence.project_health import ProjectHealth
from ai.intelligence.language_statistics import LanguageStatistics
from ai.intelligence.entry_point_detector import EntryPointDetector
from ai.intelligence.documentation_indexer import DocumentationIndexer

__all__ = [
    "ProjectAnalyzer",
    "ArchitectureDetector",
    "DependencyGraph",
    "SymbolIndexer",
    "ReferenceIndex",
    "ImpactAnalyzer",
    "ProjectHealth",
    "LanguageStatistics",
    "EntryPointDetector",
    "DocumentationIndexer",
]