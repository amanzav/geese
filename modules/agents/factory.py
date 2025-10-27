"""Agent factory for creating and managing AI agents"""

from typing import Dict, Optional, Type, TypeVar

from .tracker import TokenBudgetTracker
from .base import BaseAgent
from .cover_letter import CoverLetterAgent
from .keyword_extractor import KeywordExtractorAgent
from .document_classifier import DocumentClassifierAgent

T = TypeVar('T', bound='BaseAgent')


class AgentFactory:
    """Factory for creating and managing AI agents with unified configuration"""
    
    def __init__(self, config: Optional[Dict] = None, enable_tracking: bool = True):
        """
        Initialize agent factory
        
        Args:
            config: Optional configuration dict with agent settings
            enable_tracking: Whether to track token usage
        """
        self.config = config or self._load_default_config()
        self.tracker = TokenBudgetTracker() if enable_tracking else None
        self._agents: Dict[str, BaseAgent] = {}
    
    def _load_default_config(self) -> Dict:
        return {
            "cover_letter_agent": {
                "provider": "gemini",
                "model": "gemini-1.5-flash"
            },
            "keyword_extractor_agent": {
                "provider": "groq",
                "model": "llama-3.1-8b-instant"
            },
            "document_classifier_agent": {
                "provider": "groq",
                "model": "llama-3.1-8b-instant"
            }
        }
    
    def _get_or_create_agent(
        self,
        agent_key: str,
        agent_class: Type[T],
        config_key: str,
        default_provider: str,
        default_model: str
    ) -> T:
        if agent_key not in self._agents:
            config = self.config.get(config_key, {})
            self._agents[agent_key] = agent_class(
                provider=config.get("provider", default_provider),
                model=config.get("model", default_model),
                tracker=self.tracker
            )
        return self._agents[agent_key]
    
    def get_cover_letter_agent(self) -> CoverLetterAgent:
        return self._get_or_create_agent(
            "cover_letter",
            CoverLetterAgent,
            "cover_letter_agent",
            "gemini",
            "gemini-1.5-flash"
        )
    
    def get_keyword_extractor_agent(self) -> KeywordExtractorAgent:
        return self._get_or_create_agent(
            "keyword_extractor",
            KeywordExtractorAgent,
            "keyword_extractor_agent",
            "groq",
            "llama-3.1-8b-instant"
        )
    
    def get_document_classifier_agent(self) -> DocumentClassifierAgent:
        return self._get_or_create_agent(
            "document_classifier",
            DocumentClassifierAgent,
            "document_classifier_agent",
            "groq",
            "llama-3.1-8b-instant"
        )
    
    def get_usage_summary(self) -> Dict:
        if self.tracker:
            return self.tracker.get_summary()
        return {"message": "Tracking disabled"}
    
    def print_usage_summary(self):
        summary = self.get_usage_summary()
        
        if "message" in summary:
            print(summary["message"])
            return
        
        print("\n" + "="*60)
        print("📊 AI AGENT TOKEN USAGE SUMMARY")
        print("="*60)
        print(f"Total Tokens Used: {summary['total_tokens']:,}")
        print(f"Total Cost: ${summary['total_cost_usd']:.4f}")
        print(f"Total API Calls: {summary['session_count']}")
        print("\nBy Agent:")
        print("-"*60)
        
        for agent_name, stats in summary.get("by_agent", {}).items():
            print(f"\n{agent_name}:")
            print(f"  Tokens: {stats['total_tokens']:,}")
            print(f"  Cost: ${stats['total_cost_usd']:.4f}")
            print(f"  Calls: {stats['call_count']}")
        
        print("="*60 + "\n")
