"""
Impact Analyzer — calculates the impact of file changes.

This module analyzes how changes to a file will affect other files
in the project. It considers:
- Direct dependencies
- Import relationships
- Business logic dependencies
- Test dependencies

The impact analysis is used for:
- Risk assessment before changes
- Determining test scope
- Predicting merge conflicts
- Optimizing CI/CD pipelines
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field

from core.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ImpactReport:
    """Report of the impact of changing a file."""
    file_path: str
    affected_files: List[str] = field(default_factory=list)
    affected_classes: List[str] = field(default_factory=list)
    affected_functions: List[str] = field(default_factory=list)
    risk_level: str = "low"  # low, medium, high, critical
    dependency_count: int = 0
    build_impact: List[str] = field(default_factory=list)
    test_impact: List[str] = field(default_factory=list)
    estimated_complexity: str = "simple"  # simple, moderate, complex, major
    
    def to_dict(self) -> Dict[str, object]:
        return {
            "file_path": self.file_path,
            "affected_files": self.affected_files,
            "affected_classes": self.affected_classes,
            "affected_functions": self.affected_functions,
            "risk_level": self.risk_level,
            "dependency_count": self.dependency_count,
            "build_impact": self.build_impact,
            "test_impact": self.test_impact,
            "estimated_complexity": self.estimated_complexity,
        }


class ImpactAnalyzer:
    """
    Analyzes the impact of file changes in a project.
    
    This analyzer considers:
    - Direct file dependencies (imports)
    - Reverse dependencies (who imports this file)
    - Class and function dependencies
    - Test file relationships
    - Build system dependencies
    
    The analysis is cached to avoid recomputing for the same file.
    """
    
    def __init__(self):
        self._cache: Dict[str, ImpactReport] = {}
        self._dependency_graph = None
        self._symbol_index = None
        
    def set_dependency_graph(self, graph):
        """Set the dependency graph for analysis."""
        self._dependency_graph = graph
        
    def set_symbol_index(self, index):
        """Set the symbol index for analysis."""
        self._symbol_index = index
        
    def analyze(self, file_path: str | Path, project_path: str | Path = None) -> ImpactReport:
        """
        Analyze the impact of changing a file.
        
        Args:
            file_path: Path to the file to analyze
            project_path: Optional project root (uses file_path's root if not provided)
            
        Returns:
            ImpactReport with all impact information
        """
        file_path = Path(file_path).resolve()
        
        if project_path:
            project_path = Path(project_path).resolve()
        else:
            project_path = file_path.parent
            
        # Check cache first
        cache_key = str(file_path)
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        logger.info(f"Analyzing impact for: {file_path}")
        start_time = time.perf_counter()
        
        # Build impact report
        report = ImpactReport(file_path=str(file_path))
        
        # 1. Find files that import this file
        if self._dependency_graph:
            dependents = self._dependency_graph.get_dependents(str(file_path.relative_to(project_path)))
            report.affected_files.extend(dependents)
            
            # 2. Find files this file depends on
            dependencies = self._dependency_graph.get_dependencies(str(file_path.relative_to(project_path)))
            report.dependency_count = len(dependencies)
            
        # 3. Find classes and functions defined in this file
        if self._symbol_index:
            symbols = self._symbol_index.get_symbols_in_file(str(file_path))
            for symbol in symbols:
                if symbol.symbol_type.value in ('class', 'function', 'method'):
                    if symbol.name not in report.affected_classes:
                        report.affected_classes.append(symbol.name)
                        
        # 4. Find test files for this file
        test_files = self._find_test_files(file_path, project_path)
        report.test_impact.extend(test_files)
        
        # 5. Check build system dependencies
        build_impact = self._analyze_build_impact(file_path, project_path)
        report.build_impact.extend(build_impact)
        
        # 6. Calculate risk level
        report.risk_level = self._calculate_risk_level(report)
        
        # 7. Estimate complexity
        report.estimated_complexity = self._estimate_complexity(report)
        
        # Cache the result
        self._cache[cache_key] = report
        
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(f"Impact analysis completed in {elapsed_ms:.0f}ms")
        
        return report
    
    def _find_test_files(self, file_path: Path, project_path: Path) -> List[str]:
        """Find test files related to a file."""
        test_patterns = [
            "test_*.py",
            "*_test.py",
            "tests/test_*.py",
            "tests/*_test.py",
            "spec_*.py",
            "*_spec.py",
        ]
        
        # Get the base name of the file
        stem = file_path.stem
        
        test_files = []
        for pattern in test_patterns:
            for test_file in project_path.rglob(pattern):
                # Check if the test file relates to our file
                if stem in test_file.name or test_file.name in stem:
                    test_files.append(str(test_file))
                    
        return test_files
    
    def _analyze_build_impact(self, file_path: Path, project_path: Path) -> List[str]:
        """Analyze build system dependencies."""
        impact = []
        
        # Check for common build/config files
        config_files = [
            "Makefile",
            "CMakeLists.txt",
            "build.gradle",
            "pom.xml",
            "package.json",
            "requirements.txt",
            "pyproject.toml",
            "Cargo.toml",
            "go.mod",
        ]
        
        for config in config_files:
            config_path = project_path / config
            if config_path.exists():
                # Check if the config references our file
                try:
                    content = config_path.read_text(encoding='utf-8', errors='ignore')
                    if str(file_path.relative_to(project_path)) in content:
                        impact.append(config)
                except Exception:
                    pass
                    
        return impact
    
    def _calculate_risk_level(self, report: ImpactReport) -> str:
        """Calculate the risk level of changing a file."""
        # Count factors that increase risk
        risk_factors = 0
        max_factors = 10
        
        # More affected files = higher risk
        if len(report.affected_files) > 50:
            risk_factors += 3
        elif len(report.affected_files) > 10:
            risk_factors += 2
        elif len(report.affected_files) > 3:
            risk_factors += 1
            
        # More dependencies = higher risk
        if report.dependency_count > 20:
            risk_factors += 2
        elif report.dependency_count > 10:
            risk_factors += 1
            
        # More test files = higher risk
        if len(report.test_impact) > 10:
            risk_factors += 2
            
        # More affected classes/functions = higher risk
        if len(report.affected_classes) > 10:
            risk_factors += 2
        elif len(report.affected_classes) > 3:
            risk_factors += 1
            
        # If file is in build system
        if report.build_impact:
            risk_factors += 1
            
        # Calculate risk level
        if risk_factors >= 7:
            return "critical"
        elif risk_factors >= 5:
            return "high"
        elif risk_factors >= 3:
            return "medium"
        else:
            return "low"
    
    def _estimate_complexity(self, report: ImpactReport) -> str:
        """Estimate the complexity of the change."""
        complexity_factors = 0
        
        # More affected files = more complex
        if len(report.affected_files) > 100:
            complexity_factors += 3
        elif len(report.affected_files) > 50:
            complexity_factors += 2
        elif len(report.affected_files) > 10:
            complexity_factors += 1
            
        # More affected functions/classes = more complex
        if len(report.affected_classes) > 20:
            complexity_factors += 2
        elif len(report.affected_classes) > 10:
            complexity_factors += 1
            
        # If test files are affected = more complex
        if report.test_impact:
            complexity_factors += 1
            
        if complexity_factors >= 5:
            return "major"
        elif complexity_factors >= 3:
            return "complex"
        elif complexity_factors >= 2:
            return "moderate"
        else:
            return "simple"
    
    def analyze_batch(self, file_paths: List[str | Path], project_path: str | Path) -> Dict[str, ImpactReport]:
        """
        Analyze multiple files at once.
        
        Args:
            file_paths: List of file paths to analyze
            project_path: Project root path
            
        Returns:
            Dictionary mapping file paths to impact reports
        """
        results = {}
        for file_path in file_paths:
            results[str(file_path)] = self.analyze(file_path, project_path)
        return results
    
    def get_high_impact_files(self, project_path: str | Path, threshold: str = "medium") -> List[str]:
        """
        Get all files with high or critical impact.
        
        Args:
            project_path: Project root path
            threshold: Minimum risk level ("low", "medium", "high", "critical")
            
        Returns:
            List of file paths with high impact
        """
        high_impact = []
        
        # Scan common source files
        patterns = ["*.py", "*.js", "*.ts", "*.java", "*.c", "*.cpp"]
        
        for pattern in patterns:
            for file_path in Path(project_path).rglob(pattern):
                report = self.analyze(file_path, project_path)
                
                if report.risk_level in ("high", "critical"):
                    high_impact.append(str(file_path))
                    
        return high_impact
    
    def clear_cache(self):
        """Clear the impact analysis cache."""
        self._cache = {}
        logger.info("Impact analysis cache cleared")
        
    def to_dict(self) -> Dict[str, object]:
        """Return a JSON-serializable representation of the analyzer state."""
        return {
            "cache_size": len(self._cache),
            "has_dependency_graph": self._dependency_graph is not None,
            "has_symbol_index": self._symbol_index is not None,
        }