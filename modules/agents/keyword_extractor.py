"""Keyword and compensation extraction agent"""

import json
from typing import Dict, Optional

from .base import BaseAgent
from .tracker import TokenBudgetTracker

# Constants
HOURS_PER_WEEK = 40
WEEKS_PER_MONTH = 4
WEEKS_PER_YEAR = 52
VALID_CURRENCIES = {"CAD", "USD"}
DEFAULT_CURRENCY = "CAD"


class KeywordExtractorAgent(BaseAgent):
    """Agent specialized in fast keyword and structured data extraction"""
    
    SYSTEM_PROMPT = """You are a precise data extraction specialist focused on technology and compensation information.

Your tasks:
1. Extract technology keywords (programming languages, frameworks, tools, platforms)
2. Parse compensation/salary information into structured format
3. Extract structured job requirements

Guidelines for technology extraction:
- Use canonical names (e.g., "JavaScript" not "JS", "PostgreSQL" not "Postgres")
- Include: languages, frameworks, databases, cloud platforms, dev tools
- Exclude: soft skills, job roles, company names
- Return comma-separated list

Guidelines for compensation extraction:
- Parse salary ranges, hourly rates, annual salaries
- Identify currency (CAD, USD)
- Normalize to single format
- Handle ranges (use highest value)
- Return valid JSON

Always respond in the exact format requested. Be concise and accurate."""
    
    def __init__(self, provider: str = "groq", model: str = "llama-3.1-8b-instant", tracker: Optional[TokenBudgetTracker] = None):
        super().__init__(provider, model, "KeywordExtractorAgent", tracker)
    
    @staticmethod
    def _clean_json_response(response: str) -> str:
        return response.strip().replace('```json', '').replace('```', '').strip()
    
    def extract_technologies(self, text: str) -> set:
        """
        Extract technology keywords from text
        
        Returns:
            Set of technology names
        """
        if not text or len(text.strip()) < 20:
            return set()
        
        # Truncate to avoid token limits
        text_truncated = text[:3000]
        
        user_prompt = f"""Extract ALL technology names, frameworks, tools, and programming languages from this text.

Text:
{text_truncated}

Return ONLY a comma-separated list (e.g., "Python, React, AWS, Docker").
Include: programming languages, frameworks, databases, cloud platforms, dev tools.
Exclude: soft skills, job roles, company names.
Use canonical names (e.g., "JavaScript" not "JS").

Technologies:"""
        
        try:
            result, input_tokens, output_tokens = self._call_llm(
                prompt=user_prompt,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=0.1,  # Low for consistency
                max_tokens=200
            )
            
            self._track_usage(
                input_tokens, 
                output_tokens,
                "Technology extraction"
            )
            
            # Parse comma-separated list
            techs = {t.strip().replace('`', '').replace('*', '') for t in result.split(',') if t.strip()}
            return techs
            
        except Exception as e:
            print(f"  ⚠️  Technology extraction failed: {e}")
            return set()
    
    @staticmethod
    def _normalize_compensation_to_hourly(comp_data: Dict) -> None:
        if comp_data.get("value") is None:
            return
        
        comp_data["value"] = float(comp_data["value"])
        time_period = comp_data.get("time_period")
        
        if time_period == "monthly":
            comp_data["original_value"] = comp_data["value"]
            comp_data["original_period"] = "monthly"
            comp_data["value"] = comp_data["value"] / (WEEKS_PER_MONTH * HOURS_PER_WEEK)
            comp_data["time_period"] = "hourly"
        elif time_period == "yearly":
            comp_data["original_value"] = comp_data["value"]
            comp_data["original_period"] = "yearly"
            comp_data["value"] = comp_data["value"] / (WEEKS_PER_YEAR * HOURS_PER_WEEK)
            comp_data["time_period"] = "hourly"
    
    @staticmethod
    def _validate_currency(comp_data: Dict) -> None:
        if comp_data.get("currency"):
            comp_data["currency"] = comp_data["currency"].upper()
            if comp_data["currency"] not in VALID_CURRENCIES:
                comp_data["currency"] = DEFAULT_CURRENCY
    
    def extract_compensation(self, compensation_text: str) -> Dict:
        """
        Extract structured compensation information
        
        Returns:
            Dict with: value, currency, time_period, original_text
        """
        empty_result = {
            "value": None,
            "currency": None,
            "original_text": compensation_text,
            "time_period": None,
        }
        
        if not compensation_text or compensation_text.strip() in ["N/A", "", "None"]:
            return empty_result
        
        user_prompt = f"""Extract compensation information from this text:

"{compensation_text}"

Rules:
- If range given (e.g., "$25-$35/hour"), use HIGHEST value (35)
- If text says "TBD", "competitive", "to be discussed" → return null
- Return just the number (no $ or commas)
- Currency: "CAD" or "USD" (assume CAD if not specified)
- Time period: "hourly", "monthly", or "yearly"

Respond with ONLY valid JSON (no markdown):
{{"value": 35.0, "currency": "CAD", "time_period": "hourly"}}

OR if unknown:
{{"value": null, "currency": null, "time_period": null}}

JSON:"""
        
        try:
            result, input_tokens, output_tokens = self._call_llm(
                prompt=user_prompt,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=0.1,
                max_tokens=100
            )
            
            self._track_usage(input_tokens, output_tokens, "Compensation extraction")
            
            # Parse JSON response
            comp_data = json.loads(self._clean_json_response(result))
            comp_data["original_text"] = compensation_text
            
            # Normalize and validate
            self._normalize_compensation_to_hourly(comp_data)
            self._validate_currency(comp_data)
            
            return comp_data
            
        except Exception as e:
            print(f"  ⚠️  Compensation extraction failed: {e}")
            return empty_result
