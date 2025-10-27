"""Unified filtering engine for WaterlooWorks job analysis.

Supports batch filtering (post-analysis).
"""

from __future__ import annotations

from typing import Dict, Iterable, List


class FilterEngine:
    """Unified filter engine for batch job filtering."""

    def __init__(self, config: Dict):
        """Initialize filter engine with configuration."""
        self.config = config or {}
        matcher_config = self.config.get("matcher", {})
        
        # Filter criteria
        self.auto_save_threshold = matcher_config.get("auto_save_threshold", 30)
        self.min_score = matcher_config.get("min_match_score", 0)
        self.folder_name = self.config.get("waterlooworks_folder", "geese")
        
        # Location/keyword/company filters
        self.preferred_locations = self._normalize_iterable(
            self.config.get("preferred_locations", [])
        )
        self.keywords = self._normalize_iterable(
            self.config.get("keywords_to_match", [])
        )
        self.avoid_companies = self._normalize_iterable(
            self.config.get("companies_to_avoid", [])
        )

    def update_config(self, config: Dict) -> None:
        """Update the configuration used by the filter engine."""
        self.__init__(config)

    def apply_batch(self, results: Iterable[Dict]) -> List[Dict]:
        """
        Apply filters to analyzed job results in batch mode.
        
        Args:
            results: Iterable of result dictionaries with 'job' and 'match' keys
            
        Returns:
            Filtered list of results sorted by fit score
        """
        filtered: List[Dict] = []
        
        for result in results:
            job = result["job"]
            match = result["match"]

            # Score threshold filter
            if match["fit_score"] < self.min_score:
                continue

            # Location filter
            if self.preferred_locations:
                job_location = job.get("location", "").lower()
                if not any(loc in job_location for loc in self.preferred_locations):
                    continue

            # Keyword filter
            if self.keywords:
                job_text = self._aggregate_job_text(job)
                if not any(kw in job_text for kw in self.keywords):
                    continue

            # Company filter
            if self.avoid_companies:
                company = job.get("company", "").lower()
                if any(avoid in company for avoid in self.avoid_companies):
                    continue

            filtered.append(result)

        return filtered

    @staticmethod
    def _aggregate_job_text(job_data: Dict) -> str:
        """Aggregate all searchable text from a job into one string."""
        fields = ["title", "summary", "responsibilities", "skills", 
                  "employment_location_arrangement", "work_term_duration"]
        parts = []
        for field in fields:
            value = job_data.get(field)
            if value and value != "N/A":
                parts.append(str(value))
        return " ".join(parts).lower()

    @staticmethod
    def _normalize_iterable(items: Iterable[str]) -> list[str]:
        """Normalize string list to lowercase for case-insensitive matching."""
        return [item.lower() for item in items if item]
