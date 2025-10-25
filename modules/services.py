"""Shared service objects for application-wide resources."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, TYPE_CHECKING

from modules.config import AppConfig

if TYPE_CHECKING:  # pragma: no cover - only for type checkers
    from modules.embeddings import EmbeddingsManager


ResumeLoader = Callable[[], List[str]]
MatchCacheLoader = Callable[[], Dict[str, Dict]]
EmbeddingsFactory = Callable[[], "EmbeddingsManager"]


@dataclass
class MatcherResourceService:
    """Provides cached resume data, embeddings, and match cache access."""

    config: AppConfig
    cache_path: str = "data/job_matches_cache.json"
    resume_cache_path: str = "data/resume_parsed.txt"
    _resume_bullets: Optional[List[str]] = None
    _match_cache: Optional[Dict[str, Dict]] = None
    _embeddings_manager: Optional["EmbeddingsManager"] = None

    def provide_resume_bullets(self, loader: ResumeLoader) -> List[str]:
        if self._resume_bullets is None:
            self._resume_bullets = loader()
        return self._resume_bullets

    def set_resume_bullets(self, bullets: List[str]) -> None:
        self._resume_bullets = bullets

    def provide_embeddings(self, factory: EmbeddingsFactory) -> "EmbeddingsManager":
        if self._embeddings_manager is None:
            self._embeddings_manager = factory()
        return self._embeddings_manager

    def set_embeddings_manager(self, manager: "EmbeddingsManager") -> None:
        self._embeddings_manager = manager

    def provide_match_cache(self, loader: MatchCacheLoader) -> Dict[str, Dict]:
        if self._match_cache is None:
            self._match_cache = loader()
        return self._match_cache

    def update_match_cache(self, cache: Dict[str, Dict]) -> None:
        self._match_cache = cache


_matcher_service: Optional[MatcherResourceService] = None


def register_matcher_service(service: MatcherResourceService) -> None:
    """Register a global matcher resource service for reuse."""

    global _matcher_service
    _matcher_service = service


def get_matcher_service(config: AppConfig, **kwargs) -> MatcherResourceService:
    """Return the registered matcher service, creating one if needed."""

    global _matcher_service
    if _matcher_service is None:
        _matcher_service = MatcherResourceService(config, **kwargs)
    return _matcher_service


def reset_matcher_service() -> None:
    """Reset the matcher resource service (useful in tests)."""

    global _matcher_service
    _matcher_service = None
