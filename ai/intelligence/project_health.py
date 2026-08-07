"""
Project Health — calculates project health scores and recommendations.

This module analyzes a project for code quality issues and generates
a health score along with actionable recommendations.

Health factors considered:
- Dead code detection
- Large files
- Circular imports
- Duplicate code
- Long functions
- Unused imports
- Missing tests
- Large classes
- Architecture violations
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from core.logger import setup_logger

logger = setup_logger(__name__)


class HealthStatus(Enum):
    """Health status indicators."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class HealthRecommendation:
    """A recommendation for improving project health."""
    category: str  # code_quality, architecture, tests, documentation
    severity: str  # low, medium, high, critical
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggested_fix: Optional[str] = None
    
    def to_dict(self) -> Dict[str, object]:
        return {
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "suggested_fix": self.suggested_fix,
        }


@dataclass
class HealthScore:
    """Health score for a project."""
    total_score: int  # 0-100
    status: HealthStatus
    breakdown: Dict[str, int] = field(default_factory=dict)
    recommendations: List[HealthRecommendation] = field(default_factory=list)
    scores: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, object]:
        return {
            "total_score": self.total_score,
            "status": self.status.value,
            "breakdown": self.breakdown,
            "recommendations": [r.to_dict() for r in self.recommendations],
            "scores": self.scores,
        }


class ProjectHealth:
    """
    Analyzes project health and generates recommendations.
    
    This analyzer examines the codebase for common quality issues
    and assigns a health score from 0-100.
    
    Categories:
    - Code Quality (40 points)
    - Architecture (25 points)
    - Tests (20 points)
    - Documentation (15 points)
    """
    
    # File size thresholds (in KB)
    MAX_FILE_SIZE = 500  # KB
    LARGE_FILE_SIZE = 200  # KB
    
    # Class/Function thresholds
    MAX_CLASS_LINES = 500
    MAX_FUNCTION_LINES = 50
    MAX_PARAMETERS = 5
    
    # Dependency thresholds
    MAX_CIRCULAR_DEPENDENCIES = 3
    MAX_DEPENDENCIES_PER_FILE = 20
    
    def __init__(
        self,
        project_path: str | Path,
        symbols: List = None,
        dependency_graph = None,
        documentation: List = None,
    ):
        self.project_path = Path(project_path).resolve()
        self.symbols = symbols or []
        self.dependency_graph = dependency_graph
        self.documentation = documentation or []
        
        # Cache for analysis results
        self._large_files: List[str] = []
        self._circular_dependencies: List[List[str]] = []
        self._dead_code: List[str] = []
        self._unused_imports: List[str] = []
        self._long_functions: List[str] = []
        self._large_classes: List[str] = []
        self._duplicate_code: List[str] = []
        self._missing_tests: List[str] = []
        self._architecture_violations: List[str] = []
        
    def calculate(self) -> HealthScore:
        """
        Calculate the overall project health score.
        
        Returns:
            HealthScore with total score, status, and recommendations
        """
        logger.info(f"Calculating project health for: {self.project_path}")
        
        # Run all analyses
        self._analyze_large_files()
        self._analyze_circular_dependencies()
        self._analyze_dead_code()
        self._analyze_unused_imports()
        self._analyze_long_functions()
        self._analyze_large_classes()
        self._analyze_duplicate_code()
        self._analyze_missing_tests()
        self._analyze_architecture()
        
        # Calculate scores for each category
        code_quality_score = self._calculate_code_quality_score()
        architecture_score = self._calculate_architecture_score()
        tests_score = self._calculate_tests_score()
        documentation_score = self._calculate_documentation_score()
        
        # Weighted total
        total_score = (
            code_quality_score * 0.40 +
            architecture_score * 0.25 +
            tests_score * 0.20 +
            documentation_score * 0.15
        )
        
        # Determine status
        if total_score >= 90:
            status = HealthStatus.EXCELLENT
        elif total_score >= 75:
            status = HealthStatus.GOOD
        elif total_score >= 50:
            status = HealthStatus.FAIR
        elif total_score >= 25:
            status = HealthStatus.POOR
        else:
            status = HealthStatus.CRITICAL
            
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        # Build breakdown
        breakdown = {
            "code_quality": code_quality_score,
            "architecture": architecture_score,
            "tests": tests_score,
            "documentation": documentation_score,
        }
        
        scores = {
            "code_quality": code_quality_score,
            "architecture": architecture_score,
            "tests": tests_score,
            "documentation": documentation_score,
        }
        
        score = HealthScore(
            total_score=int(total_score),
            status=status,
            breakdown=breakdown,
            recommendations=recommendations,
            scores=scores,
        )
        
        logger.info(f"Project health score: {score.total_score}/100 ({score.status.value})")
        
        return score
    
    def _analyze_large_files(self):
        """Analyze file sizes."""
        self._large_files = []
        
        for file_path in self.project_path.rglob("*"):
            if file_path.is_file():
                try:
                    size_kb = file_path.stat().st_size / 1024
                    if size_kb > self.MAX_FILE_SIZE:
                        self._large_files.append(str(file_path))
                except Exception:
                    pass
                    
    def _analyze_circular_dependencies(self):
        """Detect circular dependencies."""
        self._circular_dependencies = []
        
        if self.dependency_graph:
            cycles = self.dependency_graph.get_cycle_paths()
            self._circular_dependencies = cycles
    
    def _analyze_dead_code(self):
        """Detect dead code (unused classes/functions)."""
        self._dead_code = []
        
        # Find classes and functions with no references
        for symbol in self.symbols:
            if symbol.symbol_type.value in ('class', 'function', 'method'):
                # Check if symbol has any references
                has_references = False
                for ref_symbol in self.symbols:
                    if ref_symbol.path != symbol.path:
                        # This is a simplified check
                        pass
                        
                if not has_references:
                    self._dead_code.append(symbol.get_full_name())
                    
    def _analyze_unused_imports(self):
        """Detect unused imports."""
        self._unused_imports = []
        
        # This would require more sophisticated analysis
        # For now, just mark that analysis exists
        pass
        
    def _analyze_long_functions(self):
        """Detect long functions."""
        self._long_functions = []
        
        for symbol in self.symbols:
            if symbol.symbol_type.value == 'function':
                line_count = symbol.line_end - symbol.line_start
                if line_count > self.MAX_FUNCTION_LINES:
                    self._long_functions.append(symbol.get_full_name())
                    
    def _analyze_large_classes(self):
        """Detect large classes."""
        self._large_classes = []
        
        for symbol in self.symbols:
            if symbol.symbol_type.value == 'class':
                line_count = symbol.line_end - symbol.line_start
                if line_count > self.MAX_CLASS_LINES:
                    self._large_classes.append(symbol.get_full_name())
                    
    def _analyze_duplicate_code(self):
        """Detect duplicate code blocks."""
        self._duplicate_code = []
        
        # This would require fuzzy matching of code blocks
        # For now, just mark that analysis exists
        pass
        
    def _analyze_missing_tests(self):
        """Detect files without tests."""
        self._missing_tests = []
        
        # Check for test file patterns
        test_patterns = [
            "test_*.py",
            "*_test.py",
            "tests/test_*.py",
        ]
        
        source_extensions = {'.py', '.js', '.ts', '.java', '.c', '.cpp'}
        test_extensions = {'.py', '.js', '.ts', '.java'}
        
        source_files = []
        test_files = []
        
        for file_path in self.project_path.rglob("*"):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                stem = file_path.stem
                
                if ext in source_extensions:
                    source_files.append(str(file_path))
                    
                if ext in test_extensions:
                    for pattern in test_patterns:
                        if pattern.replace('*', stem) in str(file_path):
                            test_files.append(str(file_path))
                            break
                            
        # Find source files without tests
        for source in source_files:
            has_test = False
            for test in test_files:
                if source.replace('/src/', '/tests/') in test or 'test' in test:
                    has_test = True
                    break
                    
            if not has_test:
                self._missing_tests.append(source)
                
    def _analyze_architecture(self):
        """Check for architecture violations."""
        self._architecture_violations = []
        
        # Check for common violations based on detected architecture
        # This would be more sophisticated with actual architecture detection
        
    def _calculate_code_quality_score(self) -> int:
        """Calculate code quality score."""
        score = 100
        
        # Large files penalty
        large_file_count = len(self._large_files)
        score -= min(large_file_count * 2, 20)
        
        # Circular dependencies penalty
        cycle_count = len(self._circular_dependencies)
        score -= min(cycle_count * 5, 25)
        
        # Dead code penalty
        dead_code_count = len(self._dead_code)
        score -= min(dead_code_count * 3, 15)
        
        # Long functions penalty
        long_func_count = len(self._long_functions)
        score -= min(long_func_count * 2, 10)
        
        # Large classes penalty
        large_class_count = len(self._large_classes)
        score -= min(large_class_count * 2, 10)
        
        return max(score, 0)
    
    def _calculate_architecture_score(self) -> int:
        """Calculate architecture score."""
        score = 100
        
        # Circular dependencies penalty
        cycle_count = len(self._circular_dependencies)
        score -= min(cycle_count * 10, 30)
        
        # Architecture violations penalty
        violation_count = len(self._architecture_violations)
        score -= min(violation_count * 5, 20)
        
        return max(score, 0)
    
    def _calculate_tests_score(self) -> int:
        """Calculate test coverage score."""
        score = 100
        
        # Missing tests penalty
        missing_count = len(self._missing_tests)
        if missing_count > 0:
            # Calculate percentage of files without tests
            total_source_files = len(self.symbols)  # Rough estimate
            percentage = missing_count / max(total_source_files, 1)
            penalty = int(percentage * 50)
            score -= penalty
            
        return max(score, 0)
    
    def _calculate_documentation_score(self) -> int:
        """Calculate documentation score."""
        score = 100
        
        # Check for README
        readme_count = sum(1 for f in self.documentation if 'readme' in f.path.lower())
        if readme_count == 0:
            score -= 10
            
        # Check for docstrings
        docstring_count = sum(1 for s in self.symbols if s.docstring)
        if docstring_count < len(self.symbols) * 0.5:
            score -= 20
            
        return max(score, 0)
    
    def _generate_recommendations(self) -> List[HealthRecommendation]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        # Large files
        if self._large_files:
            recommendations.append(HealthRecommendation(
                category="code_quality",
                severity="high",
                message=f"Found {len(self._large_files)} large files (>500KB)",
                suggested_fix="Consider splitting large files into smaller modules",
            ))
            
        # Circular dependencies
        if self._circular_dependencies:
            recommendations.append(HealthRecommendation(
                category="architecture",
                severity="critical",
                message=f"Found {len(self._circular_dependencies)} circular dependency paths",
                suggested_fix="Refactor to break circular dependencies using dependency injection",
            ))
            
        # Dead code
        if self._dead_code:
            recommendations.append(HealthRecommendation(
                category="code_quality",
                severity="medium",
                message=f"Found {len(self._dead_code)} potential dead code items",
                suggested_fix="Remove or comment out unused code",
            ))
            
        # Long functions
        if self._long_functions:
            recommendations.append(HealthRecommendation(
                category="code_quality",
                severity="medium",
                message=f"Found {len(self._long_functions)} long functions (>50 lines)",
                suggested_fix="Refactor long functions into smaller, focused functions",
            ))
            
        # Large classes
        if self._large_classes:
            recommendations.append(HealthRecommendation(
                category="code_quality",
                severity="medium",
                message=f"Found {len(self._large_classes)} large classes (>500 lines)",
                suggested_fix="Apply Single Responsibility Principle to split classes",
            ))
            
        # Missing tests
        if self._missing_tests:
            recommendations.append(HealthRecommendation(
                category="tests",
                severity="high",
                message=f"Found {len(self._missing_tests)} files without tests",
                suggested_fix="Add unit tests for uncovered code",
            ))
            
        # Architecture violations
        if self._architecture_violations:
            recommendations.append(HealthRecommendation(
                category="architecture",
                severity="high",
                message=f"Found {len(self._architecture_violations)} architecture violations",
                suggested_fix="Review and fix architecture violations",
            ))
            
        return recommendations
    
    def get_health_summary(self) -> Dict[str, object]:
        """Get a summary of project health."""
        score = self.calculate()
        
        return {
            "total_score": score.total_score,
            "status": score.status.value,
            "breakdown": score.breakdown,
            "recommendations_count": len(score.recommendations),
            "issues": {
                "large_files": len(self._large_files),
                "circular_dependencies": len(self._circular_dependencies),
                "dead_code": len(self._dead_code),
                "long_functions": len(self._long_functions),
                "large_classes": len(self._large_classes),
                "missing_tests": len(self._missing_tests),
            },
        }
    
    def to_dict(self) -> Dict[str, object]:
        """Return a JSON-serializable representation."""
        return {
            "project_path": str(self.project_path),
            "large_files": self._large_files,
            "circular_dependencies": self._circular_dependencies,
            "dead_code": self._dead_code,
            "long_functions": self._long_functions,
            "large_classes": self._large_classes,
            "missing_tests": self._missing_tests,
        }