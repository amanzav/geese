"""
LLM Assistant Module
Handles LLM-based tasks like compensation extraction using specialized agents
"""

import os
from typing import Dict
from dotenv import load_dotenv
from .config import load_app_config
from .agents import AgentFactory

# Load environment variables
load_dotenv()


class CompensationExtractor:
    """Extract and normalize compensation information from job postings using LLM agents"""

    def __init__(self, provider: str = "groq"):
        """
        Initialize compensation extractor

        Args:
            provider: LLM provider (deprecated - now uses agent configuration)
        """
        self.config = load_app_config()
        
        # Initialize agent factory
        agent_config = {
            "keyword_extractor_agent": {
                "provider": self.config.agents.keyword_extractor_agent.get("provider", "groq"),
                "model": self.config.agents.keyword_extractor_agent.get("model", "llama-3.1-8b-instant")
            }
        }
        
        self.factory = AgentFactory(
            config=agent_config,
            enable_tracking=self.config.agents.enable_token_tracking
        )
        
        self.agent = self.factory.get_keyword_extractor_agent()
        print(f"✅ CompensationExtractor initialized with {self.agent.provider}/{self.agent.model}")

    def extract_compensation(self, compensation_text: str) -> Dict:
        """
        Extract compensation information from text using LLM agent

        Args:
            compensation_text: Raw compensation text from job posting

        Returns:
            Dict with keys:
                - value: Single numeric value (hourly rate) or None
                - currency: "CAD", "USD", or None
                - original_text: Original text for reference
                - time_period: Always "hourly" after conversion
                - original_value: Original value if converted
                - original_period: Original period if converted
        """
        # Use the agent's extraction method (handles all the logic)
        return self.agent.extract_compensation(compensation_text)

    def format_compensation(self, comp_data: Dict) -> str:
        """
        Format compensation data for display

        Args:
            comp_data: Compensation dict from extract_compensation

        Returns:
            Formatted string like "$35.00/hour CAD" or "$40.00/hour CAD (was $83,200/year)" for conversions
        """
        if not comp_data or comp_data.get("value") is None:
            return "TBD"

        value = comp_data["value"]
        currency = comp_data.get("currency", "CAD")

        # Format hourly value with 2 decimal places
        formatted_value = f"${value:,.2f}/hour {currency}"

        # Add original value if it was converted
        if comp_data.get("original_value") and comp_data.get("original_period"):
            original_value = comp_data["original_value"]
            original_period = comp_data["original_period"]

            if original_period == "monthly":
                formatted_value += f" (was ${original_value:,.2f}/month)"
            elif original_period == "yearly":
                formatted_value += f" (was ${original_value:,.0f}/year)"

        return formatted_value


def extract_compensation_from_text(text: str, provider: str = "groq") -> Dict:
    """
    Convenience function to extract compensation from text

    Args:
        text: Compensation text from job posting
        provider: LLM provider to use (deprecated - uses agent config)

    Returns:
        Compensation dict
    """
    extractor = CompensationExtractor(provider=provider)
    return extractor.extract_compensation(text)
