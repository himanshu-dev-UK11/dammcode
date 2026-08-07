"""
Architecture Detector — identifies project architecture patterns.

This analyzer examines the project structure, file organization,
and code patterns to determine the architectural design pattern
used by the project.

Return values:
- Clean Architecture
- MVC (Model-View-Controller)
- MVVM (Model-View-ViewModel)
- Feature First
- Layered (Three-tier)
- Hexagonal (Ports and Adapters)
- Event-Driven
- Microservices
- Unknown
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional

from core.logger import setup_logger

logger = setup_logger(__name__)


class ArchitectureResult:
    """Result from architecture detection."""
    
    def __init__(self, architecture: str, confidence: float, evidence: List[str] = None):
        self.architecture = architecture
        self.confidence = confidence
        self.evidence = evidence or []
        
    def to_dict(self) -> Dict[str, object]:
        return {
            "architecture": self.architecture,
            "confidence": self.confidence,
            "evidence": self.evidence,
        }


class ArchitectureDetector:
    """
    Detects the architectural pattern of a project.
    
    This analyzer examines:
    - Folder structure and organization
    - File naming conventions
    - Import patterns
    - Configuration files
    - Framework-specific patterns
    
    Return a confidence score between 0.0 and 1.0.
    """
    
    def __init__(self):
        self._detection_rules = self._build_detection_rules()
        
    def _build_detection_rules(self) -> List[Dict]:
        """Build detection rules for different architectures."""
        return [
            {
                "name": "Clean Architecture",
                "folders": ["domain", "application", "infrastructure", "presentation"],
                "patterns": ["core/", "src/core/", "app/core/"],
                "confidence_weights": {"folders": 0.5, "patterns": 0.5},
            },
            {
                "name": "MVC",
                "folders": ["models", "views", "controllers", "controller"],
                "patterns": ["Controller.cs", "Controller.php", "controller.py"],
                "confidence_weights": {"folders": 0.4, "patterns": 0.6},
            },
            {
                "name": "MVVM",
                "folders": ["models", "views", "viewmodels", "view-models"],
                "patterns": ["ViewModel.cs", "ViewModel.ts", "view-model.ts"],
                "confidence_weights": {"folders": 0.4, "patterns": 0.6},
            },
            {
                "name": "Feature First",
                "folders": ["features", "modules", "features/"],
                "patterns": ["feature/", "module/"],
                "confidence_weights": {"folders": 0.6, "patterns": 0.4},
            },
            {
                "name": "Layered",
                "folders": ["layers", "layers/", "tier", "tier/"],
                "patterns": ["layer", "tier"],
                "confidence_weights": {"folders": 0.5, "patterns": 0.5},
            },
            {
                "name": "Hexagonal",
                "folders": ["ports", "adapters", "ports/", "adapters/"],
                "patterns": ["port", "adapter"],
                "confidence_weights": {"folders": 0.5, "patterns": 0.5},
            },
            {
                "name": "Event-Driven",
                "folders": ["events", "handlers", "events/", "handlers/"],
                "patterns": ["Event", "EventHandler", "EventListener"],
                "confidence_weights": {"folders": 0.4, "patterns": 0.6},
            },
            {
                "name": "Microservices",
                "folders": ["services", "microservices", "services/", "microservices/"],
                "patterns": ["service", "microservice"],
                "confidence_weights": {"folders": 0.5, "patterns": 0.5},
            },
        ]
        
    def detect(self, project_path: str | Path) -> Optional[ArchitectureResult]:
        """
        Detect the architecture pattern of a project.
        
        Args:
            project_path: Path to the project root
            
        Returns:
            ArchitectureResult with architecture name, confidence, and evidence
        """
        project_path = Path(project_path).resolve()
        
        if not project_path.exists():
            logger.error(f"Project path does not exist: {project_path}")
            return None
            
        logger.info(f"Detecting architecture for: {project_path}")
        
        # Collect evidence
        evidence = []
        scores = {}
        
        # Check folder structure
        folders = self._get_directories(project_path)
        
        # Check for config files that indicate frameworks
        config_files = self._find_config_files(project_path)
        
        # Check for architecture-specific patterns in code
        code_patterns = self._analyze_code_patterns(project_path)
        
        # Score each architecture
        for rule in self._detection_rules:
            rule_name = rule["name"]
            folder_score = self._score_folders(rule["folders"], folders)
            pattern_score = self._score_patterns(rule["patterns"], code_patterns)
            
            # Calculate weighted score
            weights = rule["confidence_weights"]
            total_score = (folder_score * weights["folders"] + 
                          pattern_score * weights["patterns"])
            
            scores[rule_name] = total_score
            
            if total_score > 0.3:
                rule_evidence = []
                if folder_score > 0:
                    rule_evidence.append(f"Found {folder_score:.0%} of expected folders")
                if pattern_score > 0:
                    rule_evidence.append(f"Found {pattern_score:.0%} of expected patterns")
                scores[rule_name] = max(scores[rule_name], 0.3)
                
        # Find best match
        if not scores:
            return ArchitectureResult("Unknown", 0.0, ["No patterns detected"])
            
        best_architecture = max(scores.keys(), key=lambda x: scores[x])
        best_score = scores[best_architecture]
        
        # Build evidence list
        for rule in self._detection_rules:
            if rule["name"] == best_architecture:
                evidence = rule.get("evidence", [])
                break
                
        if best_score < 0.4:
            evidence.append("Low confidence - architecture may be Unknown")
            
        logger.info(f"Detected architecture: {best_architecture} (confidence: {best_score:.0%})")
        
        return ArchitectureResult(best_architecture, best_score, evidence)
    
    def _get_directories(self, project_path: Path) -> List[str]:
        """Get list of directory names at project root."""
        directories = []
        try:
            for item in project_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    directories.append(item.name.lower())
        except Exception as e:
            logger.error(f"Failed to read directories: {e}")
        return directories
    
    def _find_config_files(self, project_path: Path) -> List[str]:
        """Find framework config files."""
        config_patterns = {
            "django": ["settings.py", "manage.py"],
            "flask": ["app.py", "wsgi.py"],
            "fastapi": ["main.py", "app.py"],
            "spring": ["pom.xml", "build.gradle"],
            "django": ["models.py", "views.py"],
            "laravel": ["routes/web.php", "app/Http/Controllers"],
            "rails": ["Gemfile", "app/controllers"],
            "nextjs": ["next.config.js", "pages/"],
            "react": ["package.json", "src/"],
            "angular": ["angular.json", "src/app/"],
            "vue": ["vue.config.js", "src/"],
            "node": ["package.json", "server.js"],
        }
        
        found_configs = []
        for framework, patterns in config_patterns.items():
            for pattern in patterns:
                if (project_path / pattern).exists() or any(
                    (project_path / p).exists() for p in [pattern] if '/' not in pattern
                ):
                    found_configs.append(framework)
                    break
                    
        return found_configs
    
    def _analyze_code_patterns(self, project_path: Path) -> List[str]:
        """Analyze code files for architecture patterns."""
        patterns = []
        
        # Pattern files to check
        pattern_files = ["main.py", "app.py", "server.py", "App.java", "Main.cs"]
        
        for pattern_file in pattern_files:
            file_path = project_path / pattern_file
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    
                    # Check for controller patterns
                    if re.search(r'class.*[Cc]ontroller', content):
                        patterns.append("controller")
                        
                    # Check for viewmodel patterns
                    if re.search(r'class.*[Vv]iew[Mm]odel', content):
                        patterns.append("viewmodel")
                        
                    # Check for event patterns
                    if re.search(r'class.*[Ee]vent', content):
                        patterns.append("event")
                        
                    # Check for domain patterns
                    if re.search(r'class.*[Dd]omain', content):
                        patterns.append("domain")
                        
                    # Check for port/adapter patterns
                    if re.search(r'(port|adapter)', content, re.IGNORECASE):
                        patterns.append("hexagonal")
                        
                except Exception as e:
                    logger.debug(f"Could not read {pattern_file}: {e}")
                    
        return patterns
    
    def _score_folders(self, expected_folders: List[str], actual_folders: List[str]) -> float:
        """Score how well expected folders match actual folders."""
        if not expected_folders or not actual_folders:
            return 0.0
            
        matches = sum(1 for folder in expected_folders 
                     if any(folder in actual for actual in actual_folders))
        
        return matches / len(expected_folders)
    
    def _score_patterns(self, expected_patterns: List[str], actual_patterns: List[str]) -> float:
        """Score how well expected patterns match actual patterns."""
        if not expected_patterns or not actual_patterns:
            return 0.0
            
        matches = sum(1 for pattern in expected_patterns 
                     if any(pattern in actual for actual in actual_patterns))
        
        return matches / len(expected_patterns)