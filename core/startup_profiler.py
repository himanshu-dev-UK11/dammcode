"""
Startup Performance Profiler

Tracks timing for all initialization phases to identify bottlenecks.
Generates detailed reports showing which operations exceed the 16ms UI thread threshold.
"""

import time
import threading
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class TimingEntry:
    """Records timing for a single initialization step."""
    name: str
    start_time: float
    end_time: float = 0.0
    duration_ms: float = 0.0
    thread_id: int = 0
    parent: Optional[str] = None
    is_ui_thread: bool = True
    children: List[str] = field(default_factory=list)
    
    @property
    def exceeds_threshold(self) -> bool:
        """Returns True if this operation exceeds the 16ms UI thread threshold."""
        return self.is_ui_thread and self.duration_ms > 16.0


class StartupProfiler:
    """
    Profiles application startup performance.
    
    Usage:
        profiler = StartupProfiler()
        profiler.start("phase_name")
        # ... do work ...
        profiler.end("phase_name")
        
        # Get results
        report = profiler.generate_report()
        profiler.print_report()
        profiler.save_report("startup_timing.json")
    """
    
    def __init__(self):
        self._entries: Dict[str, TimingEntry] = {}
        self._active_stack: List[str] = []
        self._main_thread_id = threading.get_ident()
        self._app_start_time = time.perf_counter()
        self._hierarchy: Dict[str, List[str]] = {}
        
    def start(self, name: str, is_ui_thread: bool = True):
        """Start timing a phase."""
        current_time = time.perf_counter()
        thread_id = threading.get_ident()
        
        # Determine parent
        parent = self._active_stack[-1] if self._active_stack else None
        
        entry = TimingEntry(
            name=name,
            start_time=current_time,
            thread_id=thread_id,
            is_ui_thread=is_ui_thread or (thread_id == self._main_thread_id),
            parent=parent
        )
        
        self._entries[name] = entry
        self._active_stack.append(name)
        
        # Track hierarchy
        if parent:
            if parent not in self._hierarchy:
                self._hierarchy[parent] = []
            self._hierarchy[parent].append(name)
            
    def end(self, name: str):
        """End timing a phase."""
        current_time = time.perf_counter()
        
        if name not in self._entries:
            print(f"Warning: Timing entry '{name}' not found")
            return
            
        entry = self._entries[name]
        entry.end_time = current_time
        entry.duration_ms = (current_time - entry.start_time) * 1000
        
        # Update children list
        if name in self._hierarchy:
            entry.children = self._hierarchy[name]
        
        # Remove from active stack
        if self._active_stack and self._active_stack[-1] == name:
            self._active_stack.pop()
    
    def get_total_time(self) -> float:
        """Get total elapsed time since profiler creation (ms)."""
        return (time.perf_counter() - self._app_start_time) * 1000
    
    def get_entry(self, name: str) -> Optional[TimingEntry]:
        """Get a timing entry by name."""
        return self._entries.get(name)
    
    def get_all_entries(self) -> List[TimingEntry]:
        """Get all timing entries sorted by start time."""
        return sorted(self._entries.values(), key=lambda e: e.start_time)
    
    def get_bottlenecks(self, threshold_ms: float = 16.0) -> List[TimingEntry]:
        """Get all UI thread operations exceeding the threshold."""
        return [
            entry for entry in self._entries.values()
            if entry.is_ui_thread and entry.duration_ms > threshold_ms
        ]
    
    def get_top_level_phases(self) -> List[TimingEntry]:
        """Get all top-level phases (no parent)."""
        return [entry for entry in self._entries.values() if entry.parent is None]
    
    def generate_report(self) -> Dict:
        """Generate a comprehensive timing report."""
        total_time = self.get_total_time()
        bottlenecks = self.get_bottlenecks()
        
        return {
            "total_startup_time_ms": total_time,
            "total_phases": len(self._entries),
            "bottlenecks_count": len(bottlenecks),
            "bottlenecks": [
                {
                    "name": entry.name,
                    "duration_ms": round(entry.duration_ms, 2),
                    "parent": entry.parent,
                    "thread": "UI" if entry.is_ui_thread else "Background"
                }
                for entry in sorted(bottlenecks, key=lambda e: e.duration_ms, reverse=True)
            ],
            "phases": [
                {
                    "name": entry.name,
                    "duration_ms": round(entry.duration_ms, 2),
                    "start_offset_ms": round((entry.start_time - self._app_start_time) * 1000, 2),
                    "parent": entry.parent,
                    "children": entry.children,
                    "thread": "UI" if entry.is_ui_thread else "Background",
                    "exceeds_threshold": entry.exceeds_threshold
                }
                for entry in sorted(self._entries.values(), key=lambda e: e.start_time)
            ]
        }
    
    def print_report(self):
        """Print a formatted timing report to console."""
        report = self.generate_report()
        
        print("\n" + "=" * 80)
        print("STARTUP PERFORMANCE AUDIT REPORT")
        print("=" * 80)
        print(f"\nTotal Startup Time: {report['total_startup_time_ms']:.2f} ms")
        print(f"Total Phases Tracked: {report['total_phases']}")
        print(f"UI Thread Bottlenecks (>16ms): {report['bottlenecks_count']}")
        
        if report['bottlenecks']:
            print("\n" + "-" * 80)
            print("CRITICAL BOTTLENECKS (Operations >16ms on UI thread)")
            print("-" * 80)
            print(f"{'Phase Name':<50} {'Duration':<12} {'Parent':<20}")
            print("-" * 80)
            for bottleneck in report['bottlenecks']:
                parent = bottleneck['parent'] or "ROOT"
                print(f"{bottleneck['name']:<50} {bottleneck['duration_ms']:>8.2f} ms  {parent:<20}")
        
        print("\n" + "-" * 80)
        print("ALL PHASES (Chronological Order)")
        print("-" * 80)
        print(f"{'Phase Name':<50} {'Duration':<12} {'Thread':<12} {'Status':<10}")
        print("-" * 80)
        
        for phase in report['phases']:
            status = "⚠️ SLOW" if phase['exceeds_threshold'] else "✓ OK"
            thread = phase['thread']
            indent = "  " * self._get_depth(phase['name'])
            name = f"{indent}{phase['name']}"
            print(f"{name:<50} {phase['duration_ms']:>8.2f} ms  {thread:<12} {status:<10}")
        
        print("=" * 80 + "\n")
    
    def _get_depth(self, name: str) -> int:
        """Calculate the hierarchy depth of a phase."""
        depth = 0
        entry = self._entries.get(name)
        while entry and entry.parent:
            depth += 1
            entry = self._entries.get(entry.parent)
        return depth
    
    def save_report(self, filepath: str = "startup_timing.json"):
        """Save the timing report to a JSON file."""
        report = self.generate_report()
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Timing report saved to: {output_path.absolute()}")
    
    def print_summary_table(self):
        """Print a compact summary table of major phases."""
        print("\n" + "=" * 100)
        print("STARTUP TIMING SUMMARY")
        print("=" * 100)
        print(f"{'Component':<40} {'Time (ms)':<15} {'Thread':<12} {'Status':<15}")
        print("=" * 100)
        
        # Group by major categories
        categories = {
            "Application Initialization": [],
            "Core Systems": [],
            "UI Creation": [],
            "Workspace & Editor": [],
            "AI Systems": [],
            "Provider Platform": [],
            "Model Loading": [],
            "Context & Memory": [],
            "Session Restoration": [],
            "Other": []
        }
        
        for entry in self.get_all_entries():
            name_lower = entry.name.lower()
            
            if any(x in name_lower for x in ['validate_startup', 'app_init', 'qapplication']):
                categories["Application Initialization"].append(entry)
            elif any(x in name_lower for x in ['event_bus', 'error_manager', 'resource_manager', 'watchdog']):
                categories["Core Systems"].append(entry)
            elif any(x in name_lower for x in ['mainwindow', 'ui', 'theme', 'design_system', 'toolbar', 'dock', 'status', 'explorer', 'activity_bar']):
                categories["UI Creation"].append(entry)
            elif any(x in name_lower for x in ['workspace', 'editor', 'lsp']):
                categories["Workspace & Editor"].append(entry)
            elif any(x in name_lower for x in ['chat_engine', 'workflow', 'agent', 'analyzer']):
                categories["AI Systems"].append(entry)
            elif any(x in name_lower for x in ['provider', 'discovery']):
                categories["Provider Platform"].append(entry)
            elif any(x in name_lower for x in ['model', 'registry', 'catalog', 'router']):
                categories["Model Loading"].append(entry)
            elif any(x in name_lower for x in ['context', 'memory', 'index', 'graph']):
                categories["Context & Memory"].append(entry)
            elif any(x in name_lower for x in ['session', 'load_session', 'restore']):
                categories["Session Restoration"].append(entry)
            else:
                categories["Other"].append(entry)
        
        for category, entries in categories.items():
            if entries:
                total_time = sum(e.duration_ms for e in entries)
                print(f"\n{category}")
                print("-" * 100)
                for entry in sorted(entries, key=lambda e: e.duration_ms, reverse=True):
                    thread = "UI" if entry.is_ui_thread else "Background"
                    status = "⚠️ >16ms" if entry.exceeds_threshold else "✓ OK"
                    print(f"  {entry.name:<38} {entry.duration_ms:>10.2f} ms  {thread:<12} {status:<15}")
                print(f"  {'Subtotal:':<38} {total_time:>10.2f} ms")
        
        print("=" * 100)


# Global singleton instance
_profiler: Optional[StartupProfiler] = None


def get_startup_profiler() -> StartupProfiler:
    """Get or create the global startup profiler instance."""
    global _profiler
    if _profiler is None:
        _profiler = StartupProfiler()
    return _profiler


def reset_profiler():
    """Reset the global profiler (useful for testing)."""
    global _profiler
    _profiler = None


# Convenience context manager
class ProfilePhase:
    """Context manager for timing a phase."""
    
    def __init__(self, name: str, is_ui_thread: bool = True):
        self.name = name
        self.is_ui_thread = is_ui_thread
        self.profiler = get_startup_profiler()
    
    def __enter__(self):
        self.profiler.start(self.name, self.is_ui_thread)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.profiler.end(self.name)
        return False
