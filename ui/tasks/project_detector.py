"""
Auto Project Detection — Detect Project Type

Automatically detects project type and creates appropriate default tasks.
"""
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

from ui.tasks.task import Task, TaskType
from core.logger import setup_logger

logger = setup_logger(__name__)


class ProjectDetector:
    """
    Detects project type and creates appropriate default tasks.
    """
    
    def __init__(self, task_manager):
        self.task_manager = task_manager
    
    def detect_project(self, project_root: Path) -> str:
        """
        Detect the project type based on files and configuration.
        
        Returns project type string or 'unknown' if not recognized.
        """
        # Check for configuration files in priority order
        detectors = [
            self._detect_flutter,
            self._detect_django,
            self._detect_fastapi,
            self._detect_node,
            self._detect_react,
            self._detect_nextjs,
            self._detect_rust,
            self._detect_go,
            self._detect_java,
            self._detect_cmake,
            self._detect_qt,
            self._detect_cargo,
            self._detect_maven,
            self._detect_gradle,
        ]
        
        for detector in detectors:
            result = detector(project_root)
            if result:
                return result
        
        # Check for simple Python project
        if (project_root / "main.py").exists() or (project_root / "app.py").exists():
            return "python"
        
        return "unknown"
    
    def get_project_type_tasks(self, project_type: str, project_root: Path) -> List[Tuple[str, str, TaskType]]:
        """
        Get default tasks for a project type.
        
        Returns list of (name, command, task_type) tuples.
        """
        tasks = [
            ("Run", self._get_run_command(project_type, project_root), TaskType.RUN),
            ("Build", self._get_build_command(project_type, project_root), TaskType.BUILD),
            ("Test", self._get_test_command(project_type, project_root), TaskType.TEST),
            ("Clean", self._get_clean_command(project_type, project_root), TaskType.CLEAN),
            ("Install Dependencies", self._get_install_command(project_type, project_root), TaskType.INSTALL),
            ("Update Dependencies", self._get_update_command(project_type, project_root), TaskType.UPDATE),
        ]
        
        # Add type-specific tasks
        if project_type == "python":
            tasks.extend([
                ("Format", "ruff format .", TaskType.FORMAT),
                ("Lint", "ruff check .", TaskType.LINT),
                ("Package", "python -m build", TaskType.PACKAGE),
            ])
        elif project_type == "node":
            tasks.extend([
                ("Format", "prettier --write .", TaskType.FORMAT),
                ("Lint", "eslint .", TaskType.LINT),
            ])
        elif project_type == "rust":
            tasks.extend([
                ("Format", "rustfmt", TaskType.FORMAT),
                ("Lint", "clippy", TaskType.LINT),
                ("Check", "cargo check", TaskType.BUILD),
            ])
        elif project_type == "go":
            tasks.extend([
                ("Format", "gofmt -w .", TaskType.FORMAT),
                ("Lint", "golangci-lint run", TaskType.LINT),
                ("Vet", "go vet ./...", TaskType.LINT),
            ])
        elif project_type == "java":
            tasks.extend([
                ("Format", "mvn formatter:format", TaskType.FORMAT),
                ("Lint", "mvn checkstyle:check", TaskType.LINT),
            ])
        
        return tasks
    
    def _detect_flutter(self, project_root: Path) -> Optional[str]:
        """Detect Flutter project."""
        if (project_root / "pubspec.yaml").exists():
            with open(project_root / "pubspec.yaml", "r") as f:
                content = f.read()
                if "flutter:" in content:
                    return "flutter"
        return None
    
    def _detect_django(self, project_root: Path) -> Optional[str]:
        """Detect Django project."""
        if (project_root / "manage.py").exists():
            return "django"
        return None
    
    def _detect_fastapi(self, project_root: Path) -> Optional[str]:
        """Detect FastAPI project."""
        main_py = project_root / "main.py"
        if main_py.exists():
            try:
                with open(main_py, "r") as f:
                    content = f.read()
                    if "from fastapi" in content or "import fastapi" in content:
                        return "fastapi"
            except Exception:
                pass
        return None
    
    def _detect_node(self, project_root: Path) -> Optional[str]:
        """Detect Node.js project."""
        if (project_root / "package.json").exists():
            return "node"
        return None
    
    def _detect_react(self, project_root: Path) -> Optional[str]:
        """Detect React project."""
        # React typically has package.json with react dependency
        package_json = project_root / "package.json"
        if package_json.exists():
            try:
                with open(package_json, "r") as f:
                    pkg = json.load(f)
                    if "react" in pkg.get("dependencies", {}) or "react" in pkg.get("devDependencies", {}):
                        return "react"
            except Exception:
                pass
        return None
    
    def _detect_nextjs(self, project_root: Path) -> Optional[str]:
        """Detect Next.js project."""
        package_json = project_root / "package.json"
        if package_json.exists():
            try:
                with open(package_json, "r") as f:
                    pkg = json.load(f)
                    if "next" in pkg.get("dependencies", {}):
                        return "nextjs"
            except Exception:
                pass
        return None
    
    def _detect_rust(self, project_root: Path) -> Optional[str]:
        """Detect Rust project."""
        if (project_root / "Cargo.toml").exists():
            return "rust"
        return None
    
    def _detect_go(self, project_root: Path) -> Optional[str]:
        """Detect Go project."""
        if (project_root / "go.mod").exists():
            return "go"
        return None
    
    def _detect_java(self, project_root: Path) -> Optional[str]:
        """Detect Java project."""
        if (project_root / "pom.xml").exists():
            return "java-maven"
        if (project_root / "build.gradle").exists() or (project_root / "build.gradle.kts").exists():
            return "java-gradle"
        if list(project_root.glob("*.java")):
            return "java"
        return None
    
    def _detect_cmake(self, project_root: Path) -> Optional[str]:
        """Detect CMake project."""
        if (project_root / "CMakeLists.txt").exists():
            return "cmake"
        return None
    
    def _detect_qt(self, project_root: Path) -> Optional[str]:
        """Detect Qt project."""
        if (project_root / "*.pro").exists():
            return "qt"
        return None
    
    def _detect_cargo(self, project_root: Path) -> Optional[str]:
        """Detect Rust/Cargo project."""
        return self._detect_rust(project_root)
    
    def _detect_maven(self, project_root: Path) -> Optional[str]:
        """Detect Maven project."""
        return self._detect_java(project_root)
    
    def _detect_gradle(self, project_root: Path) -> Optional[str]:
        """Detect Gradle project."""
        return self._detect_java(project_root)
    
    def _get_run_command(self, project_type: str, project_root: Path) -> str:
        """Get run command for project type."""
        commands = {
            "python": "python main.py",
            "node": "npm start",
            "react": "npm start",
            "nextjs": "npm run dev",
            "flutter": "flutter run",
            "rust": "cargo run",
            "go": "go run .",
            "java": "mvn spring-boot:run",
            "django": "python manage.py runserver",
            "fastapi": "uvicorn main:app --reload",
            "cmake": "cmake --build build --target run",
            "qt": "qmake && make && ./app",
        }
        return commands.get(project_type, "python main.py")
    
    def _get_build_command(self, project_type: str, project_root: Path) -> str:
        """Get build command for project type."""
        commands = {
            "python": "python setup.py build",
            "node": "npm run build",
            "react": "npm run build",
            "nextjs": "npm run build",
            "flutter": "flutter build",
            "rust": "cargo build --release",
            "go": "go build ./...",
            "java": "mvn package",
            "django": "python manage.py collectstatic",
            "fastapi": "echo 'FastAPI is typically run directly'",
            "cmake": "cmake --build build --config Release",
            "qt": "qmake && make",
        }
        return commands.get(project_type, "echo 'Build command not configured'")
    
    def _get_test_command(self, project_type: str, project_root: Path) -> str:
        """Get test command for project type."""
        commands = {
            "python": "pytest",
            "node": "npm test",
            "react": "npm test",
            "nextjs": "npm test",
            "flutter": "flutter test",
            "rust": "cargo test",
            "go": "go test ./...",
            "java": "mvn test",
            "django": "python manage.py test",
            "fastapi": "pytest",
            "cmake": "ctest",
            "qt": "make check",
        }
        return commands.get(project_type, "echo 'Test command not configured'")
    
    def _get_clean_command(self, project_type: str, project_root: Path) -> str:
        """Get clean command for project type."""
        commands = {
            "python": "rm -rf build/ dist/ *.egg-info/ __pycache__/",
            "node": "npm run clean",
            "react": "rm -rf build/",
            "nextjs": "rm -rf .next/",
            "flutter": "flutter clean",
            "rust": "cargo clean",
            "go": "go clean -cache -testcache",
            "java": "mvn clean",
            "django": "rm -rf __pycache__/",
            "fastapi": "rm -rf __pycache__/",
            "cmake": "rm -rf build/",
            "qt": "make clean",
        }
        return commands.get(project_type, "echo 'Clean command not configured'")
    
    def _get_install_command(self, project_type: str, project_root: Path) -> str:
        """Get install command for project type."""
        commands = {
            "python": "pip install -e .",
            "node": "npm install",
            "react": "npm install",
            "nextjs": "npm install",
            "flutter": "flutter pub get",
            "rust": "cargo build",
            "go": "go mod tidy",
            "java": "mvn install",
            "django": "pip install -e .",
            "fastapi": "pip install -e .",
            "cmake": "cmake --build .",
            "qt": "qmake && make",
        }
        return commands.get(project_type, "pip install -e .")
    
    def _get_update_command(self, project_type: str, project_root: Path) -> str:
        """Get update command for project type."""
        commands = {
            "python": "pip install --upgrade -e .",
            "node": "npm update",
            "react": "npm update",
            "nextjs": "npm update",
            "flutter": "flutter pub upgrade",
            "rust": "cargo update",
            "go": "go get -u ./...",
            "java": "mvn versions:update-dependencies",
            "django": "pip install --upgrade -e .",
            "fastapi": "pip install --upgrade -e .",
            "cmake": "echo 'Update dependencies manually'",
            "qt": "echo 'Update dependencies manually'",
        }
        return commands.get(project_type, "pip install --upgrade -e .")


def create_default_tasks_for_project(task_manager, project_root: Path) -> List[str]:
    """
    Create default tasks for a project based on its type.
    
    Returns list of task IDs created.
    """
    detector = ProjectDetector(task_manager)
    
    # Detect project type
    project_type = detector.detect_project(project_root)
    
    if project_type == "unknown":
        logger.info(f"Unable to detect project type in {project_root}")
        return []
    
    logger.info(f"Detected project type: {project_type}")
    
    # Create default tasks
    tasks = detector.get_project_type_tasks(project_type, project_root)
    task_ids = []
    
    for name, command, task_type in tasks:
        try:
            task = task_manager.create_default_task(
                name=name,
                command=command,
                task_type=task_type
            )
            task_ids.append(task.id)
        except Exception as e:
            logger.error(f"Failed to create task '{name}': {e}")
    
    return task_ids
