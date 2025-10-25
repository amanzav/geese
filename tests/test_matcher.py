"""Test suite for the resume matcher with injectable dependencies."""

from __future__ import annotations

import sys
import os
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.matcher import ResumeMatcher
from modules.config import app_config_from_dict, clear_cached_configs
from modules.services import MatcherResourceService, reset_matcher_service


class FakeEmbeddingsManager:
    """Lightweight stand-in for the embeddings manager used in tests."""

    def __init__(self) -> None:
        self.resume_bullets: List[str] = []

    def index_exists(self) -> bool:
        return bool(self.resume_bullets)

    def load_index(self) -> None:
        # No-op for the fake manager since we keep bullets in memory
        return None

    def build_resume_index(self, resume_bullets: List[str]) -> None:
        self.resume_bullets = list(resume_bullets)

    def search(self, query_texts: List[str], k: int = 5) -> List[List[Dict]]:
        results: List[List[Dict]] = []
        for query in query_texts:
            matches = []
            for idx, bullet in enumerate(self.resume_bullets):
                similarity = self._similarity(query, bullet)
                if similarity > 0:
                    matches.append({
                        "resume_bullet": bullet,
                        "similarity": similarity,
                        "index": idx,
                    })
            matches.sort(key=lambda item: item["similarity"], reverse=True)
            results.append(matches[:k])
        return results

    @staticmethod
    def _similarity(query: str, bullet: str) -> float:
        query_tokens = set(query.lower().split())
        bullet_tokens = set(bullet.lower().split())
        if not query_tokens or not bullet_tokens:
            return 0.0
        overlap = query_tokens & bullet_tokens
        if not overlap:
            return 0.0
        union = query_tokens | bullet_tokens
        return round(len(overlap) / len(union), 3)


def test_matcher():
    """Verify that the matcher can score jobs using injected dependencies."""

    reset_matcher_service()
    clear_cached_configs()

    config = app_config_from_dict({
        "resume_path": "unused.pdf",
        "explicit_skills": {"tools": ["Python", "React", "Docker"]},
        "matcher": {
            "embedding_model": "fake-model",
            "similarity_threshold": 0.1,
            "top_k": 3,
            "penalty_per_missing_must_have": 0.05,
            "weights": {
                "keyword_match": 0.4,
                "semantic_coverage": 0.4,
                "semantic_strength": 0.1,
                "seniority_alignment": 0.1,
            },
        },
    })

    resume_bullets = [
        "Developed scalable Python APIs for data processing",
        "Built responsive React dashboards for analytics",
        "Automated deployments with Docker and CI/CD pipelines",
    ]

    embeddings = FakeEmbeddingsManager()

    resources = MatcherResourceService(
        config,
        cache_path=":memory:",
        resume_cache_path=":memory:",
    )
    resources.set_resume_bullets(resume_bullets)
    resources.set_embeddings_manager(embeddings)

    matcher = ResumeMatcher(config=config, resources=resources)

    sample_jobs = [
        {
            "id": "job-1",
            "title": "Backend Engineer",
            "company": "DataTech",
            "location": "Remote",
            "summary": "Looking for engineers to build Python services",
            "responsibilities": "Develop and deploy Python APIs",
            "skills": "Python, Docker, REST APIs",
        },
        {
            "id": "job-2",
            "title": "Frontend Developer",
            "company": "UI Works",
            "location": "Toronto",
            "summary": "Create interactive dashboards",
            "responsibilities": "Design and build React dashboards",
            "skills": "React, TypeScript, UX",
        },
    ]

    results = matcher.batch_analyze(sample_jobs)

    assert len(results) == 2
    assert [result["job"]["id"] for result in results] == ["job-1", "job-2"]
    assert results[0]["match"]["fit_score"] >= results[1]["match"]["fit_score"]
    assert len(matcher.match_cache) == 2
