"""Cover letter generation agent"""

import time
from typing import Optional

from .base import BaseAgent
from .tracker import TokenBudgetTracker


class CoverLetterAgent(BaseAgent):
    """Agent specialized in generating high-quality cover letters"""
    
    SYSTEM_PROMPT = """You are an expert cover letter writer with deep knowledge of professional communication and job applications.

Your goal is to write compelling, personalized cover letters that:
- Highlight the candidate's most relevant skills and experiences for the specific role
- Demonstrate genuine enthusiasm and cultural fit
- Use professional yet warm language
- Are concise (100-400 words) and scannable
- Follow proper business letter structure

Guidelines:
- Start strong with why you're excited about THIS specific role/company
- Include 2-3 concrete examples of relevant experience from the resume
- Show you understand the company/role (reference job description keywords naturally)
- End with a confident call-to-action
- Avoid generic phrases like "I am writing to apply" or "perfect fit"
- Use active voice and strong action verbs
- Be authentic and human, not robotic"""
    
    def __init__(self, provider: str = "gemini", model: str = "gemini-1.5-flash", tracker: Optional[TokenBudgetTracker] = None):
        super().__init__(provider, model, "CoverLetterAgent", tracker)
    
    def generate_cover_letter(
        self,
        company: str,
        job_title: str,
        job_description: str,
        resume_text: str,
        max_retries: int = 3
    ) -> Optional[str]:
        """
        Generate a personalized cover letter
        
        Returns:
            Generated cover letter text (100-400 words) or None if failed
        """
        user_prompt = f"""Write a professional cover letter for this position:

**Company:** {company}
**Position:** {job_title}

**Job Description:**
{job_description[:2000]}  

**My Resume Highlights:**
{resume_text[:1500]}

Requirements:
- Length: 100-400 words (strict requirement)
- Format: 3-4 paragraphs
- Do NOT include my address, their address, or date
- Do NOT include "Dear Hiring Manager," or signature - I'll add those
- Focus on: relevant experience, enthusiasm for role, value I bring

Write ONLY the body paragraphs of the cover letter."""
        
        for attempt in range(max_retries):
            try:
                result, input_tokens, output_tokens = self._call_llm(
                    prompt=user_prompt,
                    system_prompt=self.SYSTEM_PROMPT,
                    temperature=0.7,  # Higher for creativity
                    max_tokens=600
                )
                
                self._track_usage(
                    input_tokens, 
                    output_tokens,
                    f"Cover letter: {company} - {job_title}"
                )
                
                # Validate word count
                word_count = len(result.split())
                if 100 <= word_count <= 400:
                    return result.strip()
                
                # Retry if too short/long
                if attempt < max_retries - 1:
                    print(f"      ⚠️  Word count {word_count}, retrying...")
                    time.sleep(0.5)
                
            except Exception as e:
                print(f"      ⚠️  Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
        
        return None
