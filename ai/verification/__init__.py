"""
ai/verification/ — Verification Engine & Safe Execution (v0.7)

This package provides a complete verification framework for AI-generated
code changes. Every modification passes through validation before success
is reported, ensuring code quality and preventing broken builds.

Pipeline flow:
  Planner → Context Engine → Model Manager → Editing Pipeline
    ↓
  Verification Engine → (Format → Lint → Build → Test → Analysis)
    ↓
  Success Validator → Memory Update → UI

Key features:
  - Multi-verifier pipeline (format, lint, build, test, analysis)
  - Plugin-agnostic design (configs are configurable)
  - Automatic build system detection (Python, Node, Flutter, Rust, Java, CMake, Go)
  - Automatic test framework detection (pytest, unittest, Jest, Mocha, Flutter, Rust, Maven, Gradle)
  - Error classification with severity levels
  - Retry logic with exponential backoff
  - Comprehensive reporting

Classes (in order of pipeline):
  VerificationTask    - Task dataclass with verifiers, results, retry info
  VerificationEngine  - Main coordinator executing all verifiers
  BuildRunner         - Automated build detection and execution
  TestRunner          - Automated test framework detection and execution
  FormatterRunner     - Code formatter execution (Black, Prettier, etc.)
  LinterRunner        - Linter execution (Ruff, ESLint, etc.)
  ErrorClassifier     - Categorize failures and assign severity
  RetryManager        - Retry logic with exponential backoff
  SuccessValidator    - Determine if all checks passed
  VerificationReport  - Generate human-readable verification reports
"""

__all__ = [
    "VerificationTask",
    "VerificationEngine",
    "BuildRunner",
    "TestRunner",
    "FormatterRunner",
    "LinterRunner",
    "ErrorClassifier",
    "RetryManager",
    "SuccessValidator",
    "VerificationReportGenerator",
]

from ai.verification.verification_task import (
    VerificationTask,
    VerifierType,
    VerifierStatus,
    VerifierResult,
    VerifierConfig,
    create_default_config,
)
from ai.verification.verification_engine import VerificationEngine
from ai.verification.build_runner import BuildRunner
from ai.verification.test_runner import TestRunner
from ai.verification.formatter_runner import FormatterRunner
from ai.verification.linter_runner import LinterRunner
from ai.verification.error_classifier import ErrorClassifier
from ai.verification.retry_manager import RetryManager
from ai.verification.success_validator import SuccessValidator
from ai.verification.verification_report import VerificationReportGenerator

__version__ = "0.7.0"