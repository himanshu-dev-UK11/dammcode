"""
Dependency Graph — builds and queries dependency relationships.

This module builds a graph representing imports and dependencies
between files in a project. The graph is queryable to answer questions
like:
- What files does X import?
- What files import X?
- What files will be affected by changing X?
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field

from core.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class DependencyNode:
    """Represents a file in the dependency graph."""
    path: str
    imports: List[str] = field(default_factory=list)
    imported_by: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, object]:
        return {
            "path": self.path,
            "imports": self.imports,
            "imported_by": self.imported_by,
        }


@dataclass
class DependencyEdge:
    """Represents a dependency relationship between two files."""
    from_file: str
    to_file: str
    dependency_type: str = "import"  # import, extends, implements, call
    
    def to_dict(self) -> Dict[str, object]:
        return {
            "from_file": self.from_file,
            "to_file": self.to_file,
            "dependency_type": self.dependency_type,
        }


class DependencyGraph:
    """
    Builds and manages a dependency graph for a project.
    
    The graph is built by scanning import statements in source files.
    It supports queries like:
    - get_dependencies(path): What does this file import?
    - get_dependents(path): What files import this file?
    - get_impact(path): What files will be affected by changing this file?
    
    The graph is stored in memory and rebuilt when files change.
    """
    
    def __init__(self):
        self.nodes: Dict[str, DependencyNode] = {}
        self.edges: List[DependencyEdge] = []
        
    def build(self, project_path: str | Path, file_patterns: List[str] = None):
        """
        Build the dependency graph for a project.
        
        Args:
            project_path: Path to the project root
            file_patterns: File patterns to include (default: common source patterns)
        """
        project_path = Path(project_path).resolve()
        
        if file_patterns is None:
            file_patterns = [
                "*.py", "*.js", "*.ts", "*.jsx", "*.tsx",
                "*.java", "*.c", "*.cpp", "*.h", "*.hpp",
                "*.go", "*.rs", "*.php", "*.rb",
            ]
            
        logger.info(f"Building dependency graph for: {project_path}")
        
        # Reset graph
        self.nodes = {}
        self.edges = []
        
        # Find all source files
        source_files = self._find_source_files(project_path, file_patterns)
        logger.info(f"Found {len(source_files)} source files")
        
        # Build nodes and edges
        for file_path in source_files:
            self._process_file(file_path, project_path)
            
        logger.info(f"Dependency graph built: {len(self.nodes)} nodes, {len(self.edges)} edges")
        
    def _find_source_files(self, project_path: Path, patterns: List[str]) -> List[Path]:
        """Find all source files matching patterns."""
        source_files = []
        
        for pattern in patterns:
            try:
                source_files.extend(project_path.rglob(pattern))
            except Exception as e:
                logger.warning(f"Error finding files with pattern {pattern}: {e}")
                
        return source_files
        
    def _process_file(self, file_path: Path, project_path: Path):
        """Process a single file to extract dependencies."""
        relative_path = str(file_path.relative_to(project_path))
        
        # Create node
        node = DependencyNode(path=relative_path)
        
        # Parse imports based on file type
        imports = self._parse_imports(file_path, project_path)
        
        node.imports = imports
        self.nodes[relative_path] = node
        
        # Create edges
        for imp in imports:
            self.edges.append(DependencyEdge(
                from_file=relative_path,
                to_file=imp,
                dependency_type="import"
            ))
            # Update dependent's imported_by list
            if imp in self.nodes:
                self.nodes[imp].imported_by.append(relative_path)
                
    def _parse_imports(self, file_path: Path, project_path: Path) -> List[str]:
        """Parse import statements from a file."""
        imports = []
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            ext = file_path.suffix.lower()
            
            # Python imports
            if ext == '.py':
                imports.extend(self._parse_python_imports(content, file_path, project_path))
                
            # JavaScript/TypeScript imports
            elif ext in ['.js', '.ts', '.jsx', '.tsx']:
                imports.extend(self._parse_js_imports(content, file_path, project_path))
                
            # Java imports
            elif ext == '.java':
                imports.extend(self._parse_java_imports(content, file_path, project_path))
                
            # C/C++ imports
            elif ext in ['.c', '.cpp', '.h', '.hpp']:
                imports.extend(self._parse_c_imports(content, file_path, project_path))
                
            # Go imports
            elif ext == '.go':
                imports.extend(self._parse_go_imports(content, file_path, project_path))
                
            # Rust imports
            elif ext == '.rs':
                imports.extend(self._parse_rust_imports(content, file_path, project_path))
                
            # PHP imports
            elif ext == '.php':
                imports.extend(self._parse_php_imports(content, file_path, project_path))
                
            # Ruby imports
            elif ext == '.rb':
                imports.extend(self._parse_ruby_imports(content, file_path, project_path))
                
        except Exception as e:
            logger.warning(f"Error parsing imports from {file_path}: {e}")
            
        return imports
        
    def _parse_python_imports(self, content: str, file_path: Path, project_path: Path) -> List[str]:
        """Parse Python import statements."""
        imports = []
        
        # Match: import x, from x import y, import x.y.z
        patterns = [
            r'^import\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'^from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import',
        ]
        
        for line in content.split('\n'):
            line = line.strip()
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    module = match.group(1)
                    # Try to resolve to relative path
                    resolved = self._resolve_python_module(module, file_path, project_path)
                    if resolved:
                        imports.append(resolved)
                        
        return imports
    
    def _resolve_python_module(self, module: str, file_path: Path, project_path: Path) -> Optional[str]:
        """Resolve a Python module name to a file path."""
        # Convert module path to file path
        parts = module.split('.')
        rel_dir = project_path / Path(*parts)
        
        # Check for module.py
        if (rel_dir.with_suffix('.py')).exists():
            return str(rel_dir.with_suffix('.py').relative_to(project_path))
            
        # Check for module/__init__.py
        if (rel_dir / '__init__.py').exists():
            return str((rel_dir / '__init__.py').relative_to(project_path))
            
        return None
    
    def _parse_js_imports(self, content: str, file_path: Path, project_path: Path) -> List[str]:
        """Parse JavaScript/TypeScript import statements."""
        imports = []
        
        # Match: import x from 'y', import { x } from 'y', require('y')
        patterns = [
            r"import\s+(?:.*?\s+from\s+)?['\"]([^'\"]+)['\"]",
            r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
            r"import\s+type\s+.*?\s+from\s+['\"]([^'\"]+)['\"]",
        ]
        
        for line in content.split('\n'):
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    module = match.group(1)
                    resolved = self._resolve_js_module(module, file_path, project_path)
                    if resolved:
                        imports.append(resolved)
                        
        return imports
    
    def _resolve_js_module(self, module: str, file_path: Path, project_path: Path) -> Optional[str]:
        """Resolve a JavaScript module to a file path."""
        # Get the directory of the current file
        file_dir = file_path.parent
        
        # Check if module is relative
        if module.startswith('.'):
            resolved = (file_dir / module).resolve()
            if resolved.exists():
                return str(resolved.relative_to(project_path))
                
        # Non-relative imports are harder to resolve
        # Try to find in common locations
        possible_paths = [
            file_dir / module,
            file_dir / f"{module}.js",
            file_dir / f"{module}.ts",
            file_dir / f"{module}.jsx",
            file_dir / f"{module}.tsx",
        ]
        
        for path in possible_paths:
            if path.exists():
                try:
                    return str(path.relative_to(project_path))
                except ValueError:
                    # Path is not under project_path
                    pass
                    
        return None
    
    def _parse_java_imports(self, content: str, file_path: Path, project_path: Path) -> List[str]:
        """Parse Java import statements."""
        imports = []
        
        # Match: import package.Class;
        pattern = r'^import\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s*;'
        
        for line in content.split('\n'):
            line = line.strip()
            match = re.match(pattern, line)
            if match:
                module = match.group(1)
                # Convert to file path
                file_path_str = module.replace('.', '/') + '.java'
                resolved = project_path / file_path_str
                if resolved.exists():
                    imports.append(str(resolved.relative_to(project_path)))
                    
        return imports
    
    def _parse_c_imports(self, content: str, file_path: Path, project_path: Path) -> List[str]:
        """Parse C/C++ include statements."""
        imports = []
        
        # Match: #include <file> or #include "file"
        pattern = r'#include\s*[<"]([^>"]+)[>"]'
        
        for line in content.split('\n'):
            match = re.search(pattern, line)
            if match:
                header = match.group(1)
                # Try to resolve header file
                # For now, just return the header name
                # In a real implementation, this would search include paths
                imports.append(header)
                
        return imports
    
    def _parse_go_imports(self, content: str, file_path: Path, project_path: Path) -> List[str]:
        """Parse Go import statements."""
        imports = []
        
        # Match: import "path" or import ( ... )
        pattern = r'import\s+["\']([^"\']+)["\']'
        
        for line in content.split('\n'):
            match = re.search(pattern, line)
            if match:
                module = match.group(1)
                imports.append(module)
                
        return imports
    
    def _parse_rust_imports(self, content: str, file_path: Path, project_path: Path) -> List[str]:
        """Parse Rust import (use) statements."""
        imports = []
        
        # Match: use path::module;
        pattern = r'^use\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        
        for line in content.split('\n'):
            line = line.strip()
            match = re.match(pattern, line)
            if match:
                module = match.group(1)
                imports.append(module)
                
        return imports
    
    def _parse_php_imports(self, content: str, file_path: Path, project_path: Path) -> List[str]:
        """Parse PHP import statements."""
        imports = []
        
        # Match: use Namespace\Class;
        pattern = r'^use\s+([a-zA-Z_][a-zA-Z0-9_\\]*)'
        
        for line in content.split('\n'):
            line = line.strip()
            match = re.match(pattern, line)
            if match:
                module = match.group(1)
                imports.append(module)
                
        return imports
    
    def _parse_ruby_imports(self, content: str, file_path: Path, project_path: Path) -> List[str]:
        """Parse Ruby require statements."""
        imports = []
        
        # Match: require 'file' or require_relative 'file'
        pattern = r"require(?:_relative)?\s+['\"]([^'\"]+)['\"]"
        
        for line in content.split('\n'):
            match = re.search(pattern, line)
            if match:
                module = match.group(1)
                imports.append(module)
                
        return imports
    
    def get_dependencies(self, path: str) -> List[str]:
        """Get files that the given file depends on."""
        node = self.nodes.get(path)
        if node:
            return node.imports
        return []
    
    def get_dependents(self, path: str) -> List[str]:
        """Get files that depend on the given file."""
        node = self.nodes.get(path)
        if node:
            return node.imported_by
        return []
    
    def get_impact(self, path: str, include_transitive: bool = True) -> List[str]:
        """
        Get all files affected by changing the given file.
        
        Args:
            path: The file path to analyze
            include_transitive: Whether to include transitive dependencies
            
        Returns:
            List of affected file paths
        """
        affected = set()
        
        # Direct dependents
        dependents = self.get_dependents(path)
        affected.update(dependents)
        
        if include_transitive:
            # Recursively find transitive dependents
            to_process = list(dependents)
            processed = set()
            
            while to_process:
                current = to_process.pop(0)
                if current in processed:
                    continue
                processed.add(current)
                
                # Find files that depend on this one
                transitive = self.get_dependents(current)
                for t in transitive:
                    if t not in processed:
                        to_process.append(t)
                        affected.add(t)
                        
        return list(affected)
    
    def get_cycle_paths(self) -> List[List[str]]:
        """Detect and return paths with circular dependencies."""
        cycles = []
        
        def dfs(node: str, visited: Set[str], path: List[str]) -> bool:
            if node in path:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return True
                
            if node in visited:
                return False
                
            visited.add(node)
            path.append(node)
            
            # Visit all dependencies
            for dep in self.nodes.get(node, DependencyNode(path="")).imports:
                if dep in self.nodes:
                    dfs(dep, visited, path)
                    
            path.pop()
            return False
            
        for node in self.nodes:
            dfs(node, set(), [])
            
        return cycles
    
    def to_dict(self) -> Dict[str, object]:
        """Return a JSON-serializable representation of the graph."""
        return {
            "nodes": {
                path: node.to_dict()
                for path, node in self.nodes.items()
            },
            "edges": [edge.to_dict() for edge in self.edges],
            "summary": {
                "node_count": len(self.nodes),
                "edge_count": len(self.edges),
            },
        }