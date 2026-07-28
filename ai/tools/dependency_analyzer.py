"""
DependencyAnalyzer — extract libraries, versions, and package manager info.

Reads standard dependency manifest files and parses them into structured
DependencyInfo objects. This gives the AI context engine a precise view
of which external libraries the project relies on, enabling smarter
code suggestions and conflict detection.

No files are modified. This module is read-only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from core.logger import setup_logger
from core.exceptions import MyCodingMasterError

logger = setup_logger(__name__)


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class DependencyAnalysisError(MyCodingMasterError):
    """Raised when a dependency file is malformed or cannot be parsed."""


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class Dependency:
    """
    A single library or package dependency.

    Attributes:
        name:            The package name (e.g. "django", "react").
        version:         The version constraint string (e.g. ">=4.0", "^18.0.0").
                         Empty string if no version is specified.
        is_dev:          True if this is a development-only dependency.
        source_file:     The manifest file this dependency was parsed from.
    """
    name:        str
    version:     str      = ""
    is_dev:      bool     = False
    source_file: str      = ""

    def __repr__(self) -> str:
        ver = f"@{self.version}" if self.version else ""
        return f"Dependency({self.name!r}{ver})"


@dataclass
class DependencyInfo:
    """
    Complete dependency picture for a project.

    Attributes:
        package_manager:    Detected package manager (e.g. "pip", "npm", "cargo").
        framework_version:  Version of the primary framework if detectable.
        dependencies:       List of all runtime dependencies.
        dev_dependencies:   List of development-only dependencies.
        source_files:       Manifest files that were read.
    """
    package_manager:    str
    framework_version:  str               = ""
    dependencies:       List[Dependency]  = field(default_factory=list)
    dev_dependencies:   List[Dependency]  = field(default_factory=list)
    source_files:       List[str]         = field(default_factory=list)

    @property
    def all_dependencies(self) -> List[Dependency]:
        """Combined list of runtime and dev dependencies."""
        return self.dependencies + self.dev_dependencies

    @property
    def dependency_names(self) -> List[str]:
        """Flat list of all dependency names."""
        return [d.name for d in self.all_dependencies]

    def __repr__(self) -> str:
        return (
            f"DependencyInfo(pm={self.package_manager!r}, "
            f"deps={len(self.dependencies)}, "
            f"dev_deps={len(self.dev_dependencies)})"
        )


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------

class DependencyAnalyzer:
    """
    Reads and parses project dependency manifests into DependencyInfo objects.

    Supports the following package managers / manifest formats:
      - pip       : requirements.txt
      - pip/pypa  : pyproject.toml (tool.poetry.dependencies or project.dependencies)
      - npm/yarn  : package.json
      - cargo     : Cargo.toml
      - maven     : pom.xml (partial — library name + version only)
      - gradle    : build.gradle (regex-based)
      - pubspec   : pubspec.yaml (Flutter/Dart)

    Usage:
        analyzer = DependencyAnalyzer("/path/to/project")
        info     = analyzer.analyze()
        print(info.package_manager, info.dependency_names)
    """

    def __init__(self, root_path: str | Path) -> None:
        self.root_path = Path(root_path).resolve()
        logger.info(f"DependencyAnalyzer initialized for: {self.root_path}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self) -> Optional[DependencyInfo]:
        """
        Detect the package manager and parse all available dependency files.

        Returns:
            DependencyInfo if at least one manifest was found, otherwise None.
        """
        logger.info("Analyzing project dependencies...")

        # Try each parser in priority order
        parsers = [
            ("requirements.txt",  self._parse_requirements_txt),
            ("pyproject.toml",    self._parse_pyproject_toml),
            ("package.json",      self._parse_package_json),
            ("Cargo.toml",        self._parse_cargo_toml),
            ("pom.xml",           self._parse_pom_xml),
            ("build.gradle",      self._parse_build_gradle),
            ("pubspec.yaml",      self._parse_pubspec_yaml),
        ]

        for filename, parser in parsers:
            path = self.root_path / filename
            if path.exists():
                try:
                    logger.info(f"Parsing dependency file: {filename}")
                    info = parser(path)
                    logger.info(
                        f"Found {len(info.dependencies)} runtime deps, "
                        f"{len(info.dev_dependencies)} dev deps via {filename}."
                    )
                    return info
                except Exception as exc:
                    logger.warning(f"Failed to parse {filename}: {exc}")

        logger.info("No dependency file found.")
        return None

    # ------------------------------------------------------------------
    # Parsers — one per manifest format
    # ------------------------------------------------------------------

    def _parse_requirements_txt(self, path: Path) -> DependencyInfo:
        """Parse a pip requirements.txt file."""
        deps: List[Dependency] = []
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()

        for raw in lines:
            line = raw.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            # e.g. django>=4.0,<5.0  or  requests==2.28.1
            match = re.match(r"^([A-Za-z0-9_.\-]+)\s*([><=!~^].+)?", line)
            if match:
                name    = match.group(1).lower()
                version = (match.group(2) or "").strip()
                deps.append(Dependency(name=name, version=version, source_file=str(path)))

        return DependencyInfo(
            package_manager="pip",
            dependencies=deps,
            source_files=[str(path)],
        )

    def _parse_pyproject_toml(self, path: Path) -> DependencyInfo:
        """Parse a pyproject.toml (PEP 517/518/621 or Poetry format)."""
        text = path.read_text(encoding="utf-8", errors="ignore")
        deps:     List[Dependency] = []
        dev_deps: List[Dependency] = []

        # PEP 621 project.dependencies
        pep621 = re.findall(r'dependencies\s*=\s*\[([^\]]+)\]', text, re.DOTALL)
        if pep621:
            for entry in re.findall(r'"([^"]+)"', pep621[0]):
                m = re.match(r"^([A-Za-z0-9_.\-]+)\s*([><=!~^].+)?", entry)
                if m:
                    deps.append(Dependency(name=m.group(1).lower(),
                                           version=(m.group(2) or "").strip(),
                                           source_file=str(path)))

        # Poetry [tool.poetry.dependencies]
        poetry_block = re.search(
            r'\[tool\.poetry\.dependencies\](.*?)(?=\[|$)', text, re.DOTALL
        )
        if poetry_block:
            for m in re.finditer(r'^([a-zA-Z][a-zA-Z0-9_\-]+)\s*=\s*"([^"]*)"',
                                  poetry_block.group(1), re.MULTILINE):
                if m.group(1).lower() != "python":
                    deps.append(Dependency(name=m.group(1).lower(),
                                           version=m.group(2),
                                           source_file=str(path)))

        # Poetry [tool.poetry.dev-dependencies]
        dev_block = re.search(
            r'\[tool\.poetry\.dev-dependencies\](.*?)(?=\[|$)', text, re.DOTALL
        )
        if dev_block:
            for m in re.finditer(r'^([a-zA-Z][a-zA-Z0-9_\-]+)\s*=\s*"([^"]*)"',
                                  dev_block.group(1), re.MULTILINE):
                dev_deps.append(Dependency(name=m.group(1).lower(),
                                           version=m.group(2),
                                           is_dev=True,
                                           source_file=str(path)))

        return DependencyInfo(
            package_manager="pip/poetry",
            dependencies=deps,
            dev_dependencies=dev_deps,
            source_files=[str(path)],
        )

    def _parse_package_json(self, path: Path) -> DependencyInfo:
        """Parse a Node.js package.json file using the standard json module."""
        import json
        data = json.loads(path.read_text(encoding="utf-8"))

        runtime_raw = data.get("dependencies", {})
        dev_raw     = data.get("devDependencies", {})

        deps     = [Dependency(name=k, version=v, source_file=str(path))
                    for k, v in runtime_raw.items()]
        dev_deps = [Dependency(name=k, version=v, is_dev=True, source_file=str(path))
                    for k, v in dev_raw.items()]

        # Detect yarn vs npm
        pm = "yarn" if (path.parent / "yarn.lock").exists() else "npm"

        return DependencyInfo(
            package_manager=pm,
            dependencies=deps,
            dev_dependencies=dev_deps,
            source_files=[str(path)],
        )

    def _parse_cargo_toml(self, path: Path) -> DependencyInfo:
        """Parse a Rust Cargo.toml file (TOML, parsed with regex)."""
        text = path.read_text(encoding="utf-8", errors="ignore")
        deps:     List[Dependency] = []
        dev_deps: List[Dependency] = []

        dep_block = re.search(r'\[dependencies\](.*?)(?=\[|$)', text, re.DOTALL)
        if dep_block:
            for m in re.finditer(r'^([a-z_\-]+)\s*=\s*"([^"]+)"',
                                  dep_block.group(1), re.MULTILINE):
                deps.append(Dependency(name=m.group(1), version=m.group(2),
                                       source_file=str(path)))

        dev_block = re.search(r'\[dev-dependencies\](.*?)(?=\[|$)', text, re.DOTALL)
        if dev_block:
            for m in re.finditer(r'^([a-z_\-]+)\s*=\s*"([^"]+)"',
                                  dev_block.group(1), re.MULTILINE):
                dev_deps.append(Dependency(name=m.group(1), version=m.group(2),
                                           is_dev=True, source_file=str(path)))

        return DependencyInfo(
            package_manager="cargo",
            dependencies=deps,
            dev_dependencies=dev_deps,
            source_files=[str(path)],
        )

    def _parse_pom_xml(self, path: Path) -> DependencyInfo:
        """Parse a Maven pom.xml file (regex-based, no external XML library)."""
        text = path.read_text(encoding="utf-8", errors="ignore")
        deps: List[Dependency] = []

        # Extract <dependency> blocks
        for block in re.finditer(r'<dependency>(.*?)</dependency>', text, re.DOTALL):
            content  = block.group(1)
            artifact = re.search(r'<artifactId>(.*?)</artifactId>', content)
            version  = re.search(r'<version>(.*?)</version>',      content)
            is_test  = bool(re.search(r'<scope>test</scope>',       content))
            if artifact:
                deps.append(Dependency(
                    name        = artifact.group(1).strip(),
                    version     = version.group(1).strip() if version else "",
                    is_dev      = is_test,
                    source_file = str(path),
                ))

        runtime = [d for d in deps if not d.is_dev]
        dev     = [d for d in deps if d.is_dev]

        return DependencyInfo(
            package_manager="maven",
            dependencies=runtime,
            dev_dependencies=dev,
            source_files=[str(path)],
        )

    def _parse_build_gradle(self, path: Path) -> DependencyInfo:
        """Parse a Gradle build.gradle file (regex-based)."""
        text = path.read_text(encoding="utf-8", errors="ignore")
        deps:     List[Dependency] = []
        dev_deps: List[Dependency] = []

        # e.g.  implementation 'com.example:library:1.0'
        #        testImplementation "junit:junit:4.13"
        for m in re.finditer(
            r"(implementation|api|compileOnly|testImplementation|runtimeOnly)"
            r"\s+['\"]([^'\"]+)['\"]",
            text
        ):
            scope, coord = m.group(1), m.group(2)
            parts   = coord.split(":")
            name    = parts[1] if len(parts) > 1 else coord
            version = parts[2] if len(parts) > 2 else ""
            is_dev  = scope.startswith("test")
            dep     = Dependency(name=name, version=version, is_dev=is_dev,
                                 source_file=str(path))
            (dev_deps if is_dev else deps).append(dep)

        return DependencyInfo(
            package_manager="gradle",
            dependencies=deps,
            dev_dependencies=dev_deps,
            source_files=[str(path)],
        )

    def _parse_pubspec_yaml(self, path: Path) -> DependencyInfo:
        """Parse a Flutter/Dart pubspec.yaml file (regex-based YAML parsing)."""
        text = path.read_text(encoding="utf-8", errors="ignore")
        deps:     List[Dependency] = []
        dev_deps: List[Dependency] = []

        dep_block = re.search(r'^dependencies:(.*?)(?=^\S|\Z)', text,
                               re.DOTALL | re.MULTILINE)
        if dep_block:
            for m in re.finditer(r'^\s{2}([a-z_]+):\s*(\^?[\d\.]+)?',
                                  dep_block.group(1), re.MULTILINE):
                if m.group(1) not in ("flutter", "sdk"):
                    deps.append(Dependency(name=m.group(1),
                                           version=m.group(2) or "",
                                           source_file=str(path)))

        dev_block = re.search(r'^dev_dependencies:(.*?)(?=^\S|\Z)', text,
                               re.DOTALL | re.MULTILINE)
        if dev_block:
            for m in re.finditer(r'^\s{2}([a-z_]+):\s*(\^?[\d\.]+)?',
                                  dev_block.group(1), re.MULTILINE):
                dev_deps.append(Dependency(name=m.group(1),
                                           version=m.group(2) or "",
                                           is_dev=True,
                                           source_file=str(path)))

        return DependencyInfo(
            package_manager="pub",
            dependencies=deps,
            dev_dependencies=dev_deps,
            source_files=[str(path)],
        )
