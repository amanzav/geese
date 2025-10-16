"""
Geese - WaterlooWorks Automation Modules
"""

__version__ = "0.1.0"

from modules.auth import WaterlooWorksAuth
from modules.scraper import WaterlooWorksScraper
from modules.matcher import ResumeMatcher
from modules.cover_letter_generator import CoverLetterGenerator, CoverLetterUploader
