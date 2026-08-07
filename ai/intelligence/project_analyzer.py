"""
Project Analyzer — orchestrates the Project Intelligence Engine.

When a project is opened, this analyzer runs all sub-analyzers,
aggregates their results, and produces a comprehensive ProjectIntelligence
object that describes the project's structure, architecture, and health.

The analyzer is asynchronous and runs in the background to avoid UI freezes.
Results are cached and only re-scanned when files change.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

from core.logger import setup_logger
from core.event_bus import EventBus

# Sub-analyzers
from ai.intelligence.architecture_detector import ArchitectureDetector
from ai.intelligence.dependency_graph import DependencyGraph
from ai.intelligence.symbol_indexer import SymbolIndexer
from ai.intelligence.reference_index import ReferenceIndex
from ai.intelligence.impact_analyzer import ImpactAnalyzer
from ai.intelligence.project_health import ProjectHealth
from ai.intelligence.language_statistics import LanguageStatistics
from ai.intelligence.entry_point_detector import EntryPointDetector
from ai.intelligence.documentation_indexer import DocumentationIndexer

# Result types
from ai.intelligence.dependency_graph import DependencyNode
from ai.intelligence.symbol_indexer import SymbolEntry
from ai.intelligence.impact_analyzer import ImpactReport
from ai.intelligence.project_health import HealthScore, HealthRecommendation
from ai.intelligence.entry_point_detector import EntryPoint
from ai.intelligence.documentation_indexer import DocumentationEntry

logger = setup_logger(__name__)


class ProjectIntelligence:
    """
    Complete understanding of a project's structure, architecture, and health.
    
    This object is populated by ProjectAnalyzer and becomes the source
    of truth for all AI operations. It includes:
    - Architecture and design patterns
    - Dependency relationships
    - Symbol locations and references
    - Entry points and main modules
    - Health score and recommendations
    - Language statistics
    - Documentation coverage
    """
    
    def __init__(
        self,
        project_path: Path,
        architecture: Optional[str] = None,
        architecture_confidence: float = 0.0,
        dependency_graph: Optional[DependencyGraph] = None,
        symbols: List[SymbolEntry] = None,
        references: Dict[str, List[str]] = None,
        entry_points: List[EntryPoint] = None,
        health: Optional[HealthScore] = None,
        language_stats: Optional[LanguageStatistics] = None,
        documentation: List[DocumentationEntry] = None,
        impact_cache: Dict[str, ImpactReport] = None,
        scan_duration_ms: float = 0.0,
        last_scan_time: Optional[float] = None,
    ):
        self.project_path = project_path
        self.architecture = architecture
        self.architecture_confidence = architecture_confidence
        self.dependency_graph = dependency_graph or DependencyGraph()
        self.symbols = symbols or []
        self.references = references or {}
        self.entry_points = entry_points or []
        self.health = health
        self.language_stats = language_stats
        self.documentation = documentation or []
        self.impact_cache = impact_cache or {}
        self.scan_duration_ms = scan_duration_ms
        self.last_scan_time = last_scan_time or time.time()
        
    def get_summary(self) -> Dict[str, Any]:
        """Return a human-readable summary of project intelligence."""
        return {
            "project": str(self.project_path),
            "architecture": {
                "type": self.architecture,
                "confidence": f"{self.architecture_confidence:.0%}",
            },
            "dependency_graph": {
                "node_count": len(self.dependency_graph.nodes),
                "edge_count": len(self.dependency_graph.edges),
            },
            "symbols": len(self.symbols),
            "entry_points": [ep.path for ep in self.entry_points],
            "health": {
                "score": self.health.score if self.health else None,
                "status": self.health.status if self.health else None,
                "recommendations": [
                    rec.to_dict() for rec in (self.health.recommendations if self.health else [])
                ],
            },
            "language_stats": self.language_stats.to_dict() if self.language_stats else None,
            "documentation": {
                "indexed_files": len(self.documentation),
                "coverage": f"{len(self.documentation):,} entries",
            },
            "impact_cache_size": len(self.impact_cache),
            "scan_duration_ms": self.scan_duration_ms,
        }


class ProjectAnalyzer:
    """
    Orchestrates all sub-analyzers to build complete project intelligence.
    
    This is the main entry point for the Project Intelligence Engine.
    When a workspace is opened, this analyzer runs all sub-analyzers
    asynchronously and publishes results to the EventBus.
    
    Events published:
    - `project_intelligence_scan_started`: Scan beginning
    - `project_intelligence_scan_progress`: Progress updates
    - `project_intelligence_scan_completed`: Scan completed with results
    - `project_intelligence_scan_failed`: Scan failed with error
    
    Usage:
        analyzer = ProjectAnalyzer(event_bus)
        analyzer.analyze("/path/to/project")
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self._current_task: Optional[str] = None
        self._canceled = False
        
    def analyze(self, project_path: str | Path, callback: Callable[[ProjectIntelligence], None] = None):
        """
        Analyze a project and return comprehensive intelligence.
        
        This method runs asynchronously and publishes progress events.
        The final ProjectIntelligence object is passed to the callback
        if provided, or can be retrieved from the last scan completed event.
        
        Args:
            project_path: Path to the project to analyze
            callback: Optional callback to receive the results
        """
        project_path = Path(project_path).resolve()
        logger.info(f"Starting project analysis: {project_path}")
        
        # Publish scan started
        self.event_bus.publish("project_intelligence_scan_started", {
            "project_path": str(project_path),
        })
        
        # Start analysis in background thread
        thread = threading.Thread(
            target=self._analyze_async,
            args=(project_path, callback),
            daemon=True
        )
        thread.start()
        
    def _analyze_async(self, project_path: Path, callback: Callable[[ProjectIntelligence], None] = None):
        """Run analysis in background thread."""
        start_time = time.perf_counter()
        self._canceled = False
        
        try:
            # Initialize intelligence object
            intelligence = ProjectIntelligence(project_path=project_path)
            
            # Step 1: Architecture detection
            self._current_task = "Detecting architecture..."
            self.event_bus.publish("project_intelligence_scan_progress", {
                "task": self._current_task,
                "progress": 10,
            })
            
            arch_detector = ArchitectureDetector()
            arch_result = arch_detector.detect(project_path)
            if arch_result:
                intelligence.architecture = arch_result.architecture
                intelligence.architecture_confidence = arch_result.confidence
            
            # Step 2: Language statistics
            self._current_task = "Analyzing language statistics..."
            self.event_bus.publish("project_intelligence_scan_progress", {
                "task": self._current_task,
                "progress": 20,
            })
            
            lang_stats = LanguageStatistics(project_path)
            intelligence.language_stats = lang_stats
            
            # Step 3: Entry point detection
            self._current_task = "Detecting entry points..."
            self.event_bus.publish("project_intelligence_scan_progress", {
                "task": self._current_task,
                "progress": 30,
            })
            
            entry_detector = EntryPointDetector(project_path)
            intelligence.entry_points = entry_detector.detect()
            
            # Step 4: Dependency graph
            self._current_task = "Building dependency graph..."
            self.event_bus.publish("project_intelligence_scan_progress", {
                "task": self._current_task,
                "progress": 45,
            })
            
            dep_graph = DependencyGraph()
            dep_graph.build(project_path)
            intelligence.dependency_graph = dep_graph
            
            # Step 5: Symbol indexing
            self._current_task = "Indexing symbols..."
            self.event_bus.publish("project_intelligence_scan_progress", {
                "task": self._current_task,
                "progress": 60,
            })
            
            symbol_indexer = SymbolIndexer()
            intelligence.symbols = symbol_indexer.index_project(str(project_path))
            
            # Step 6: Reference index
            self._current_task = "Building reference index..."
            self.event_bus.publish("project_intelligence_scan_progress", {
                "task": self._current_task,
                "progress": 70,
            })
            
            ref_index = ReferenceIndex()
            intelligence.references = ref_index.build_index(str(project_path), intelligence.symbols)
            
            # Step 7: Documentation indexing
            self._current_task = "Indexing documentation..."
            self.event_bus.publish("project_intelligence_scan_progress", {
                "task": self._current_task,
                "progress": 80,
            })
            
            doc_indexer = DocumentationIndexer(project_path)
            intelligence.documentation = doc_indexer.index()
            
            # Step 8: Project health
            self._current_task = "Calculating project health..."
            self.event_bus.publish("project_intelligence_scan_progress", {
                "task": self._current_task,
                "progress": 90,
            })
            
            health = ProjectHealth(
                project_path=project_path,
                symbols=intelligence.symbols,
                dependency_graph=intelligence.dependency_graph,
                documentation=intelligence.documentation,
            )
            intelligence.health = health.calculate()
            
            # Calculate total duration
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            intelligence.scan_duration_ms = elapsed_ms
            intelligence.last_scan_time = time.time()
            
            # Publish completion
            logger.info(f"Project analysis completed in {elapsed_ms:.0f}ms")
            self.event_bus.publish("project_intelligence_scan_completed", {
                "project_path": str(project_path),
                "intelligence": intelligence,
                "duration_ms": elapsed_ms,
            })
            
            # Call callback if provided
            if callback:
                callback(intelligence)
                
        except Exception as e:
            logger.error(f"Project analysis failed: {e}", exc_info=True)
            self.event_bus.publish("project_intelligence_scan_failed", {
                "project_path": str(project_path),
                "error": str(e),
            })
    
    def get_intelligence(self, project_path: str | Path) -> Optional[ProjectIntelligence]:
        """
        Get cached intelligence for a project if available.
        
        This method checks if intelligence has been previously calculated
        for this project and returns it. Otherwise, returns None.
        
        Note: Currently this analyzer doesn't cache results. In the future,
        it could store intelligence in a file or database for persistence.
        
        Args:
            project_path: Path to the project
            
        Returns:
            ProjectIntelligence if previously analyzed, None otherwise
        """
        # TODO: Implement caching by reading from disk
        return None
    
    def cancel(self):
        """Cancel the current analysis if running."""
        self._canceled = True
        logger.info("Project analysis cancelled")