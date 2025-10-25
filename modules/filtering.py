"""Filtering strategies for WaterlooWorks job analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional


@dataclass
class FilterDecision:
    """Represents the outcome of evaluating a job against filter rules."""

    skip: bool
    auto_save: bool
    message: Optional[str] = None


class RealTimeFilterStrategy:
    """Filtering and auto-save decisions for real-time job processing."""

    def __init__(self, config: Dict):
        matcher_config = config.get("matcher", {})
        self.auto_save_threshold = matcher_config.get("auto_save_threshold", 30)
        self.folder_name = config.get("waterlooworks_folder", "geese")
        self.preferred_locations = self._normalize_iterable(
            config.get("preferred_locations", [])
        )
        self.keywords = self._normalize_iterable(config.get("keywords_to_match", []))
        self.avoid_companies = self._normalize_iterable(
            config.get("companies_to_avoid", [])
        )

    def decide(
        self,
        job_data: Dict,
        match: Dict,
        auto_save_enabled: bool,
    ) -> FilterDecision:
        """Compute the appropriate action for a job result."""

        skip, reason = self._should_skip(job_data)
        if skip:
            return FilterDecision(skip=True, auto_save=False, message=f"Skipped ({reason})")

        if not auto_save_enabled:
            return FilterDecision(skip=False, auto_save=False, message="Auto-save disabled")

        fit_score = match.get("fit_score", 0)
        if fit_score < self.auto_save_threshold:
            return FilterDecision(
                skip=False,
                auto_save=False,
                message=f"Not saved (score < {self.auto_save_threshold})",
            )

        return FilterDecision(skip=False, auto_save=True)

    def _should_skip(self, job_data: Dict) -> tuple[bool, str]:
        """Determine if a job should be skipped and provide a reason."""

        if self.preferred_locations:
            location = job_data.get("location", "").lower()
            if not any(loc in location for loc in self.preferred_locations):
                return True, "location filter"

        if self.keywords:
            job_text = self._aggregate_text(job_data)
            if not any(keyword in job_text for keyword in self.keywords):
                return True, "keyword filter"

        if self.avoid_companies:
            company = job_data.get("company", "").lower()
            if company and any(comp in company for comp in self.avoid_companies):
                return True, "company filter"

        return False, ""

    @staticmethod
    def _normalize_iterable(items: Iterable[str]) -> list[str]:
        return [item.lower() for item in items if item]

    @staticmethod
    def _aggregate_text(job_data: Dict) -> str:
        fields = ["title", "summary", "responsibilities", "skills"]
        parts = []
        for field in fields:
            value = job_data.get(field)
            if value and value != "N/A":
                parts.append(str(value))
        return " ".join(parts).lower()
