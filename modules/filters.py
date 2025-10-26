"""Unified filtering engine for WaterlooWorks job analysis.

Supports both batch filtering (post-analysis) and real-time filtering (during scraping).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional


@dataclass
class FilterDecision:
    """Represents the outcome of evaluating a job against filter rules."""

    skip: bool
    auto_save: bool
    message: Optional[str] = None


class FilterEngine:
    """Unified filter engine for batch and real-time job filtering."""

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

    def decide_realtime(
        self,
        job_data: Dict,
        match: Dict,
        auto_save_enabled: bool,
    ) -> FilterDecision:
        """
        Make a filtering decision for real-time job processing.
        
        Args:
            job_data: Raw job data dictionary
            match: Match analysis results
            auto_save_enabled: Whether auto-save is enabled
            
        Returns:
            FilterDecision indicating whether to skip, save, or continue
        """
        # Check if job should be skipped entirely
        skip, reason = self._should_skip_job(job_data)
        if skip:
            return FilterDecision(skip=True, auto_save=False, message=f"Skipped ({reason})")

        # If auto-save is disabled, don't save but don't skip
        if not auto_save_enabled:
            return FilterDecision(skip=False, auto_save=False, message="Auto-save disabled")

        # Check score threshold for auto-save
        fit_score = match.get("fit_score", 0)
        if fit_score < self.auto_save_threshold:
            return FilterDecision(
                skip=False,
                auto_save=False,
                message=f"Not saved (score < {self.auto_save_threshold})",
            )

        # All checks passed - auto-save this job
        return FilterDecision(skip=False, auto_save=True)

    def _should_skip_job(self, job_data: Dict) -> tuple[bool, str]:
        """
        Determine if a job should be skipped entirely.
        
        Returns:
            Tuple of (should_skip, reason)
        """
        # Location filter
        if self.preferred_locations:
            location = job_data.get("location", "").lower()
            if not any(loc in location for loc in self.preferred_locations):
                return True, "location filter"

        # Keyword filter
        if self.keywords:
            job_text = self._aggregate_job_text(job_data)
            if not any(keyword in job_text for keyword in self.keywords):
                return True, "keyword filter"

        # Company filter
        if self.avoid_companies:
            company = job_data.get("company", "").lower()
            if company and any(comp in company for comp in self.avoid_companies):
                return True, "company filter"

        return False, ""

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
