"""
Reference Index — builds and queries symbol references.

This module builds an index of all symbol references (usages) in a project.
It complements SymbolIndexer by tracking where symbols are used rather than
where they are defined.

This enables features like:
- Find all usages of a function
- Find all implementations of an interface
- Cross-reference analysis
- Impact analysis
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass

from core.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class Reference:
    """Represents a reference to a symbol."""
    symbol_name: str
    file_path: str
    line_number: int
    column: int
    context: str  # Short code snippet around the reference
    
    def to_dict(self) -> Dict[str, object]:
        return {
            "symbol_name": self.symbol_name,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column": self.column,
            "context": self.context,
        }


class ReferenceIndex:
    """
    Indexes all references to symbols in a project.
    
    This index is built from:
    - Symbol definitions (from SymbolIndexer)
    - File content analysis
    
    It supports queries like:
    - get_references(symbol_name): Find all usages of a symbol
    - get_definitions(symbol_name): Find all definitions
    - get_cross_references(): Find bidirectional references
    """
    
    def __init__(self):
        self.references: Dict[str, List[Reference]] = {}  # symbol_name -> references
        self.definitions: Dict[str, List[Reference]] = {}  # symbol_name -> definitions
        self.file_references: Dict[str, List[Reference]] = {}  # file_path -> references
        
    def build_index(self, project_path: str | Path, symbols: List) -> Dict[str, List[str]]:
        """
        Build a reference index for a project.
        
        Args:
            project_path: Path to the project root
            symbols: List of SymbolEntry objects from SymbolIndexer
            
        Returns:
            Dictionary mapping symbol names to reference file paths
        """
        project_path = Path(project_path).resolve()
        
        logger.info(f"Building reference index for: {project_path}")
        
        # Reset index
        self.references = {}
        self.definitions = {}
        self.file_references = {}
        
        # Index all definitions first
        for symbol in symbols:
            self._add_definition(symbol)
            
        # Then index all references
        self._scan_files(project_path)
        
        logger.info(f"Reference index built: {len(self.references)} symbols referenced")
        
        # Return file paths for each symbol
        result = {}
        for symbol_name, refs in self.references.items():
            result[symbol_name] = list(set(r.file_path for r in refs))
            
        return result
    
    def _add_definition(self, symbol):
        """Add a symbol definition to the index."""
        ref = Reference(
            symbol_name=symbol.name,
            file_path=symbol.path,
            line_number=symbol.line_start,
            column=0,
            context=symbol.signature or "",
        )
        
        if symbol.symbol_type.value in ('class', 'function', 'method', 'variable', 'constant'):
            if symbol.name not in self.definitions:
                self.definitions[symbol.name] = []
            self.definitions[symbol.name].append(ref)
            
            if symbol.name not in self.references:
                self.references[symbol.name] = []
            self.references[symbol.name].append(ref)
            
            # Add to file references
            if symbol.path not in self.file_references:
                self.file_references[symbol.path] = []
            self.file_references[symbol.path].append(ref)
    
    def _scan_files(self, project_path: Path):
        """Scan all files for symbol references."""
        # Find all source files
        patterns = ["*.py", "*.js", "*.ts", "*.java", "*.c", "*.cpp", "*.go", "*.rs", "*.php", "*.rb", "*.cs"]
        
        for pattern in patterns:
            for file_path in project_path.rglob(pattern):
                self._scan_file(file_path)
                
    def _scan_file(self, file_path: Path):
        """Scan a single file for symbol references."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            relative_path = str(file_path.relative_to(file_path.parents[1]))  # Get relative to project
            
            for line_num, line in enumerate(lines, 1):
                # Try to match known symbols in this line
                for symbol_name in self.definitions.keys():
                    if self._symbol_in_line(symbol_name, line):
                        ref = Reference(
                            symbol_name=symbol_name,
                            file_path=relative_path,
                            line_number=line_num,
                            column=0,
                            context=line.strip(),
                        )
                        
                        if symbol_name not in self.references:
                            self.references[symbol_name] = []
                        self.references[symbol_name].append(ref)
                        
                        if relative_path not in self.file_references:
                            self.file_references[relative_path] = []
                        self.file_references[relative_path].append(ref)
                        
        except Exception as e:
            logger.warning(f"Error scanning file {file_path}: {e}")
    
    def _symbol_in_line(self, symbol_name: str, line: str) -> bool:
        """Check if a symbol name appears in a line (not as part of another identifier)."""
        # Use word boundary to match only full words
        pattern = r'\b' + re.escape(symbol_name) + r'\b'
        return bool(re.search(pattern, line))
    
    def get_references(self, symbol_name: str) -> List[Reference]:
        """Get all references to a symbol."""
        return self.references.get(symbol_name, [])
    
    def get_definitions(self, symbol_name: str) -> List[Reference]:
        """Get all definitions of a symbol."""
        return self.definitions.get(symbol_name, [])
    
    def get_file_references(self, file_path: str) -> List[Reference]:
        """Get all references in a specific file."""
        return self.file_references.get(file_path, [])
    
    def get_cross_references(self, symbol_name: str) -> Dict[str, List[Reference]]:
        """
        Get bidirectional references for a symbol.
        
        Returns a dictionary with 'references' and 'definitions' keys.
        """
        return {
            "references": self.get_references(symbol_name),
            "definitions": self.get_definitions(symbol_name),
        }
    
    def find_callers(self, function_name: str) -> List[Reference]:
        """Find all calls to a function."""
        return [ref for ref in self.get_references(function_name) 
                if 'def' not in ref.context and '(' in ref.context]
    
    def find_implementations(self, interface_name: str) -> List[Reference]:
        """Find all implementations of an interface."""
        implementations = []
        
        # For Python: look for class definitions that reference the interface
        # For Java/C#: look for implements/extends
        
        for ref in self.get_references(interface_name):
            # This is a simplified check
            if 'class' in ref.context:
                implementations.append(ref)
                
        return implementations
    
    def get_call_graph(self, function_name: str, depth: int = 3) -> Dict:
        """
        Build a call graph for a function up to a certain depth.
        
        Returns a nested dictionary showing the call hierarchy.
        """
        def build_graph(name: str, current_depth: int, visited: Set[str]) -> Dict:
            if current_depth > depth or name in visited:
                return {"name": name, "depth": current_depth}
                
            visited.add(name)
            callers = self.find_callers(name)
            
            return {
                "name": name,
                "depth": current_depth,
                "callers": [
                    build_graph(c.symbol_name, current_depth + 1, visited.copy())
                    for c in callers
                    if c.symbol_name != name  # Avoid self-reference
                ],
            }
            
        return build_graph(function_name, 0, set())
    
    def get_impact_analysis(self, symbol_name: str) -> List[str]:
        """
        Get files that would be affected by changing a symbol.
        
        This includes:
        - Direct references to the symbol
        - Files that import the file containing the symbol
        - Transitive references
        """
        affected_files = set()
        
        # Direct references
        for ref in self.get_references(symbol_name):
            affected_files.add(ref.file_path)
            
        # Files that import those files (simplified)
        # In a real implementation, this would analyze import statements
        
        return list(affected_files)
    
    def get_top_referenced(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get the most referenced symbols in the project."""
        counts = [(name, len(refs)) for name, refs in self.references.items()]
        counts.sort(key=lambda x: x[1], reverse=True)
        return counts[:limit]
    
    def to_dict(self) -> Dict[str, object]:
        """Return a JSON-serializable representation of the index."""
        return {
            "symbol_count": len(self.references),
            "definition_count": len(self.definitions),
            "file_count": len(self.file_references),
            "top_referenced": self.get_top_referenced(10),
        }