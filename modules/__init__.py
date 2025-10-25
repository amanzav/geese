"""Geese - WaterlooWorks Automation Modules."""

__version__ = "0.1.0"

__all__ = [
    "WaterlooWorksAuth",
    "WaterlooWorksScraper",
    "ResumeMatcher",
    "CoverLetterGenerator",
    "CoverLetterUploader",
    "FilterEngine",
    "JobAnalyzer",
]


def __getattr__(name):  # pragma: no cover - thin convenience wrapper
    if name == "WaterlooWorksAuth":
        from .auth import WaterlooWorksAuth

        return WaterlooWorksAuth
    if name == "WaterlooWorksScraper":
        from .scraper import WaterlooWorksScraper

        return WaterlooWorksScraper
    if name == "ResumeMatcher":
        from .matcher import ResumeMatcher

        return ResumeMatcher
    if name == "CoverLetterGenerator":
        from .cover_letter_generator import CoverLetterGenerator

        return CoverLetterGenerator
    if name == "CoverLetterUploader":
        from .cover_letter_generator import CoverLetterUploader

        return CoverLetterUploader
    if name == "FilterEngine":
        from .filter_engine import FilterEngine

        return FilterEngine
    if name == "JobAnalyzer":
        from .pipeline import JobAnalyzer

        return JobAnalyzer
    raise AttributeError(name)
