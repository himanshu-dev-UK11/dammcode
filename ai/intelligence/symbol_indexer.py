"""
Symbol Indexer — indexes classes, functions, and variables in source code.

This module provides symbol indexing for multiple programming languages.
It extracts:
- Classes
- Functions/Methods
- Variables/Constants
- Interfaces/Enums
- Import statements

The index can be used for:
- Code navigation (go to definition)
- Finding usages
- Understanding code structure
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

from core.logger import setup_logger

logger = setup_logger(__name__)


class SymbolType(Enum):
    """Types of symbols that can be indexed."""
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    CONSTANT = "constant"
    INTERFACE = "interface"
    ENUM = "enum"
    STRUCT = "struct"
    MODULE = "module"
    IMPORT = "import"
    DECORATOR = "decorator"
    ANNOTATION = "annotation"


@dataclass
class SymbolEntry:
    """Represents a symbol in the codebase."""
    name: str
    symbol_type: SymbolType
    path: str
    line_start: int
    line_end: int
    class_name: Optional[str] = None  # For methods
    module: Optional[str] = None
    signature: Optional[str] = None
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    visibility: str = "public"  # public, private, protected
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "symbol_type": self.symbol_type.value,
            "path": self.path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "class_name": self.class_name,
            "module": self.module,
            "signature": self.signature,
            "docstring": self.docstring,
            "decorators": self.decorators,
            "visibility": self.visibility,
            "parameters": self.parameters,
            "return_type": self.return_type,
        }
        
    def get_full_name(self) -> str:
        """Get the fully qualified name of the symbol."""
        if self.class_name:
            return f"{self.class_name}.{self.name}"
        return self.name


class SymbolIndexer:
    """
    Indexes symbols across a project's source code.
    
    Supports multiple programming languages:
    - Python
    - JavaScript/TypeScript
    - Java
    - C/C++
    - Go
    - Rust
    - PHP
    - Ruby
    - C#
    
    The index can be queried for:
    - Symbols by name
    - Symbols by type
    - Symbols in a file
    - Symbol definitions and references
    """
    
    def __init__(self):
        self.index: Dict[str, List[SymbolEntry]] = {}  # file_path -> symbols
        self.name_index: Dict[str, List[SymbolEntry]] = {}  # symbol_name -> entries
        
    def index_project(self, project_path: str | Path, file_patterns: List[str] = None) -> List[SymbolEntry]:
        """
        Index all symbols in a project.
        
        Args:
            project_path: Path to the project root
            file_patterns: File patterns to include (default: common source patterns)
            
        Returns:
            List of all indexed symbols
        """
        project_path = Path(project_path).resolve()
        
        if file_patterns is None:
            file_patterns = [
                "*.py", "*.js", "*.ts", "*.jsx", "*.tsx",
                "*.java", "*.c", "*.cpp", "*.h", "*.hpp",
                "*.go", "*.rs", "*.php", "*.rb", "*.cs",
            ]
            
        logger.info(f"Indexing symbols in: {project_path}")
        
        all_symbols = []
        
        for pattern in file_patterns:
            for file_path in project_path.rglob(pattern):
                symbols = self.index_file(str(file_path))
                all_symbols.extend(symbols)
                
        logger.info(f"Indexed {len(all_symbols)} symbols in project")
        
        return all_symbols
    
    def index_file(self, file_path: str | Path) -> List[SymbolEntry]:
        """
        Index all symbols in a single file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of symbols found in the file
        """
        file_path = Path(file_path).resolve()
        symbols = []
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            ext = file_path.suffix.lower()
            
            if ext == '.py':
                symbols.extend(self._index_python(content, str(file_path)))
            elif ext in ['.js', '.ts', '.jsx', '.tsx']:
                symbols.extend(self._index_js(content, str(file_path)))
            elif ext == '.java':
                symbols.extend(self._index_java(content, str(file_path)))
            elif ext in ['.c', '.cpp', '.h', '.hpp']:
                symbols.extend(self._index_c(content, str(file_path)))
            elif ext == '.go':
                symbols.extend(self._index_go(content, str(file_path)))
            elif ext == '.rs':
                symbols.extend(self._index_rust(content, str(file_path)))
            elif ext == '.php':
                symbols.extend(self._index_php(content, str(file_path)))
            elif ext == '.rb':
                symbols.extend(self._index_ruby(content, str(file_path)))
            elif ext == '.cs':
                symbols.extend(self._index_csharp(content, str(file_path)))
                
        except Exception as e:
            logger.warning(f"Error indexing file {file_path}: {e}")
            
        return symbols
    
    def _index_python(self, content: str, file_path: str) -> List[SymbolEntry]:
        """Index Python symbols."""
        symbols = []
        lines = content.split('\n')
        current_class = None
        
        for i, line in enumerate(lines, 1):
            # Class definition
            class_match = re.match(r'^class\s+(\w+)(?:\(([^)]*)\))?:', line)
            if class_match:
                current_class = class_match.group(1)
                symbols.append(SymbolEntry(
                    name=current_class,
                    symbol_type=SymbolType.CLASS,
                    path=file_path,
                    line_start=i,
                    line_end=self._find_block_end(lines, i),
                    signature=f"class {current_class}",
                ))
                continue
                
            # Function/method definition
            func_match = re.match(r'^\s*(async\s+)?def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([^:]+))?:', line)
            if func_match:
                is_async = bool(func_match.group(1))
                name = func_match.group(2)
                params = func_match.group(3)
                return_type = func_match.group(4)
                
                symbol_type = SymbolType.METHOD if current_class else SymbolType.FUNCTION
                symbols.append(SymbolEntry(
                    name=name,
                    symbol_type=symbol_type,
                    path=file_path,
                    line_start=i,
                    line_end=self._find_block_end(lines, i),
                    class_name=current_class,
                    signature=f"{'async ' if is_async else ''}def {name}({params})",
                    parameters=self._parse_parameters(params),
                    return_type=return_type.strip() if return_type else None,
                ))
                continue
                
            # Decorator
            decorator_match = re.match(r'^\s*@(\w+)', line)
            if decorator_match:
                symbols.append(SymbolEntry(
                    name=decorator_match.group(1),
                    symbol_type=SymbolType.DECORATOR,
                    path=file_path,
                    line_start=i,
                    line_end=i,
                ))
                
        return symbols
    
    def _index_js(self, content: str, file_path: str) -> List[SymbolEntry]:
        """Index JavaScript/TypeScript symbols."""
        symbols = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Function declaration
            func_match = re.match(r'\s*(export\s+)?(async\s+)?function\s+(\w+)\s*\(([^)]*)\)', line)
            if func_match:
                is_async = bool(func_match.group(2))
                name = func_match.group(3)
                params = func_match.group(4)
                
                symbols.append(SymbolEntry(
                    name=name,
                    symbol_type=SymbolType.FUNCTION,
                    path=file_path,
                    line_start=i,
                    line_end=i,
                    signature=f"{'async ' if is_async else ''}function {name}({params})",
                    parameters=self._parse_parameters(params),
                ))
                continue
                
            # Arrow function
            arrow_match = re.match(r'\s*(export\s+)?(const|let|var)\s+(\w+)\s*=\s*(async\s+)?\(([^)]*)\)\s*=>', line)
            if arrow_match:
                name = arrow_match.group(3)
                is_async = bool(arrow_match.group(4))
                params = arrow_match.group(5)
                
                symbols.append(SymbolEntry(
                    name=name,
                    symbol_type=SymbolType.FUNCTION,
                    path=file_path,
                    line_start=i,
                    line_end=i,
                    signature=f"const {name} = {'async ' if is_async else ''}({params}) =>",
                    parameters=self._parse_parameters(params),
                ))
                
            # Class definition
            class_match = re.match(r'\s*(export\s+)?class\s+(\w+)', line)
            if class_match:
                name = class_match.group(2)
                
                symbols.append(SymbolEntry(
                    name=name,
                    symbol_type=SymbolType.CLASS,
                    path=file_path,
                    line_start=i,
                    line_end=i,
                    signature=f"{'export ' if class_match.group(1) else ''}class {name}",
                ))
                
            # Interface definition (TypeScript)
            interface_match = re.match(r'\s*(export\s+)?interface\s+(\w+)', line)
            if interface_match:
                name = interface_match.group(2)
                
                symbols.append(SymbolEntry(
                    name=name,
                    symbol_type=SymbolType.INTERFACE,
                    path=file_path,
                    line_start=i,
                    line_end=i,
                    signature=f"{'export ' if interface_match.group(1) else ''}interface {name}",
                ))
                
            # Variable/constant
            var_match = re.match(r'\s*(export\s+)?(const|let|var)\s+(\w+)', line)
            if var_match:
                name = var_match.group(3)
                const = var_match.group(2) == 'const'
                
                symbols.append(SymbolEntry(
                    name=name,
                    symbol_type=SymbolType.CONSTANT if const else SymbolType.VARIABLE,
                    path=file_path,
                    line_start=i,
                    line_end=i,
                    signature=f"{var_match.group(1) or ''}{var_match.group(2)} {name}",
                ))
                
        return symbols
    
    def _index_java(self, content: str, file_path: str) -> List[SymbolEntry]:
        """Index Java symbols."""
        symbols = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Class definition
            class_match = re.match(r'^\s*(public|private|protected)?\s*(static\s+)?(final\s+)?class\s+(\w+)', line)
            if class_match:
                name = class_match.group(4)
                
                symbols.append(SymbolEntry(
                    name=name,
                    symbol_type=SymbolType.CLASS,
                    path=file_path,
                    line_start=i,
                    line_end=i,
                    signature=f"class {name}",
                ))
                
            # Method definition
            method_match = re.match(r'^\s*(public|private|protected)?\s*(static\s+)?(final\s+)?(\w+)\s+(\w+)\s*\(([^)]*)\)', line)
            if method_match:
                return_type = method_match.group(4)
                name = method_match.group(5)
                params = method_match.group(6)
                
                symbols.append(SymbolEntry(
                    name=name,
                    symbol_type=SymbolType.METHOD,
                    path=file_path,
                    line_start=i,
                    line_end=i,
                    signature=f"{return_type} {name}({params})",
                    parameters=self._parse_parameters(params),
                    return_type=return_type,
                ))
                
            # Interface definition
            interface_match = re.match(r'^\s*(public|private|protected)?\s*interface\s+(\w+)', line)
            if interface_match:
                name = interface_match.group(2)
                
                symbols.append(SymbolEntry(
                    name=name,
                    symbol_type=SymbolType.INTERFACE,
                    path=file_path,
                    line_start=i,
                    line_end=i,
                    signature=f"interface {name}",
                ))
                
            # Variable definition
            var_match = re.match(r'^\s*(public|private|protected)?\s*(static\s+)?(final\s+)?(\w+)\s+(\w+)\s*=', line)
            if var_match:
                type_name = var_match.group(4)
                name = var_match.group(5)
                
                symbols.append(SymbolEntry(
                    name=name,
                    symbol_type=SymbolType.VARIABLE,
                    path=file_path,
                    line_start=i,
                    line_end=i,
                    signature=f"{type_name} {name}",
                    parameters=[type_name],
                ))
                
        return symbols
    
    def _index_c(self, content: str, file_path: str) -> List[SymbolEntry]:
        """Index C/C++ symbols."""
        symbols = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Function definition
            func_match = re.match(r'^\s*(inline\s+)?(static\s+)?(const\s+)?(\w+)\s+(\w+)\s*\(([^)]*)\)', line)
            if func_match:
                return_type = func_match.group(4)
                name = func_match.group(5)
                params = func_match.group(6)
                
                symbols.append(SymbolEntry(
                    name=name,
                    symbol_type=SymbolType.FUNCTION,
                    path=file_path,
                    line_start=i,
                    line_end=i,
                    signature=f"{return_type} {name}({params})",
                    parameters=self._parse_parameters(params),
                    return_type=return_type,
                ))
                
            # Class/struct definition
            class_match = re.match(r'^\s*(struct|class)\s+(\w+)', line)
            if class_match:
                type_name = class_match.group(1)
                name = class_match.group(2)
                
                symbols.append(SymbolEntry(
                    name=name,
                    symbol_type=SymbolType.STRUCT if type_name == 'struct' else SymbolType.CLASS,
                    path=file_path,
                    line_start=i,
                    line_end=i,
                    signature=f"{type_name} {name}",
                ))
                
        return symbols
    
    def _index_go(self, content: str, file_path: str) -> List[SymbolEntry]:
        """Index Go symbols."""
        symbols = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Function definition
            func_match = re.match(r'^\s*func\s+(\w+)\s*\(([^)]*)\)', line)
            if func_match:
                name = func_match.group(1)
                params = func_match.group(2)
                
                symbols.append(SymbolEntry(
                    name=name,
                    symbol_type=SymbolType.FUNCTION,
                    path=file_path,
                    line_start=i,
                    line_end=i,
                    signature=f"func {name}({params})",
                    parameters=self._parse_parameters(params),
                ))
                
            # Method definition
            method_match = re.match(r'^\s*func\s+\(([^)]+)\)\s+(\w+)\s*\(([^)]*)\)', line)
            if method_match:
                receiver = method_match.group(1)
                name = method_match.group(2)
                params = method_match.group(3)
                
                symbols.append(SymbolEntry(
                    name=name,
                    symbol_type=SymbolType.METHOD,
                    path=file_path,
                    line_start=i,
                    line_end=i,
                    signature=f"func ({receiver}) {name}({params})",
                    parameters=self._parse_parameters(params),
                ))
                
            # Type definition
            type_match = re.match(r'^\s*type\s+(\w+)\s+', line)
            if type_match:
                name = type_match.group(1)
                
                symbols.append(SymbolEntry(
                    name=name,
                    symbol_type=SymbolType.STRUCT,
                    path=file_path,
                    line_start=i,
                    line_end=i,
                    signature=f"type {name}",
                ))
                
        return symbols
    
    def _index_rust(self, content: str, file_path: str) -> List[SymbolEntry]:
        """Index Rust symbols."""
        symbols = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Function definition
            func_match = re.match(r'^\s*fn\s+(\w+)\s*\(([^)]*)\)', line)
            if func_match:
                name = func_match.group(1)
                params = func_match.group(2)
                
                symbols.append(SymbolEntry(
                    name=name,
                    symbol_type=SymbolType.FUNCTION,
                    path=file_path,
                    line_start=i,
                    line_end=i,
                    signature=f"fn {name}({params})",
                    parameters=self._parse_parameters(params),
                ))
                
            # Method definition
            method_match = re.match(r'^\s*fn\s+(\w+)\s*\(([^)]*)\)', line)
            if method_match and '&self' in method_match.group(2):
                name = method_match.group(1)
                params = method_match.group(2)
                
                symbols.append(SymbolEntry(
                    name=name,
                    symbol_type=SymbolType.METHOD,
                    path=file_path,
                    line_start=i,
                    line_end=i,
                    signature=f"fn {name}({params})",
                    parameters=self._parse_parameters(params),
                ))
                
            # Struct definition
            struct_match = re.match(r'^\s*struct\s+(\w+)', line)
            if struct_match:
                name = struct_match.group(1)
                
                symbols.append(SymbolEntry(
                    name=name,
                    symbol_type=SymbolType.STRUCT,
                    path=file_path,
                    line_start=i,
                    line_end=i,
                    signature=f"struct {name}",
                ))
                
            # Enum definition
            enum_match = re.match(r'^\s*enum\s+(\w+)', line)
            if enum_match:
                name = enum_match.group(1)
                
                symbols.append(SymbolEntry(
                    name=name,
                    symbol_type=SymbolType.ENUM,
                    path=file_path,
                    line_start=i,
                    line_end=i,
                    signature=f"enum {name}",
                ))
                
        return symbols
    
    def _index_php(self, content: str, file_path: str) -> List[SymbolEntry]:
        """Index PHP symbols."""
        symbols = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Class definition
            class_match = re.match(r'^\s*(abstract\s+)?(final\s+)?class\s+(\w+)', line)
            if class_match:
                name = class_match.group(3)
                
                symbols.append(SymbolEntry(
                    name=name,
                    symbol_type=SymbolType.CLASS,
                    path=file_path,
                    line_start=i,
                    line_end=i,
                    signature=f"class {name}",
                ))
                
            # Function definition
            func_match = re.match(r'^\s*(public|private|protected)?\s*(static\s+)?function\s+(\w+)', line)
            if func_match:
                name = func_match.group(3)
                
                symbols.append(SymbolEntry(
                    name=name,
                    symbol_type=SymbolType.FUNCTION,
                    path=file_path,
                    line_start=i,
                    line_end=i,
                    signature=f"function {name}",
                ))
                
        return symbols
    
    def _index_ruby(self, content: str, file_path: str) -> List[SymbolEntry]:
        """Index Ruby symbols."""
        symbols = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Class definition
            class_match = re.match(r'^\s*class\s+(\w+)', line)
            if class_match:
                name = class_match.group(1)
                
                symbols.append(SymbolEntry(
                    name=name,
                    symbol_type=SymbolType.CLASS,
                    path=file_path,
                    line_start=i,
                    line_end=i,
                    signature=f"class {name}",
                ))
                
            # Method definition
            method_match = re.match(r'^\s*def\s+(\w+)', line)
            if method_match:
                name = method_match.group(1)
                
                symbols.append(SymbolEntry(
                    name=name,
                    symbol_type=SymbolType.METHOD,
                    path=file_path,
                    line_start=i,
                    line_end=i,
                    signature=f"def {name}",
                ))
                
        return symbols
    
    def _index_csharp(self, content: str, file_path: str) -> List[SymbolEntry]:
        """Index C# symbols."""
        symbols = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Class definition
            class_match = re.match(r'^\s*(public|private|protected)?\s*(static\s+)?(abstract\s+)?class\s+(\w+)', line)
            if class_match:
                name = class_match.group(4)
                
                symbols.append(SymbolEntry(
                    name=name,
                    symbol_type=SymbolType.CLASS,
                    path=file_path,
                    line_start=i,
                    line_end=i,
                    signature=f"class {name}",
                ))
                
            # Method definition
            method_match = re.match(r'^\s*(public|private|protected)?\s*(static\s+)?(async\s+)?(\w+)\s+(\w+)\s*\(([^)]*)\)', line)
            if method_match:
                return_type = method_match.group(4)
                name = method_match.group(5)
                params = method_match.group(6)
                
                symbols.append(SymbolEntry(
                    name=name,
                    symbol_type=SymbolType.METHOD,
                    path=file_path,
                    line_start=i,
                    line_end=i,
                    signature=f"{return_type} {name}({params})",
                    parameters=self._parse_parameters(params),
                    return_type=return_type,
                ))
                
            # Interface definition
            interface_match = re.match(r'^\s*interface\s+(\w+)', line)
            if interface_match:
                name = interface_match.group(1)
                
                symbols.append(SymbolEntry(
                    name=name,
                    symbol_type=SymbolType.INTERFACE,
                    path=file_path,
                    line_start=i,
                    line_end=i,
                    signature=f"interface {name}",
                ))
                
        return symbols
    
    def _find_block_end(self, lines: List[str], start_line: int) -> int:
        """Find the end of a code block (for Python)."""
        if start_line >= len(lines):
            return start_line
            
        base_indent = len(lines[start_line - 1]) - len(lines[start_line - 1].lstrip())
        
        for i in range(start_line, len(lines)):
            line = lines[i]
            if line.strip() and not line.startswith(' ' * (base_indent + 1)):
                return i
                
        return len(lines)
    
    def _parse_parameters(self, params: str) -> List[str]:
        """Parse function parameters into a list."""
        if not params:
            return []
            
        # Simple parsing - split by comma
        # This doesn't handle nested parentheses or complex types
        return [p.strip() for p in params.split(',')]
    
    def get_symbols_by_name(self, name: str) -> List[SymbolEntry]:
        """Get all symbols with a given name."""
        return self.name_index.get(name, [])
    
    def get_symbols_by_type(self, symbol_type: SymbolType) -> List[SymbolEntry]:
        """Get all symbols of a given type."""
        return [s for s in self.index.values() for symbol in s if symbol.symbol_type == symbol_type]
    
    def get_symbols_in_file(self, file_path: str) -> List[SymbolEntry]:
        """Get all symbols in a specific file."""
        return self.index.get(file_path, [])
    
    def find_definition(self, symbol_name: str, context_file: str = None) -> Optional[SymbolEntry]:
        """
        Find the definition of a symbol.
        
        Args:
            symbol_name: Name of the symbol to find
            context_file: Optional file path for context
            
        Returns:
            SymbolEntry if found, None otherwise
        """
        symbols = self.get_symbols_by_name(symbol_name)
        
        if not symbols:
            return None
            
        if len(symbols) == 1:
            return symbols[0]
            
        # If context file is provided, try to find in same file
        if context_file:
            for symbol in symbols:
                if symbol.path == context_file:
                    return symbol
                    
        # Return the first one
        return symbols[0]
    
    def find_usages(self, symbol: SymbolEntry) -> List[SymbolEntry]:
        """
        Find usages of a symbol in the codebase.
        
        Args:
            symbol: The symbol to find usages for
            
        Returns:
            List of SymbolEntry objects representing usages
        """
        usages = []
        
        for path, symbols in self.index.items():
            for s in symbols:
                # Check if this symbol references the given symbol
                # This is a simple implementation - could be improved
                if s.path == symbol.path:
                    continue
                    
                # Check if symbol name appears in the file
                try:
                    content = Path(s.path).read_text(encoding='utf-8', errors='ignore')
                    if symbol.name in content:
                        usages.append(s)
                except Exception:
                    pass
                    
        return usages
    
    def to_dict(self) -> Dict[str, object]:
        """Return a JSON-serializable representation of the index."""
        return {
            "file_count": len(self.index),
            "total_symbols": sum(len(symbols) for symbols in self.index.values()),
            "symbols_by_type": {
                t.value: len([s for file_symbols in self.index.values() for s in file_symbols if s.symbol_type.value == t.value])
                for t in SymbolType
            },
        }