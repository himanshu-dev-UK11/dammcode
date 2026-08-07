"""
Language Support — v1.6

Comprehensive language detection and metadata.
Supports 30+ programming languages with automatic detection from file extension.
"""
from pathlib import Path
from typing import Optional, Dict, List


class LanguageInfo:
    """Metadata about a programming language."""
    def __init__(
        self,
        name: str,
        extensions: List[str],
        line_comment: str = "",
        block_comment_start: str = "",
        block_comment_end: str = "",
        keywords: List[str] = None,
        file_icon: str = "",
        color: str = "#8E8E98"
    ):
        self.name = name
        self.extensions = extensions
        self.line_comment = line_comment
        self.block_comment_start = block_comment_start
        self.block_comment_end = block_comment_end
        self.keywords = keywords or []
        self.file_icon = file_icon
        self.color = color


# Language Database
LANGUAGES: Dict[str, LanguageInfo] = {
    "python": LanguageInfo(
        name="Python",
        extensions=[".py", ".pyw", ".pyi"],
        line_comment="#",
        keywords=[
            "and", "as", "assert", "async", "await", "break", "class", "continue",
            "def", "del", "elif", "else", "except", "False", "finally", "for",
            "from", "global", "if", "import", "in", "is", "lambda", "None",
            "nonlocal", "not", "or", "pass", "raise", "return", "True",
            "try", "while", "with", "yield", "self"
        ],
        file_icon="🐍",
        color="#3776AB"
    ),
    
    "javascript": LanguageInfo(
        name="JavaScript",
        extensions=[".js", ".mjs", ".cjs"],
        line_comment="//",
        block_comment_start="/*",
        block_comment_end="*/",
        keywords=[
            "abstract", "await", "boolean", "break", "byte", "case", "catch",
            "char", "class", "const", "continue", "debugger", "default",
            "delete", "do", "double", "else", "enum", "export", "extends",
            "false", "final", "finally", "float", "for", "function", "goto",
            "if", "implements", "import", "in", "instanceof", "int", "interface",
            "let", "long", "native", "new", "null", "package", "private",
            "protected", "public", "return", "short", "static", "super",
            "switch", "synchronized", "this", "throw", "throws", "transient",
            "true", "try", "typeof", "var", "void", "volatile", "while", "with", "yield"
        ],
        file_icon="📜",
        color="#F7DF1E"
    ),
    
    "typescript": LanguageInfo(
        name="TypeScript",
        extensions=[".ts", ".tsx"],
        line_comment="//",
        block_comment_start="/*",
        block_comment_end="*/",
        keywords=[
            "abstract", "any", "as", "async", "await", "boolean", "break", "case",
            "catch", "class", "const", "constructor", "continue", "debugger",
            "declare", "default", "delete", "do", "else", "enum", "export",
            "extends", "false", "finally", "for", "from", "function", "get",
            "if", "implements", "import", "in", "instanceof", "interface",
            "is", "keyof", "let", "module", "namespace", "never", "new",
            "null", "number", "of", "package", "private", "protected", "public",
            "readonly", "require", "return", "set", "static", "string", "super",
            "switch", "symbol", "this", "throw", "true", "try", "type", "typeof",
            "undefined", "unique", "unknown", "var", "void", "while", "with", "yield"
        ],
        file_icon="TS",
        color="#3178C6"
    ),
    
    "c": LanguageInfo(
        name="C",
        extensions=[".c", ".h"],
        line_comment="//",
        block_comment_start="/*",
        block_comment_end="*/",
        keywords=[
            "auto", "break", "case", "char", "const", "continue", "default",
            "do", "double", "else", "enum", "extern", "float", "for", "goto",
            "if", "inline", "int", "long", "register", "restrict", "return",
            "short", "signed", "sizeof", "static", "struct", "switch", "typedef",
            "union", "unsigned", "void", "volatile", "while", "_Bool", "_Complex",
            "_Imaginary"
        ],
        file_icon="C",
        color="#A8B9CC"
    ),
    
    "cpp": LanguageInfo(
        name="C++",
        extensions=[".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx"],
        line_comment="//",
        block_comment_start="/*",
        block_comment_end="*/",
        keywords=[
            "alignas", "alignof", "and", "and_eq", "asm", "auto", "bitand", "bitor",
            "bool", "break", "case", "catch", "char", "char16_t", "char32_t", "class",
            "compl", "concept", "const", "constexpr", "const_cast", "continue",
            "decltype", "default", "delete", "do", "double", "dynamic_cast", "else",
            "enum", "explicit", "export", "extern", "false", "float", "for", "friend",
            "goto", "if", "inline", "int", "long", "mutable", "namespace", "new",
            "noexcept", "not", "not_eq", "nullptr", "operator", "or", "or_eq",
            "private", "protected", "public", "register", "reinterpret_cast",
            "requires", "return", "short", "signed", "sizeof", "static", "static_assert",
            "static_cast", "struct", "switch", "template", "this", "thread_local",
            "throw", "true", "try", "typedef", "typeid", "typename", "union",
            "unsigned", "using", "virtual", "void", "volatile", "wchar_t", "while",
            "xor", "xor_eq"
        ],
        file_icon="C++",
        color="#00599C"
    ),
    
    "csharp": LanguageInfo(
        name="C#",
        extensions=[".cs"],
        line_comment="//",
        block_comment_start="/*",
        block_comment_end="*/",
        keywords=[
            "abstract", "as", "base", "bool", "break", "byte", "case", "catch",
            "char", "checked", "class", "const", "continue", "decimal", "default",
            "delegate", "do", "double", "else", "enum", "event", "explicit",
            "extern", "false", "finally", "fixed", "float", "for", "foreach",
            "goto", "if", "implicit", "in", "int", "interface", "internal", "is",
            "lock", "long", "namespace", "new", "null", "object", "operator", "out",
            "override", "params", "private", "protected", "public", "readonly",
            "ref", "return", "sbyte", "sealed", "short", "sizeof", "stackalloc",
            "static", "string", "struct", "switch", "this", "throw", "true", "try",
            "typeof", "uint", "ulong", "unchecked", "unsafe", "ushort", "using",
            "var", "virtual", "void", "volatile", "while"
        ],
        file_icon="C#",
        color="#239120"
    ),
    
    "java": LanguageInfo(
        name="Java",
        extensions=[".java"],
        line_comment="//",
        block_comment_start="/*",
        block_comment_end="*/",
        keywords=[
            "abstract", "assert", "boolean", "break", "byte", "case", "catch",
            "char", "class", "const", "continue", "default", "do", "double",
            "else", "enum", "extends", "final", "finally", "float", "for",
            "goto", "if", "implements", "import", "instanceof", "int", "interface",
            "long", "native", "new", "package", "private", "protected", "public",
            "return", "short", "static", "strictfp", "super", "switch", "synchronized",
            "this", "throw", "throws", "transient", "try", "void", "volatile", "while"
        ],
        file_icon="☕",
        color="#007396"
    ),
    
    "kotlin": LanguageInfo(
        name="Kotlin",
        extensions=[".kt", ".kts"],
        line_comment="//",
        block_comment_start="/*",
        block_comment_end="*/",
        keywords=[
            "abstract", "actual", "annotation", "as", "break", "by", "catch", "class",
            "companion", "const", "constructor", "continue", "crossinline", "data",
            "delegate", "do", "dynamic", "else", "enum", "expect", "external", "false",
            "field", "file", "final", "finally", "for", "fun", "get", "if", "import",
            "in", "infix", "init", "inline", "inner", "interface", "internal", "is",
            "it", "lateinit", "noinline", "null", "object", "open", "operator", "out",
            "override", "package", "param", "private", "property", "protected", "public",
            "receiver", "reified", "return", "sealed", "set", "setparam", "super",
            "suspend", "tailrec", "this", "throw", "true", "try", "typealias", "typeof",
            "val", "var", "vararg", "when", "where", "while"
        ],
        file_icon="KT",
        color="#7F52FF"
    ),
    
    "rust": LanguageInfo(
        name="Rust",
        extensions=[".rs"],
        line_comment="//",
        block_comment_start="/*",
        block_comment_end="*/",
        keywords=[
            "as", "async", "await", "break", "const", "continue", "crate", "dyn",
            "else", "enum", "extern", "false", "fn", "for", "if", "impl", "in",
            "let", "loop", "match", "mod", "move", "mut", "pub", "ref", "return",
            "self", "Self", "static", "struct", "super", "trait", "true", "type",
            "unsafe", "use", "where", "while", "abstract", "become", "box", "do",
            "final", "macro", "override", "priv", "try", "typeof", "unsized",
            "virtual", "yield"
        ],
        file_icon="🦀",
        color="#CE422B"
    ),
    
    "go": LanguageInfo(
        name="Go",
        extensions=[".go"],
        line_comment="//",
        block_comment_start="/*",
        block_comment_end="*/",
        keywords=[
            "break", "case", "chan", "const", "continue", "default", "defer",
            "else", "fallthrough", "for", "func", "go", "goto", "if", "import",
            "interface", "map", "package", "range", "return", "select", "struct",
            "switch", "type", "var"
        ],
        file_icon="Go",
        color="#00ADD8"
    ),
    
    "dart": LanguageInfo(
        name="Dart",
        extensions=[".dart"],
        line_comment="//",
        block_comment_start="/*",
        block_comment_end="*/",
        keywords=[
            "abstract", "as", "assert", "async", "await", "break", "case", "catch",
            "class", "const", "continue", "covariant", "default", "deferred", "do",
            "dynamic", "else", "enum", "export", "extends", "extension", "external",
            "factory", "false", "final", "finally", "for", "Function", "get", "hide",
            "if", "implements", "import", "in", "interface", "is", "late", "library",
            "mixin", "new", "null", "on", "operator", "part", "required", "rethrow",
            "return", "set", "show", "static", "super", "switch", "sync", "this",
            "throw", "true", "try", "typedef", "var", "void", "while", "with", "yield"
        ],
        file_icon="🎯",
        color="#0175C2"
    ),
    
    "php": LanguageInfo(
        name="PHP",
        extensions=[".php", ".phtml"],
        line_comment="//",
        block_comment_start="/*",
        block_comment_end="*/",
        keywords=[
            "abstract", "and", "array", "as", "break", "callable", "case", "catch",
            "class", "clone", "const", "continue", "declare", "default", "die", "do",
            "echo", "else", "elseif", "empty", "enddeclare", "endfor", "endforeach",
            "endif", "endswitch", "endwhile", "eval", "exit", "extends", "final",
            "finally", "for", "foreach", "function", "global", "goto", "if",
            "implements", "include", "include_once", "instanceof", "insteadof",
            "interface", "isset", "list", "namespace", "new", "or", "print", "private",
            "protected", "public", "require", "require_once", "return", "static",
            "switch", "throw", "trait", "try", "unset", "use", "var", "while", "xor",
            "yield"
        ],
        file_icon="🐘",
        color="#777BB4"
    ),
    
    "swift": LanguageInfo(
        name="Swift",
        extensions=[".swift"],
        line_comment="//",
        block_comment_start="/*",
        block_comment_end="*/",
        keywords=[
            "associatedtype", "class", "deinit", "enum", "extension", "fileprivate",
            "func", "import", "init", "inout", "internal", "let", "open", "operator",
            "private", "protocol", "public", "rethrows", "static", "struct",
            "subscript", "typealias", "var", "break", "case", "continue", "default",
            "defer", "do", "else", "fallthrough", "for", "guard", "if", "in", "repeat",
            "return", "switch", "where", "while", "as", "Any", "catch", "false", "is",
            "nil", "super", "self", "Self", "throw", "throws", "true", "try"
        ],
        file_icon="🍎",
        color="#FA7343"
    ),
    
    "sql": LanguageInfo(
        name="SQL",
        extensions=[".sql"],
        line_comment="--",
        block_comment_start="/*",
        block_comment_end="*/",
        keywords=[
            "ADD", "ALL", "ALTER", "AND", "AS", "ASC", "BACKUP", "BETWEEN", "BY",
            "CASE", "CHECK", "COLUMN", "CONSTRAINT", "CREATE", "DATABASE", "DEFAULT",
            "DELETE", "DESC", "DISTINCT", "DROP", "EXEC", "EXISTS", "FOREIGN", "FROM",
            "FULL", "GROUP", "HAVING", "IN", "INDEX", "INNER", "INSERT", "INTO", "IS",
            "JOIN", "KEY", "LEFT", "LIKE", "LIMIT", "NOT", "NULL", "OR", "ORDER",
            "OUTER", "PRIMARY", "PROCEDURE", "RIGHT", "ROWNUM", "SELECT", "SET",
            "TABLE", "TOP", "TRUNCATE", "UNION", "UNIQUE", "UPDATE", "VALUES", "VIEW",
            "WHERE"
        ],
        file_icon="🗄️",
        color="#CC2927"
    ),
    
    "ruby": LanguageInfo(
        name="Ruby",
        extensions=[".rb", ".rake", ".gemspec"],
        line_comment="#",
        keywords=[
            "alias", "and", "begin", "break", "case", "class", "def", "defined?",
            "do", "else", "elsif", "end", "ensure", "false", "for", "if", "in",
            "module", "next", "nil", "not", "or", "redo", "rescue", "retry",
            "return", "self", "super", "then", "true", "undef", "unless", "until",
            "when", "while", "yield"
        ],
        file_icon="💎",
        color="#CC342D"
    ),
    
    "html": LanguageInfo(
        name="HTML",
        extensions=[".html", ".htm"],
        block_comment_start="<!--",
        block_comment_end="-->",
        file_icon="🌐",
        color="#E34F26"
    ),
    
    "css": LanguageInfo(
        name="CSS",
        extensions=[".css"],
        block_comment_start="/*",
        block_comment_end="*/",
        file_icon="🎨",
        color="#1572B6"
    ),
    
    "scss": LanguageInfo(
        name="SCSS",
        extensions=[".scss"],
        line_comment="//",
        block_comment_start="/*",
        block_comment_end="*/",
        file_icon="🎨",
        color="#CC6699"
    ),
    
    "json": LanguageInfo(
        name="JSON",
        extensions=[".json"],
        file_icon="📋",
        color="#FBBF24"
    ),
    
    "yaml": LanguageInfo(
        name="YAML",
        extensions=[".yaml", ".yml"],
        line_comment="#",
        file_icon="📄",
        color="#CB171E"
    ),
    
    "xml": LanguageInfo(
        name="XML",
        extensions=[".xml", ".xsd", ".xsl"],
        block_comment_start="<!--",
        block_comment_end="-->",
        file_icon="📄",
        color="#FF6600"
    ),
    
    "markdown": LanguageInfo(
        name="Markdown",
        extensions=[".md", ".markdown"],
        file_icon="📝",
        color="#083FA1"
    ),
    
    "shell": LanguageInfo(
        name="Shell",
        extensions=[".sh", ".bash", ".zsh"],
        line_comment="#",
        keywords=[
            "if", "then", "else", "elif", "fi", "case", "esac", "for", "while",
            "until", "do", "done", "function", "select", "time", "in", "return"
        ],
        file_icon="🐚",
        color="#89E051"
    ),
    
    "powershell": LanguageInfo(
        name="PowerShell",
        extensions=[".ps1", ".psm1", ".psd1"],
        line_comment="#",
        block_comment_start="<#",
        block_comment_end="#>",
        file_icon="PS",
        color="#012456"
    ),
    
    "batch": LanguageInfo(
        name="Batch",
        extensions=[".bat", ".cmd"],
        line_comment="REM",
        file_icon="⚙️",
        color="#C1F12E"
    ),
    
    "dockerfile": LanguageInfo(
        name="Docker",
        extensions=["Dockerfile", ".dockerfile"],
        line_comment="#",
        keywords=[
            "FROM", "RUN", "CMD", "LABEL", "MAINTAINER", "EXPOSE", "ENV", "ADD",
            "COPY", "ENTRYPOINT", "VOLUME", "USER", "WORKDIR", "ARG", "ONBUILD",
            "STOPSIGNAL", "HEALTHCHECK", "SHELL"
        ],
        file_icon="🐳",
        color="#2496ED"
    ),
    
    "makefile": LanguageInfo(
        name="Makefile",
        extensions=["Makefile", ".make", ".mk"],
        line_comment="#",
        file_icon="🔨",
        color="#427819"
    ),
    
    "lua": LanguageInfo(
        name="Lua",
        extensions=[".lua"],
        line_comment="--",
        block_comment_start="--[[",
        block_comment_end="]]",
        keywords=[
            "and", "break", "do", "else", "elseif", "end", "false", "for", "function",
            "goto", "if", "in", "local", "nil", "not", "or", "repeat", "return",
            "then", "true", "until", "while"
        ],
        file_icon="🌙",
        color="#000080"
    ),
    
    "r": LanguageInfo(
        name="R",
        extensions=[".r", ".R"],
        line_comment="#",
        keywords=[
            "if", "else", "repeat", "while", "function", "for", "in", "next", "break",
            "TRUE", "FALSE", "NULL", "Inf", "NaN", "NA", "NA_integer_", "NA_real_",
            "NA_complex_", "NA_character_"
        ],
        file_icon="📊",
        color="#276DC3"
    ),
    
    "toml": LanguageInfo(
        name="TOML",
        extensions=[".toml"],
        line_comment="#",
        file_icon="⚙️",
        color="#9C4221"
    ),
    
    "ini": LanguageInfo(
        name="INI",
        extensions=[".ini", ".cfg", ".conf"],
        line_comment=";",
        file_icon="⚙️",
        color="#6D9CBE"
    ),
    
    "plaintext": LanguageInfo(
        name="Plain Text",
        extensions=[".txt", ".text", ".log"],
        file_icon="📄",
        color="#8E8E98"
    ),
}


def detect_language(file_path: Path) -> LanguageInfo:
    """Detect language from file path."""
    ext = file_path.suffix.lower()
    name = file_path.name
    
    # Check exact filename matches (Dockerfile, Makefile)
    for lang_id, lang_info in LANGUAGES.items():
        if name in lang_info.extensions:
            return lang_info
    
    # Check extension matches
    for lang_id, lang_info in LANGUAGES.items():
        if ext in lang_info.extensions:
            return lang_info
    
    # Default to plaintext
    return LANGUAGES["plaintext"]


def get_language_by_name(name: str) -> Optional[LanguageInfo]:
    """Get language info by name."""
    return LANGUAGES.get(name.lower())


def get_all_languages() -> List[LanguageInfo]:
    """Get list of all supported languages."""
    return list(LANGUAGES.values())


def get_language_id_for_file(file_path: Path) -> str:
    """Detect language ID from file path."""
    ext = file_path.suffix.lower()
    name = file_path.name
    
    # Check exact filename matches (Dockerfile, Makefile)
    for lang_id, lang_info in LANGUAGES.items():
        if name in lang_info.extensions:
            return lang_id
    
    # Check extension matches
    for lang_id, lang_info in LANGUAGES.items():
        if ext in lang_info.extensions:
            return lang_id
    
    # Default to plaintext
    return "plaintext"
