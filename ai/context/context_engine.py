"""
context_engine.py — Intelligent Context Engine (v0.5).

The Context Engine is the mandatory gateway between the Planner and
the Model Manager. No AI model ever receives a prompt directly from
the Planner — every request must first pass through this engine.

Pipeline (all synchronous, runs in a background thread via EventBus):

    User Prompt + Current File + Cursor Position + ProjectContext
        ↓
    ContextBuilder.collect()         — gather raw project materials
        ↓
    FileImportGraph.build()          — build the import graph (cached)
        ↓
    ContextSelector.select()         — keyword-filter candidate files
        ↓
    DependencyResolver.resolve()     — follow import chains
        ↓
    ContextRanker.rank()             — score and sort by relevance
        ↓
    [Read file contents for top N]   — lazy I/O for survivors only
        ↓
    SymbolIndex.index_project()      — index symbols in selected files
        ↓
    TokenEstimator.estimate_package()— estimate token budget
        ↓
    ContextCache.put()               — store for reuse
        ↓
    EventBus.publish("context_ready")
        ↓
    ContextPackage  →  Model Manager

Public API:
    engine = ContextEngine(event_bus, project_root)
    package = engine.build(prompt, current_file, cursor_line, project_context)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from core.logger import setup_logger
from core.event_bus import EventBus

from ai.context.context_builder    import ContextBuilder
from ai.context.context_selector   import ContextSelector
from ai.context.context_ranker     import ContextRanker, RankedFile
from ai.context.dependency_resolver import DependencyResolver
from ai.context.symbol_index       import SymbolIndex, SymbolEntry
from ai.context.file_import_graph  import FileImportGraph
from ai.context.token_estimator    import TokenEstimator
from ai.context.context_cache      import ContextCache

if TYPE_CHECKING:
    from ai.memory.project_context import ProjectContext

logger = setup_logger(__name__)


# ── Data contracts ─────────────────────────────────────────────────────────

@dataclass
class SelectedFile:
    """
    One file selected for inclusion in the context package.

    Attributes:
        path:    Absolute path to the file.
        content: Full text content of the file.
        score:   Composite relevance score from ContextRanker (0-1).
        reason:  Human-readable explanation of why this file was chosen.
        token_estimate: Estimated tokens for this file alone.
    """
    path:           str
    content:        str
    score:          float
    reason:         str
    token_estimate: int = 0


@dataclass
class ContextPackage:
    """
    Optimized context package delivered to the Model Manager.

    This is the complete, ranked, token-budgeted set of everything
    a model needs to process the user's request.

    Attributes:
        prompt:            The original user prompt.
        selected_files:    Files chosen for inclusion (ranked, contents loaded).
        symbols:           Symbol index entries for selected files.
        dependency_chain:  All file paths in the dependency graph, ordered.
        token_estimate:    Total estimated token count for the package.
        cache_hit:         True if this package was served from cache.
        build_duration_ms: Time taken to build the package.
        warnings:          Non-fatal issues encountered during building.
        metadata:          Arbitrary extra data for future use.
    """
    prompt:            str
    selected_files:    List[SelectedFile]    = field(default_factory=list)
    symbols:           List[SymbolEntry]     = field(default_factory=list)
    dependency_chain:  List[str]             = field(default_factory=list)
    token_estimate:    int                   = 0
    cache_hit:         bool                  = False
    build_duration_ms: float                 = 0.0
    warnings:          List[str]             = field(default_factory=list)
    metadata:          Dict[str, Any]        = field(default_factory=dict)

    def __repr__(self) -> str:
        return (
            f"<ContextPackage files={len(self.selected_files)} "
            f"tokens≈{self.token_estimate} "
            f"cache={'HIT' if self.cache_hit else 'MISS'}>"
        )


# ── Main engine ────────────────────────────────────────────────────────────

class ContextEngine:
    """
    Intelligent Context Engine — the gateway between Planner and Model Manager.

    Responsibilities:
      1. Collect all project files and metadata.
      2. Select and rank files relevant to the user's prompt.
      3. Follow import chains to pull in necessary dependencies.
      4. Estimate token usage and enforce model budget limits.
      5. Cache results and return optimized ContextPackage objects.
      6. Publish progress events to the EventBus for UI updates.

    Args:
        event_bus:    Application-wide EventBus for UI notifications.
        project_root: Absolute path to the open project directory.
        max_files:    Maximum number of files to include in one package.
        model_limit:  Token budget for the target model.
    """

    def __init__(
        self,
        event_bus:    EventBus,
        project_root: str,
        max_files:    int = 15,
        model_limit:  int = 128_000,
    ) -> None:
        self.event_bus    = event_bus
        self._root        = Path(project_root)
        self._max_files   = max_files
        self._model_limit = model_limit

        # Component instances (stateless or lazily populated)
        self._builder   = ContextBuilder(project_root)
        self._selector  = ContextSelector(max_candidates=max_files * 3)
        self._ranker    = ContextRanker(top_n=max_files)
        self._sym_index = SymbolIndex()
        self._estimator = TokenEstimator()
        self._cache     = ContextCache(max_size=50)

        # Import graph is built once per session (lazily, then cached)
        self._import_graph: Optional[FileImportGraph] = None

        logger.info(
            f"ContextEngine ready — root='{self._root.name}', "
            f"max_files={max_files}, model_limit={model_limit:,} tokens."
        )

    # ── Public API ─────────────────────────────────────────────────────────

    def build(
        self,
        prompt:          str,
        current_file:    Optional[str]       = None,
        cursor_line:     int                  = 0,
        project_context: Optional["ProjectContext"] = None,
        open_tabs:       Optional[List[str]] = None,
    ) -> ContextPackage:
        """
        Build an optimized ContextPackage for the given prompt.

        This is the single public method called by WorkflowPipeline.
        It runs the full pipeline and publishes EventBus events for
        the UI to display progress.

        Args:
            prompt:          Raw user prompt (e.g. "Fix the login page").
            current_file:    Absolute path of the focused editor file.
            cursor_line:     Cursor line number (1-based) in current_file.
            project_context: Most recent ProjectContext from the scanner.
            open_tabs:       Paths of all open editor tabs.

        Returns:
            ContextPackage ready for the Model Manager.
        """
        start = time.perf_counter()
        logger.info(f"ContextEngine.build(): prompt='{prompt[:60]}…'")
        self._publish("context_building", {
            "prompt_preview": prompt[:60],
        })

        # ── 1. Collect raw materials ───────────────────────────────────
        builder_result = self._builder.collect(
            project_context=project_context,
            open_tabs=open_tabs,
        )
        all_files = builder_result.all_files
        logger.info(f"Context: {len(all_files)} files in project.")

        # ── 2. Cache check ─────────────────────────────────────────────
        cache_key = ContextCache.make_key(
            prompt       = prompt,
            current_file = current_file or "",
            file_mtimes  = builder_result.file_mtimes,
        )
        cached = self._cache.get(cache_key)
        if cached is not None:
            logger.info("ContextEngine: cache HIT — returning cached package.")
            cached.cache_hit = True
            self._publish_ready(cached)
            return cached

        # ── 3. Build / reuse import graph ──────────────────────────────
        graph = self._get_import_graph(project_context)

        # ── 4. Select keyword-matched candidates ───────────────────────
        candidates = self._selector.select(
            prompt       = prompt,
            all_files    = all_files,
            current_file = current_file,
            config_files = builder_result.config_files,
        )
        logger.info(f"Context: {len(candidates)} candidates after keyword selection.")

        # ── 5. Resolve dependency chains ───────────────────────────────
        seed_files = [c.path for c in candidates]
        resolver   = DependencyResolver(graph)
        dep_chain  = resolver.resolve(seed_files)
        logger.info(
            f"Context: dependency chain resolved — "
            f"{len(dep_chain.files)} total files."
        )

        # ── 6. Rank all candidates + dependencies ──────────────────────
        ranked = self._ranker.rank(
            candidates       = candidates,
            dependency_files = dep_chain.files,
            dep_depth_map    = dep_chain.depth_map,
            git_modified     = set(builder_result.git_modified),
            open_tabs        = open_tabs,
            current_file     = current_file,
        )

        # ── 7. Load file contents for top-ranked files ─────────────────
        selected_files = self._load_file_contents(ranked, builder_result.file_mtimes)

        # ── 8. Index symbols in selected files ─────────────────────────
        symbols = self._index_symbols(selected_files)

        # ── 9. Assemble package ────────────────────────────────────────
        package = ContextPackage(
            prompt           = prompt,
            selected_files   = selected_files,
            symbols          = symbols,
            dependency_chain = dep_chain.files,
            cache_hit        = False,
        )

        # ── 10. Estimate tokens, enforce budget ────────────────────────
        token_estimate = self._estimator.estimate_package(package)
        package.token_estimate = token_estimate

        budget = self._estimator.check_budget(package, self._model_limit)
        if not budget.fits:
            drop_paths = self._estimator.suggest_reduction(package, self._model_limit)
            package.warnings.append(
                f"Context exceeds model limit by {budget.excess_tokens:,} tokens. "
                f"Suggested: drop {len(drop_paths)} file(s)."
            )
            package.selected_files = [
                f for f in package.selected_files if f.path not in set(drop_paths)
            ]
            logger.warning(
                f"ContextEngine: budget exceeded — dropped {len(drop_paths)} files."
            )

        # ── 11. Final metadata ─────────────────────────────────────────
        elapsed = (time.perf_counter() - start) * 1000
        package.build_duration_ms = round(elapsed, 1)
        package.metadata.update({
            "cursor_line":       cursor_line,
            "current_file":      current_file or "",
            "project_root":      str(self._root),
            "cache_key":         cache_key[:12] + "…",
            "budget_utilisation": f"{budget.utilisation_pct}%",
        })

        # ── 12. Cache & publish ────────────────────────────────────────
        self._cache.put(
            cache_key,
            package,
            file_paths=[f.path for f in selected_files],
        )
        self._publish_ready(package)

        # ── 13. Log summary ────────────────────────────────────────────
        logger.info(
            f"ContextEngine DONE in {elapsed:.0f} ms:\n"
            f"  • {len(all_files)} files analyzed\n"
            f"  • {len(selected_files)} files selected\n"
            f"  • {len(dep_chain.files)} in dependency chain\n"
            f"  • {len(symbols)} symbols indexed\n"
            f"  • ~{token_estimate:,} tokens estimated\n"
            f"  • {budget.utilisation_pct}% of model context used\n"
            f"  • Cache: MISS → stored"
        )

        return package

    def notify_file_changed(self, file_path: str) -> None:
        """
        Call this when a file changes on disk.

        Invalidates the import graph (forcing a rebuild next call) and
        evicts any cache entries that used the changed file.
        """
        self._import_graph = None          # Force graph rebuild
        evicted = self._cache.invalidate_file(file_path)
        logger.debug(
            f"ContextEngine: file changed '{Path(file_path).name}' — "
            f"{evicted} cache entries evicted, graph reset."
        )

    def cache_stats(self) -> Dict[str, Any]:
        """Return a dict of cache health metrics for the UI."""
        s = self._cache.stats()
        return {
            "size":        s.size,
            "max_size":    s.max_size,
            "hits":        s.hits,
            "misses":      s.misses,
            "evictions":   s.evictions,
            "hit_rate":    f"{s.hit_rate_pct}%",
        }

    # ── Pipeline helpers ───────────────────────────────────────────────────

    def _get_import_graph(
        self, project_context: Optional["ProjectContext"]
    ) -> FileImportGraph:
        """Return the cached import graph, rebuilding if necessary."""
        if self._import_graph is None:
            root = str(self._root)
            logger.debug("ContextEngine: building FileImportGraph…")
            t0 = time.perf_counter()
            self._import_graph = FileImportGraph.build(root)
            elapsed = (time.perf_counter() - t0) * 1000
            stats = self._import_graph.stats()
            logger.info(
                f"FileImportGraph built in {elapsed:.0f} ms — "
                f"{stats.total_files} files, {stats.total_edges} edges."
            )
        return self._import_graph

    def _load_file_contents(
        self,
        ranked: List[RankedFile],
        mtimes: Dict[str, float],
    ) -> List[SelectedFile]:
        """Read the content of each ranked file. Skip unreadable files."""
        selected: List[SelectedFile] = []

        for ranked_file in ranked:
            p = Path(ranked_file.path)
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                logger.warning(f"ContextEngine: cannot read '{p.name}': {exc}")
                continue

            token_est = self._estimator.estimate_file(str(p), content)
            reason    = " | ".join(ranked_file.reasons) if ranked_file.reasons else "ranked"

            selected.append(SelectedFile(
                path           = str(p),
                content        = content,
                score          = ranked_file.score,
                reason         = reason,
                token_estimate = token_est,
            ))

        return selected

    def _index_symbols(self, files: List[SelectedFile]) -> List[SymbolEntry]:
        """Index symbols for all selected files."""
        symbols: List[SymbolEntry] = []
        for sf in files:
            try:
                file_symbols = self._sym_index.index_file(sf.path)
                symbols.extend(file_symbols)
            except Exception as exc:
                logger.debug(f"Symbol index error in '{sf.path}': {exc}")
        return symbols

    # ── EventBus publishing ────────────────────────────────────────────────

    def _publish(self, event_type: str, data: Dict[str, Any]) -> None:
        try:
            self.event_bus.publish(event_type, data)
        except Exception as exc:
            logger.debug(f"ContextEngine: publish failed ({event_type}): {exc}")

    def _publish_ready(self, package: ContextPackage) -> None:
        """Publish the context_ready event with key metrics for the UI."""
        self._publish("context_ready", {
            "selected_files":   [
                {"path": f.path, "reason": f.reason, "score": f.score}
                for f in package.selected_files
            ],
            "token_estimate":    package.token_estimate,
            "dependency_count":  len(package.dependency_chain),
            "cache_hit":         package.cache_hit,
            "duration_ms":       package.build_duration_ms,
            "file_count":        len(package.selected_files),
            "symbol_count":      len(package.symbols),
            "warnings":          package.warnings,
        })
