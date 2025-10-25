"""Result collection utilities for real-time job analysis."""

from __future__ import annotations

from typing import Callable, Dict, List


class RealTimeResultsCollector:
    """Track job processing statistics and handle persistence."""

    def __init__(self) -> None:
        self._results: List[Dict] = []
        self.total_jobs = 0
        self.saved_count = 0
        self.skipped_count = 0

    def start_job(self) -> None:
        self.total_jobs += 1

    def add_result(self, result: Dict) -> None:
        self._results.append(result)

    def record_saved(self) -> None:
        self.saved_count += 1

    def record_skipped(self) -> None:
        self.skipped_count += 1

    def persist(self, save_callback: Callable[[List[Dict]], None]) -> List[Dict]:
        """Persist collected results and return them sorted by score."""

        ordered = sorted(
            self._results, key=lambda result: result["match"]["fit_score"], reverse=True
        )
        save_callback(ordered)
        return ordered
