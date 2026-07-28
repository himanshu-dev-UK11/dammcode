#!/usr/bin/env python3
"""
Static analysis of startup instrumentation.
Analyzes the code to identify all profiled phases and generate a report
without actually running the application.
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Set

class StartupAnalyzer:
    """Analyzes Python files to extract profiling instrumentation."""
    
    def __init__(self):
        self.phases: Dict[str, Dict] = {}
        self.call_hierarchy: Dict[str, List[str]] = {}
        
    def analyze_file(self, filepath: Path):
        """Extract ProfilePhase calls from a Python file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all ProfilePhase usage
            # Pattern: with ProfilePhase("name"):
            pattern = r'with\s+ProfilePhase\(["\']([^"\']+)["\']\s*(?:,\s*is_ui_thread\s*=\s*(True|False))?\)'
            matches = re.findall(pattern, content)
            
            for match in matches:
                phase_name = match[0]
                is_ui_thread = match[1] != 'False' if match[1] else True
                
                if phase_name not in self.phases:
                    self.phases[phase_name] = {
                        'name': phase_name,
                        'file': str(filepath),
                        'is_ui_thread': is_ui_thread,
                        'appears_in': []
                    }
                
                if str(filepath) not in self.phases[phase_name]['appears_in']:
                    self.phases[phase_name]['appears_in'].append(str(filepath))
            
            # Try to detect function hierarchy
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_name = node.name
                        # Look for ProfilePhase calls in this function
                        for child in ast.walk(node):
                            if isinstance(child, ast.With):
                                for item in child.items:
                                    if isinstance(item.context_expr, ast.Call):
                                        if hasattr(item.context_expr.func, 'id') and item.context_expr.func.id == 'ProfilePhase':
                                            if item.context_expr.args:
                                                if isinstance(item.context_expr.args[0], ast.Constant):
                                                    phase = item.context_expr.args[0].value
                                                    if func_name not in self.call_hierarchy:
                                                        self.call_hierarchy[func_name] = []
                                                    self.call_hierarchy[func_name].append(phase)
            except:
                pass  # AST parsing optional
                
        except Exception as e:
            print(f"Warning: Could not analyze {filepath}: {e}")
    
    def generate_report(self) -> str:
        """Generate a comprehensive report of instrumented phases."""
        report = []
        report.append("=" * 100)
        report.append("STARTUP INSTRUMENTATION ANALYSIS")
        report.append("=" * 100)
        report.append("")
        
        # Group by category
        categories = {
            'Validation & Setup': [],
            'Core Systems': [],
            'Qt & UI Framework': [],
            'MainWindow Creation': [],
            'UI Components': [],
            'Provider Platform': [],
            'Model Systems': [],
            'AI Systems': [],
            'Workflow & Execution': [],
            'Session Management': [],
            'Other': []
        }
        
        for phase_name, info in sorted(self.phases.items()):
            name_lower = phase_name.lower()
            
            if any(x in name_lower for x in ['validate', 'create_dir', 'config']):
                categories['Validation & Setup'].append((phase_name, info))
            elif any(x in name_lower for x in ['event_bus', 'error_manager', 'resource_manager', 'watchdog', 'manager_init']):
                categories['Core Systems'].append((phase_name, info))
            elif any(x in name_lower for x in ['qapplication', 'design_system', 'theme', 'stylesheet']):
                categories['Qt & UI Framework'].append((phase_name, info))
            elif any(x in name_lower for x in ['mainwindow_init', 'setup_menu', 'setup_ui', 'setup_short', 'setup_conn']):
                categories['MainWindow Creation'].append((phase_name, info))
            elif any(x in name_lower for x in ['toolbar', 'activity_bar', 'explorer', 'center_panel', 'dock', 'status_bar']):
                categories['UI Components'].append((phase_name, info))
            elif any(x in name_lower for x in ['provider', 'discovery', 'connect_provider']):
                categories['Provider Platform'].append((phase_name, info))
            elif any(x in name_lower for x in ['model', 'catalog', 'router', 'registry']):
                categories['Model Systems'].append((phase_name, info))
            elif any(x in name_lower for x in ['chat_engine', 'connection_manager', 'model_center']):
                categories['AI Systems'].append((phase_name, info))
            elif any(x in name_lower for x in ['workflow', 'execution', 'context_engine', 'applier', 'verification']):
                categories['Workflow & Execution'].append((phase_name, info))
            elif any(x in name_lower for x in ['session', 'window_show']):
                categories['Session Management'].append((phase_name, info))
            else:
                categories['Other'].append((phase_name, info))
        
        total_phases = len(self.phases)
        ui_thread_phases = sum(1 for p in self.phases.values() if p['is_ui_thread'])
        
        report.append(f"Total Instrumented Phases: {total_phases}")
        report.append(f"UI Thread Phases: {ui_thread_phases}")
        report.append(f"Background Thread Phases: {total_phases - ui_thread_phases}")
        report.append("")
        
        for category, phases in categories.items():
            if phases:
                report.append("-" * 100)
                report.append(f"{category} ({len(phases)} phases)")
                report.append("-" * 100)
                
                for phase_name, info in sorted(phases, key=lambda x: x[0]):
                    thread_status = "UI Thread" if info['is_ui_thread'] else "Background"
                    files = [Path(f).name for f in info['appears_in']]
                    report.append(f"  • {phase_name:<50} [{thread_status}]")
                    report.append(f"    Files: {', '.join(files)}")
                
                report.append("")
        
        # Critical path analysis
        report.append("=" * 100)
        report.append("CRITICAL STARTUP PATH (Sequential Operations)")
        report.append("=" * 100)
        report.append("")
        report.append("These phases must complete in sequence before the UI becomes interactive:")
        report.append("")
        
        critical_phases = [
            'total_startup',
            'validate_startup',
            'core_systems_init',
            'qapplication_init',
            'design_system_init',
            'global_stylesheet_apply',
            'theme_manager_init',
            'mainwindow_creation',
            'mainwindow_init',
            'setup_menu_bar',
            'setup_ui',
            'setup_shortcuts',
            'setup_connections',
            'window_show'
        ]
        
        found_critical = []
        for phase in critical_phases:
            if phase in self.phases:
                info = self.phases[phase]
                thread = "⚠️ UI" if info['is_ui_thread'] else "✓ BG"
                found_critical.append(f"  {thread}  {phase}")
        
        report.extend(found_critical)
        report.append("")
        
        # Optimization opportunities
        report.append("=" * 100)
        report.append("OPTIMIZATION OPPORTUNITIES")
        report.append("=" * 100)
        report.append("")
        report.append("These UI thread phases could potentially be moved to background:")
        report.append("")
        
        candidates = []
        for phase_name, info in self.phases.items():
            if info['is_ui_thread'] and any(x in phase_name.lower() for x in [
                'provider', 'model', 'catalog', 'discovery', 'connection', 'chat_engine',
                'workflow', 'context_engine', 'session', 'analyzer'
            ]):
                candidates.append(f"  • {phase_name}")
        
        if candidates:
            report.extend(sorted(candidates))
        else:
            report.append("  (Analysis will be more detailed after actual execution)")
        
        report.append("")
        report.append("=" * 100)
        
        return "\n".join(report)


def main():
    """Main analysis function."""
    project_root = Path(__file__).parent
    analyzer = StartupAnalyzer()
    
    # Analyze instrumented files
    files_to_analyze = [
        project_root / 'main.py',
        project_root / 'ui' / 'main_window.py',
    ]
    
    print("Analyzing instrumented files...")
    for filepath in files_to_analyze:
        if filepath.exists():
            print(f"  - {filepath.name}")
            analyzer.analyze_file(filepath)
    
    # Generate report
    report = analyzer.generate_report()
    print("\n" + report)
    
    # Save report
    output_file = project_root / 'STARTUP_INSTRUMENTATION_REPORT.md'
    with open(output_file, 'w') as f:
        f.write(report)
    
    print(f"\nReport saved to: {output_file}")
    print("\nNext steps:")
    print("  1. Run the application to collect actual timing data")
    print("  2. Check logs/startup_timing.json for detailed measurements")
    print("  3. Identify phases >16ms on UI thread")
    print("  4. Implement optimizations to move expensive work to background")


if __name__ == '__main__':
    main()
