"""
Terminal Output Analyzer — v1.0

Analyzes terminal output from AI-executed commands to identify:
- Compiler errors
- Runtime errors
- Warnings
- Test results
- Stack traces

Provides explanations and suggested fixes.
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ErrorLocation:
    """Location of an error in source code."""
    file_path: str
    line_number: int
    column: int = 0
    content: str = ""


@dataclass
class Diagnostic:
    """Diagnostic information about an error or warning."""
    severity: str  # error, warning, info, hint
    message: str
    file_path: str = ""
    line_number: int = 0
    column: int = 0
    code: str = ""
    suggested_fix: str = ""


@dataclass
class AnalysisResult:
    """Result of terminal output analysis."""
    success: bool
    has_errors: bool
    has_warnings: bool
    has_compiler_errors: bool
    has_runtime_errors: bool
    has_test_results: bool
    has_stack_traces: bool
    errors: List[Diagnostic] = field(default_factory=list)
    warnings: List[Diagnostic] = field(default_factory=list)
    stack_traces: List[str] = field(default_factory=list)
    test_summary: Dict = field(default_factory=dict)
    suggested_fixes: List[str] = field(default_factory=list)


class TerminalOutputAnalyzer:
    """
    Analyzes terminal output to identify issues and provide suggestions.
    
    Supports multiple languages:
    - Python (Tracebacks, exceptions)
    - C/C++ (GCC, Clang errors)
    - Java (javac, runtime exceptions)
    - Rust (cargo errors)
    - Node.js (npm, Jest)
    """
    
    def __init__(self):
        self._patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict:
        """Compile regex patterns for different languages."""
        return {
            # Python patterns
            "python_traceback": r'File\s+"([^"]+)",\s*line\s+(\d+)',
            "python_exception": r'(\w+Error|Exception):\s*(.+)',
            "python_syntax_error": r'SyntaxError:\s*(.+)',
            
            # C/C++ patterns
            "cpp_error": r'([^\s:]+)\.([a-z]+):(\d+):(\d+):\s*(error|warning):\s*(.+)',
            "cpp_file_line": r'([^\s:]+)\.([a-z]+):(\d+):',
            
            # Java patterns
            "java_error": r'([^\s:]+\.java):(\d+):\s*(error|warning):\s*(.+)',
            "java_exception": r'Exception in thread "[^"]+"\s*([\w.]+):(.+)',
            
            # Rust patterns
            "rust_error": r'-->?\s*([^:]+):(\d+):(\d+)',
            "rust_compiler_error": r'error\[E\d+\]:\s*(.+)',
            
            # Jest/Node patterns
            "jest_error": r'●\s*(.+)',
            "jest_test": r'(\d+)\s+(test|pass|fail)',
            
            # Generic patterns
            "generic_error": r'(error|Error|ERROR):\s*(.+)',
            "generic_warning": r'(warning|Warning|WARNING):\s*(.+)',
        }
    
    def analyze(self, output: str, command: str = "") -> AnalysisResult:
        """
        Analyze terminal output for errors and warnings.
        
        Args:
            output: Terminal output to analyze
            command: The command that was executed
            
        Returns:
            AnalysisResult with findings and suggestions
        """
        result = AnalysisResult(
            success=False,
            has_errors=False,
            has_warnings=False,
            has_compiler_errors=False,
            has_runtime_errors=False,
            has_test_results=False,
            has_stack_traces=False
        )
        
        if not output:
            result.success = True
            return result
        
        # Detect language and analyze
        output_lower = output.lower()
        
        # Python analysis
        if self._is_python_command(command) or self._detect_python(output_lower):
            self._analyze_python(output, result)
        
        # C/C++ analysis
        elif self._is_cpp_command(command) or self._detect_cpp(output_lower):
            self._analyze_cpp(output, result)
        
        # Java analysis
        elif self._is_java_command(command) or self._detect_java(output_lower):
            self._analyze_java(output, result)
        
        # Rust analysis
        elif self._is_rust_command(command) or self._detect_rust(output_lower):
            self._analyze_rust(output, result)
        
        # Node.js/Jest analysis
        elif self._is_node_command(command) or self._detect_node(output_lower):
            self._analyze_node(output, result)
        
        # Generic analysis (fallback)
        self._analyze_generic(output, result)
        
        # Generate suggested fixes
        result.suggested_fixes = self._generate_suggestions(result)
        
        return result
    
    def _is_python_command(self, command: str) -> bool:
        """Check if command is a Python command."""
        return command.startswith("python") or command.startswith("python3")
    
    def _detect_python(self, output: str) -> bool:
        """Detect Python output."""
        return "traceback" in output or "exception" in output or "error:" in output
    
    def _analyze_python(self, output: str, result: AnalysisResult):
        """Analyze Python output."""
        # Extract tracebacks
        traceback_pattern = r'Traceback \(most recent call last\):\n((?:\s*File\s+"[^"]+",\s*line\s+\d+.*\n)+)'
        match = re.search(traceback_pattern, output)
        if match:
            result.has_stack_traces = True
            result.has_runtime_errors = True
            
            # Extract file locations
            for line in match.group(1).split("\n"):
                file_match = re.search(r'File\s+"([^"]+)",\s*line\s+(\d+)', line)
                if file_match:
                    loc = ErrorLocation(
                        file_path=file_match.group(1),
                        line_number=int(file_match.group(2))
                    )
                    result.errors.append(Diagnostic(
                        severity="error",
                        message="Python exception in traceback",
                        file_path=loc.file_path,
                        line_number=loc.line_number
                    ))
        
        # Extract exception type
        exception_match = re.search(r'(\w+Error|Exception):\s*(.+)', output)
        if exception_match:
            result.has_runtime_errors = True
            result.errors.append(Diagnostic(
                severity="error",
                message=f"{exception_match.group(1)}: {exception_match.group(2)}",
                suggested_fix=f"Handle the {exception_match.group(1)} exception"
            ))
        
        # Syntax errors
        syntax_match = re.search(r'SyntaxError:\s*(.+)', output)
        if syntax_match:
            result.has_compiler_errors = True
            result.errors.append(Diagnostic(
                severity="error",
                message=syntax_match.group(1),
                suggested_fix="Fix the syntax error in your Python code"
            ))
    
    def _is_cpp_command(self, command: str) -> bool:
        """Check if command is a C/C++ command."""
        return any(cmd in command for cmd in ["gcc", "g++", "clang", "clang++", "make", "cmake"])
    
    def _detect_cpp(self, output: str) -> bool:
        """Detect C/C++ output."""
        return "error:" in output or "warning:" in output
    
    def _analyze_cpp(self, output: str, result: AnalysisResult):
        """Analyze C/C++ output."""
        # Extract errors
        error_pattern = r'([^\s:]+)\.([a-z]+):(\d+):(\d+):\s*(error):\s*(.+)'
        for match in re.finditer(error_pattern, output):
            result.has_compiler_errors = True
            result.errors.append(Diagnostic(
                severity="error",
                message=match.group(6),
                file_path=f"{match.group(1)}.{match.group(2)}",
                line_number=int(match.group(3)),
                column=int(match.group(4))
            ))
        
        # Extract warnings
        warning_pattern = r'([^\s:]+)\.([a-z]+):(\d+):(\d+):\s*(warning):\s*(.+)'
        for match in re.finditer(warning_pattern, output):
            result.has_warnings = True
            result.warnings.append(Diagnostic(
                severity="warning",
                message=match.group(6),
                file_path=f"{match.group(1)}.{match.group(2)}",
                line_number=int(match.group(3)),
                column=int(match.group(4))
            ))
    
    def _is_java_command(self, command: str) -> bool:
        """Check if command is a Java command."""
        return any(cmd in command for cmd in ["javac", "java", "mvn", "gradle"])
    
    def _detect_java(self, output: str) -> bool:
        """Detect Java output."""
        return ".java:" in output or "Exception" in output
    
    def _analyze_java(self, output: str, result: AnalysisResult):
        """Analyze Java output."""
        # Extract errors
        error_pattern = r'([^\s:]+\.java):(\d+):\s*(error):\s*(.+)'
        for match in re.finditer(error_pattern, output):
            result.has_compiler_errors = True
            result.errors.append(Diagnostic(
                severity="error",
                message=match.group(4),
                file_path=match.group(1),
                line_number=int(match.group(2))
            ))
        
        # Extract exceptions
        exception_pattern = r'Exception in thread "[^"]+"\s*([\w.]+):(.+)'
        match = re.search(exception_pattern, output)
        if match:
            result.has_runtime_errors = True
            result.errors.append(Diagnostic(
                severity="error",
                message=match.group(2),
                suggested_fix=f"Handle the {match.group(1)} exception"
            ))
    
    def _is_rust_command(self, command: str) -> bool:
        """Check if command is a Rust command."""
        return command.startswith("cargo")
    
    def _detect_rust(self, output: str) -> bool:
        """Detect Rust output."""
        return "-->" in output or "error" in output
    
    def _analyze_rust(self, output: str, result: AnalysisResult):
        """Analyze Rust output."""
        # Extract errors
        error_pattern = r'-->?\s*([^:]+):(\d+):(\d+)\s*\n\s*\|\s*\d+\s*\|\s*(.+)'
        for match in re.finditer(error_pattern, output, re.MULTILINE):
            result.has_compiler_errors = True
            result.errors.append(Diagnostic(
                severity="error",
                message=match.group(4).strip(),
                file_path=match.group(1),
                line_number=int(match.group(2)),
                column=int(match.group(3))
            ))
        
        # Extract compiler error codes
        code_pattern = r'error\[E(\d+)\]:\s*(.+)'
        for match in re.finditer(code_pattern, output):
            result.errors.append(Diagnostic(
                severity="error",
                message=match.group(2),
                code=f"E{match.group(1)}",
                suggested_fix=f"Search for Rust error E{match.group(1)}"
            ))
    
    def _is_node_command(self, command: str) -> bool:
        """Check if command is a Node.js command."""
        return any(cmd in command for cmd in ["npm", "yarn", "node", "jest"])
    
    def _detect_node(self, output: str) -> bool:
        """Detect Node.js output."""
        return "npm" in output or "jest" in output or "Error:" in output
    
    def _analyze_node(self, output: str, result: AnalysisResult):
        """Analyze Node.js output."""
        # Jest test results
        test_pattern = r'(\d+)\s+(test|pass|fail)'
        for match in re.finditer(test_pattern, output):
            if match.group(2) == "test":
                result.has_test_results = True
                result.test_summary["total"] = int(match.group(1))
            elif match.group(2) == "pass":
                result.test_summary["passed"] = int(match.group(1))
            elif match.group(2) == "fail":
                result.test_summary["failed"] = int(match.group(1))
        
        # Jest error messages
        error_pattern = r'●\s*(.+)'
        for match in re.finditer(error_pattern, output):
            result.has_errors = True
            result.errors.append(Diagnostic(
                severity="error",
                message=match.group(1),
                suggested_fix="Check the test file for errors"
            ))
    
    def _analyze_generic(self, output: str, result: AnalysisResult):
        """Generic analysis fallback."""
        # Extract generic errors
        error_pattern = r'(error|Error|ERROR):\s*(.+)'
        for match in re.finditer(error_pattern, output):
            result.has_errors = True
            result.errors.append(Diagnostic(
                severity="error",
                message=match.group(2),
                suggested_fix="Check the command output for details"
            ))
        
        # Extract warnings
        warning_pattern = r'(warning|Warning|WARNING):\s*(.+)'
        for match in re.finditer(warning_pattern, output):
            result.has_warnings = True
            result.warnings.append(Diagnostic(
                severity="warning",
                message=match.group(2),
                suggested_fix="Review the warning and consider fixing"
            ))
    
    def _generate_suggestions(self, result: AnalysisResult) -> List[str]:
        """Generate suggested fixes based on analysis."""
        suggestions = []
        
        if result.has_compiler_errors:
            suggestions.append("1. Review compiler error messages carefully")
            suggestions.append("2. Check file paths and syntax")
            suggestions.append("3. Verify all dependencies are installed")
        
        if result.has_runtime_errors:
            suggestions.append("1. Check exception types and stack traces")
            suggestions.append("2. Verify input data and environment")
            suggestions.append("3. Add proper error handling")
        
        if result.has_warnings:
            suggestions.append("1. Review all warnings")
            suggestions.append("2. Fix deprecated API usage")
            suggestions.append("3. Remove unused variables/imports")
        
        if result.has_test_results:
            suggestions.append("1. Check failed test details")
            suggestions.append("2. Verify test expectations")
            suggestions.append("3. Run tests individually for debugging")
        
        if not result.success and not suggestions:
            suggestions.append("1. Review the full output for clues")
            suggestions.append("2. Check command arguments")
            suggestions.append("3. Verify environment setup")
        
        return suggestions
