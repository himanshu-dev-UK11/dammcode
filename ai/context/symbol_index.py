"""
symbol_index.py — Per-file and per-project symbol indexing.

Indexes every class, function, method, variable, and constant in a
project so the Context Engine can surface relevant symbols alongside
selected files.

Python files are parsed with the built-in `ast` module for accuracy.
Other languages (JS, TS, Java, C#, C++) fall back to fast regex
patterns that cover the most common declaration forms.

Thread safety: SymbolIndex is stateless — each call is independent.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from core.logger import setup_logger

logger = setup_logger(__name__)


# ── Data contract ──────────────────────────────────────────────────────────

@dataclass
class SymbolEntry:
    """
    One indexed symbol in the project.

    Attributes:
        name:       Symbol identifier (e.g. "login", "AuthManager").
        kind:       One of "class", "function", "method", "variable",
                    "constant", "interface", "enum".
        file:       Absolute path to the source file.
        line:       1-based line number of the definition.
        parent:     Enclosing class name (for methods), else "".
        references: File paths where this symbol is referenced (populated
                    lazily by DependencyResolver when needed).
    """
    name:       str
    kind:       str
    file:       str
    line:       int
    parent:     str = ""
    references: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # noqa: D105
        parent_str = f".{self.parent}" if self.parent else ""
        return f"<Symbol {self.kind} {parent_str}{self.name} @ {Path(self.file).name}:{self.line}>"


# ── Language-specific regex patterns ──────────────────────────────────────

# JS/TS — covers function declarations, arrow functions, classes, const/let/var
_JS_PATTERNS: List[tuple[str, str]] = [
    (r"^\s*(?:export\s+)?(?:default\s+)?class\s+(\w+)",        "class"),
    (r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)",       "function"),
    (r"^\s*(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s*)?\(", "function"),  # arrow
    (r"^\s*(?:export\s+)?const\s+(\w+)\s*=",                   "constant"),
    (r"^\s*(?:export\s+)?(?:let|var)\s+(\w+)\s*=",             "variable"),
    (r"^\s*interface\s+(\w+)",                                  "interface"),
    (r"^\s*enum\s+(\w+)",                                       "enum"),
]

# Java/C# — classes, methods, interfaces, enums
_JAVA_PATTERNS: List[tuple[str, str]] = [
    (r"^\s*(?:public|private|protected|internal|static|abstract|sealed)?\s*class\s+(\w+)",     "class"),
    (r"^\s*(?:public|private|protected|internal|static|abstract|override|virtual)?\s*(?:void|int|str|bool|String|List|Dict|[A-Z]\w*)\s+(\w+)\s*\(",  "function"),
    (r"^\s*interface\s+(\w+)",                                                                   "interface"),
    (r"^\s*enum\s+(\w+)",                                                                        "enum"),
]

# C++ — functions, classes, structs, enums
_CPP_PATTERNS: List[tuple[str, str]] = [
    (r"^\s*class\s+(\w+)",      "class"),
    (r"^\s*struct\s+(\w+)",     "class"),
    (r"^\s*enum\s+(?:class\s+)?(\w+)", "enum"),
    (r"^(?:\w[\w\s\*&<>:,]+)\s+(\w+)\s*\(",  "function"),
]

_EXTENSION_PATTERNS: Dict[str, List[tuple[str, str]]] = {
    ".js":   _JS_PATTERNS,
    ".jsx":  _JS_PATTERNS,
    ".ts":   _JS_PATTERNS,
    ".tsx":  _JS_PATTERNS,
    ".java": _JAVA_PATTERNS,
    ".cs":   _JAVA_PATTERNS,
    ".cpp":  _CPP_PATTERNS,
    ".cc":   _CPP_PATTERNS,
    ".cxx":  _CPP_PATTERNS,
    ".h":    _CPP_PATTERNS,
    ".hpp":  _CPP_PATTERNS,
}


class SymbolIndex:
    """
    Indexes symbols in individual files or entire project trees.

    Usage::

        index = SymbolIndex()
        symbols = index.index_file("/path/to/auth.py")
        project_index = index.index_project("/path/to/project")
    """

    # ── Public API ─────────────────────────────────────────────────────────

    def index_file(self, path: str) -> List[SymbolEntry]:
        """
        Return all symbols found in a single file.

        Chooses the best parser for the file's extension.
        Returns an empty list on parse errors (never raises).
        """
        p = Path(path)
        if not p.is_file():
            return []

        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            logger.warning(f"SymbolIndex: cannot read {path}: {exc}")
            return []

        ext = p.suffix.lower()

        if ext == ".py":
            return self._index_python(path, content)
        elif ext in _EXTENSION_PATTERNS:
            return self._index_regex(path, content, _EXTENSION_PATTERNS[ext])
        else:
            return []

    def index_project(self, root: str) -> Dict[str, List[SymbolEntry]]:
        """
        Walk *root* and index every supported source file.

        Returns a dict: absolute_path → list of SymbolEntry.
        Ignores hidden dirs, __pycache__, node_modules, build/, dist/.
        """
        root_path = Path(root)
        result: Dict[str, List[SymbolEntry]] = {}

        _SKIP_DIRS = {
            "__pycache__", ".git", "node_modules",
            "build", "dist", ".venv", "venv", "env",
            ".mypy_cache", ".pytest_cache",
        }
        _SUPPORTED_EXTS = {".py", ".js", ".jsx", ".ts", ".tsx",
                           ".java", ".cs", ".cpp", ".cc", ".cxx", ".h", ".hpp"}

        for p in root_path.rglob("*"):
            if any(part in _SKIP_DIRS for part in p.parts):
                continue
            if p.suffix.lower() not in _SUPPORTED_EXTS:
                continue
            if not p.is_file():
                continue

            symbols = self.index_file(str(p))
            if symbols:
                result[str(p)] = symbols

        total = sum(len(v) for v in result.values())
        logger.debug(
            f"SymbolIndex.index_project: {len(result)} files, "
            f"{total} symbols in '{root_path.name}'."
        )
        return result

    def search(
        self,
        project_index: Dict[str, List[SymbolEntry]],
        query: str,
        kinds: Optional[List[str]] = None,
    ) -> List[SymbolEntry]:
        """
        Search the project index for symbols whose name contains *query*.

        Args:
            project_index: Output of :meth:`index_project`.
            query:         Case-insensitive substring to match.
            kinds:         If provided, restrict to these symbol kinds.
        """
        q = query.lower()
        results: List[SymbolEntry] = []

        for symbols in project_index.values():
            for sym in symbols:
                if kinds and sym.kind not in kinds:
                    continue
                if q in sym.name.lower():
                    results.append(sym)

        return sorted(results, key=lambda s: s.name.lower())

    # ── Python parser (AST) ────────────────────────────────────────────────

    def _index_python(self, path: str, content: str) -> List[SymbolEntry]:
        """Parse Python source with ast for accurate symbol extraction."""
        try:
            tree = ast.parse(content, filename=path)
        except SyntaxError as exc:
            logger.debug(f"SymbolIndex: AST parse error in {path}: {exc}")
            return []

        symbols: List[SymbolEntry] = []
        self._walk_python_node(tree, path, symbols, parent_class="")
        return symbols

    def _walk_python_node(
        self,
        node: ast.AST,
        path: str,
        out: List[SymbolEntry],
        parent_class: str,
    ) -> None:
        """Recursively visit AST nodes and collect symbol definitions."""
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                out.append(SymbolEntry(
                    name=child.name, kind="class",
                    file=path, line=child.lineno, parent=parent_class,
                ))
                # Recurse into class body to capture methods
                self._walk_python_node(child, path, out, parent_class=child.name)

            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                kind = "method" if parent_class else "function"
                out.append(SymbolEntry(
                    name=child.name, kind=kind,
                    file=path, line=child.lineno, parent=parent_class,
                ))
                # Do NOT recurse further into function bodies (too noisy)

            elif isinstance(child, ast.Assign) and not parent_class:
                # Module-level assignments: constants and variables
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        kind = "constant" if target.id.isupper() else "variable"
                        out.append(SymbolEntry(
                            name=target.id, kind=kind,
                            file=path, line=child.lineno, parent="",
                        ))

            elif isinstance(child, ast.AnnAssign) and not parent_class:
                # Module-level annotated assignments
                if isinstance(child.target, ast.Name):
                    out.append(SymbolEntry(
                        name=child.target.id, kind="variable",
                        file=path, line=child.lineno, parent="",
                    ))

    # ── Regex parser (non-Python) ──────────────────────────────────────────

    def _index_regex(
        self,
        path: str,
        content: str,
        patterns: List[tuple[str, str]],
    ) -> List[SymbolEntry]:
        """Apply a list of (pattern, kind) pairs line-by-line."""
        compiled = [(re.compile(pat), kind) for pat, kind in patterns]
        symbols: List[SymbolEntry] = []

        for lineno, line in enumerate(content.splitlines(), start=1):
            for regex, kind in compiled:
                m = regex.match(line)
                if m:
                    name = m.group(1)
                    # Skip short/generic names
                    if len(name) > 1:
                        symbols.append(SymbolEntry(
                            name=name, kind=kind,
                            file=path, line=lineno,
                        ))
                    break  # First matching pattern wins

        return symbols
