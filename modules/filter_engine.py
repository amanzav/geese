"""Filtering engine for Waterloo Works job analysis."""
from __future__ import annotations

from typing import Dict, Iterable, List


class FilterEngine:
    """Apply configuration-driven filters to analyzed job results."""

    def __init__(self, config: Dict):
        self.config = config or {}

    def apply(self, results: Iterable[Dict]) -> List[Dict]:
        """Filter analyzed job results according to the configured rules."""
        preferred_locations = self.config.get("preferred_locations", [])
        keywords = self.config.get("keywords_to_match", [])
        avoid_companies = self.config.get("companies_to_avoid", [])
        min_score = self.config.get("matcher", {}).get("min_match_score", 0)

        filtered: List[Dict] = []
        for result in results:
            job = result["job"]
            match = result["match"]

            if match["fit_score"] < min_score:
                continue

            if preferred_locations:
                job_location = job.get("location", "").lower()
                if not any(loc.lower() in job_location for loc in preferred_locations):
                    continue

            if keywords:
                job_text_parts = []
                for field in [
                    "title",
                    "summary",
                    "responsibilities",
                    "skills",
                    "employment_location_arrangement",
                    "work_term_duration",
                ]:
                    if job.get(field) and job[field] != "N/A":
                        job_text_parts.append(job[field])
                job_text = " ".join(job_text_parts).lower()
                if not any(kw.lower() in job_text for kw in keywords):
                    continue

            if avoid_companies:
                company = job.get("company", "").lower()
                if any(avoid.lower() in company for avoid in avoid_companies):
                    continue

            filtered.append(result)

        return filtered

    def update_config(self, config: Dict) -> None:
        """Update the configuration used by the filter engine."""
        self.config = config or {}
