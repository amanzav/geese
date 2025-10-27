"""Document requirement classification agent"""

import json
from typing import Optional

from .base import BaseAgent
from .tracker import TokenBudgetTracker
from .keyword_extractor import KeywordExtractorAgent


class DocumentClassifierAgent(BaseAgent):
    """Agent specialized in fast document requirement classification"""
    
    SYSTEM_PROMPT = """You are a precise binary classifier for job application requirements.

Your task is to analyze job postings and determine:
1. If additional documents beyond resume/cover letter are required (transcripts, portfolio, references, etc.)
2. If external application (outside the portal) is required

Guidelines:
- Be conservative: only flag as "yes" if clearly stated
- Focus on explicit requirements, not suggestions
- Return concise yes/no with brief reasoning
- Extract relevant URLs if mentioned

Always respond in valid JSON format."""
    
    def __init__(self, provider: str = "groq", model: str = "llama-3.1-8b-instant", tracker: Optional[TokenBudgetTracker] = None):
        super().__init__(provider, model, "DocumentClassifierAgent", tracker)
    
    def _detect_feature(
        self,
        job_text: str,
        feature_name: str,
        prompt_template: str,
        expected_key: str,
        url_key: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        if not job_text or job_text == "N/A":
            return (False, None)
        
        try:
            result, input_tokens, output_tokens = self._call_llm(
                prompt=prompt_template.format(job_text=job_text[:1500]),
                system_prompt=self.SYSTEM_PROMPT,
                temperature=0.1,
                max_tokens=150
            )
            
            self._track_usage(input_tokens, output_tokens, feature_name)
            
            # Parse JSON
            data = json.loads(KeywordExtractorAgent._clean_json_response(result))
            requires = data.get(expected_key, False)
            extra_info = data.get(url_key) if (url_key and requires) else data.get("reason") if requires else None
            
            return (requires, extra_info)
            
        except Exception as e:
            print(f"  ⚠️  {feature_name} failed: {e}")
            return (False, None)
    
    def detect_additional_documents(self, job_text: str) -> tuple[bool, Optional[str]]:
        """
        Detect if job requires additional documents beyond resume/cover letter
        
        Returns:
            (requires_extra_docs, reason)
        """
        prompt = """Analyze if this job requires additional documents beyond resume and cover letter.

Job Text:
{job_text}

Look for requirements like:
- Transcripts (official/unofficial)
- Portfolio, GitHub, or work samples
- Writing samples or code samples
- References or reference letters
- Certificates or security clearance
- Any other documents

Respond with ONLY valid JSON (no markdown):
{{"requires_extra_docs": true/false, "reason": "brief explanation"}}

JSON:"""
        
        return self._detect_feature(
            job_text,
            "Additional docs detection",
            prompt,
            "requires_extra_docs"
        )
    
    def detect_external_application(self, job_text: str) -> tuple[bool, Optional[str]]:
        """
        Detect if job requires external application
        
        Returns:
            (requires_external, url)
        """
        prompt = """Analyze if this job requires applying externally (outside this portal).

Job Text:
{job_text}

Look for phrases like:
- "Apply directly at..."
- "Apply on our website"
- "Use this link to apply"
- External job board URLs (Greenhouse, Lever, Workday, etc.)

Respond with ONLY valid JSON (no markdown):
{{"requires_external": true/false, "url": "http://..." or null}}

JSON:"""
        
        return self._detect_feature(
            job_text,
            "External application detection",
            prompt,
            "requires_external",
            "url"
        )
