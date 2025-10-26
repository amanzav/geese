"""
AI Agents Module - Centralized LLM agent management for cost optimization
"""

import os
import json
import time
from typing import Dict, List, Optional, Any, Literal
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class TokenBudgetTracker:
    """Track token usage and costs across different AI providers"""
    
    # Approximate pricing (per 1M tokens) - update as needed
    PRICING = {
        "groq": {
            "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
            "mixtral-8x7b-instant": {"input": 0.24, "output": 0.24},
        },
        "gemini": {
            "gemini-2.0-flash-exp": {"input": 0.0, "output": 0.0},  # Free tier
            "gemini-2.0-flash-lite": {"input": 0.075, "output": 0.30},
            "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
        },
        "openai": {
            "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        }
    }
    
    def __init__(self, log_path: str = "data/token_usage.json"):
        self.log_path = log_path
        self.usage_log = self._load_log()
    
    def _load_log(self) -> Dict:
        """Load existing usage log"""
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {"sessions": [], "total_by_agent": {}}
        return {"sessions": [], "total_by_agent": {}}
    
    def _save_log(self):
        """Save usage log to disk"""
        try:
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            with open(self.log_path, 'w', encoding='utf-8') as f:
                json.dump(self.usage_log, f, indent=2)
        except Exception as e:
            print(f"⚠️  Failed to save token usage log: {e}")
    
    def track_usage(
        self, 
        agent_name: str, 
        provider: str, 
        model: str,
        input_tokens: int,
        output_tokens: int,
        task_description: str = ""
    ):
        """Track token usage for an agent call"""
        # Calculate cost
        cost = 0.0
        if provider in self.PRICING and model in self.PRICING[provider]:
            pricing = self.PRICING[provider][model]
            cost = (
                (input_tokens / 1_000_000) * pricing["input"] +
                (output_tokens / 1_000_000) * pricing["output"]
            )
        
        # Log the usage
        session = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "provider": provider,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost_usd": round(cost, 6),
            "task": task_description
        }
        
        self.usage_log["sessions"].append(session)
        
        # Update totals by agent
        if agent_name not in self.usage_log["total_by_agent"]:
            self.usage_log["total_by_agent"][agent_name] = {
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "call_count": 0
            }
        
        totals = self.usage_log["total_by_agent"][agent_name]
        totals["total_tokens"] += input_tokens + output_tokens
        totals["total_cost_usd"] += cost
        totals["call_count"] += 1
        
        self._save_log()
    
    def get_summary(self) -> Dict:
        """Get usage summary across all agents"""
        total_tokens = sum(
            agent["total_tokens"] 
            for agent in self.usage_log["total_by_agent"].values()
        )
        total_cost = sum(
            agent["total_cost_usd"]
            for agent in self.usage_log["total_by_agent"].values()
        )
        
        return {
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "by_agent": self.usage_log["total_by_agent"],
            "session_count": len(self.usage_log["sessions"])
        }


class BaseAgent:
    """Base class for all AI agents"""
    
    def __init__(
        self, 
        provider: str,
        model: str,
        agent_name: str,
        tracker: Optional[TokenBudgetTracker] = None
    ):
        self.provider = provider
        self.model = model
        self.agent_name = agent_name
        self.tracker = tracker
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the appropriate LLM client"""
        if self.provider == "groq":
            self._initialize_groq()
        elif self.provider == "gemini":
            self._initialize_gemini()
        elif self.provider == "openai":
            self._initialize_openai()
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _initialize_groq(self):
        """Initialize Groq client"""
        try:
            from groq import Groq
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment variables")
            self.client = Groq(api_key=api_key)
            print(f"✅ {self.agent_name}: Groq initialized ({self.model})")
        except ImportError:
            raise ImportError("groq package not installed. Run: pip install groq")
    
    def _initialize_gemini(self):
        """Initialize Gemini client"""
        try:
            import google.generativeai as genai
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(self.model)
            print(f"✅ {self.agent_name}: Gemini initialized ({self.model})")
        except ImportError:
            raise ImportError("google-generativeai package not installed")
    
    def _initialize_openai(self):
        """Initialize OpenAI client"""
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            self.client = OpenAI(api_key=api_key)
            print(f"✅ {self.agent_name}: OpenAI initialized ({self.model})")
        except ImportError:
            raise ImportError("openai package not installed")
    
    def _call_llm(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1000
    ) -> tuple[str, int, int]:
        """
        Call the LLM and return (response_text, input_tokens, output_tokens)
        """
        input_tokens = 0
        output_tokens = 0
        
        if self.provider == "groq":
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            result = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            
        elif self.provider == "gemini":
            # Gemini doesn't support system prompts directly, prepend to user message
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
            
            response = self.client.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            result = response.text
            # Gemini doesn't always provide token counts, estimate if needed
            try:
                input_tokens = response.usage_metadata.prompt_token_count
                output_tokens = response.usage_metadata.candidates_token_count
            except:
                # Rough estimate: ~4 chars per token
                input_tokens = len(full_prompt) // 4
                output_tokens = len(result) // 4
            
        elif self.provider == "openai":
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            result = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
        
        return result, input_tokens, output_tokens
    
    def _track_usage(
        self, 
        input_tokens: int, 
        output_tokens: int,
        task_description: str = ""
    ):
        """Track token usage if tracker is available"""
        if self.tracker:
            self.tracker.track_usage(
                agent_name=self.agent_name,
                provider=self.provider,
                model=self.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                task_description=task_description
            )


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
    
    def extract_compensation(self, compensation_text: str) -> Dict:
        """
        Extract structured compensation information
        
        Returns:
            Dict with: value, currency, time_period, original_text
        """
        if not compensation_text or compensation_text.strip() in ["N/A", "", "None"]:
            return {
                "value": None,
                "currency": None,
                "original_text": compensation_text,
                "time_period": None,
            }
        
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
            
            self._track_usage(
                input_tokens,
                output_tokens,
                "Compensation extraction"
            )
            
            # Clean and parse JSON
            result = result.strip().replace('```json', '').replace('```', '').strip()
            comp_data = json.loads(result)
            
            # Add original text
            comp_data["original_text"] = compensation_text
            
            # Validate and convert to hourly
            if comp_data.get("value") is not None:
                comp_data["value"] = float(comp_data["value"])
                
                # Convert to hourly rate
                if comp_data.get("time_period") == "monthly":
                    comp_data["original_value"] = comp_data["value"]
                    comp_data["original_period"] = "monthly"
                    comp_data["value"] = comp_data["value"] / (4 * 40)  # 4 weeks * 40 hours
                elif comp_data.get("time_period") == "yearly":
                    comp_data["original_value"] = comp_data["value"]
                    comp_data["original_period"] = "yearly"
                    comp_data["value"] = comp_data["value"] / (52 * 40)  # 52 weeks * 40 hours
                
                comp_data["time_period"] = "hourly"
            
            # Ensure currency is valid
            if comp_data.get("currency"):
                comp_data["currency"] = comp_data["currency"].upper()
                if comp_data["currency"] not in ["CAD", "USD"]:
                    comp_data["currency"] = "CAD"
            
            return comp_data
            
        except Exception as e:
            print(f"  ⚠️  Compensation extraction failed: {e}")
            return {
                "value": None,
                "currency": None,
                "original_text": compensation_text,
                "time_period": None,
            }


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
    
    def detect_additional_documents(self, job_text: str) -> tuple[bool, Optional[str]]:
        """
        Detect if job requires additional documents beyond resume/cover letter
        
        Returns:
            (requires_extra_docs, reason)
        """
        if not job_text or job_text == "N/A":
            return (False, None)
        
        user_prompt = f"""Analyze if this job requires additional documents beyond resume and cover letter.

Job Text:
{job_text[:1500]}

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
        
        try:
            result, input_tokens, output_tokens = self._call_llm(
                prompt=user_prompt,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=0.1,
                max_tokens=100
            )
            
            self._track_usage(
                input_tokens,
                output_tokens,
                "Additional docs detection"
            )
            
            # Parse JSON
            result = result.strip().replace('```json', '').replace('```', '').strip()
            data = json.loads(result)
            
            requires = data.get("requires_extra_docs", False)
            reason = data.get("reason") if requires else None
            
            return (requires, reason)
            
        except Exception as e:
            print(f"  ⚠️  Document detection failed: {e}")
            return (False, None)
    
    def detect_external_application(self, job_text: str) -> tuple[bool, Optional[str]]:
        """
        Detect if job requires external application
        
        Returns:
            (requires_external, url)
        """
        if not job_text or job_text == "N/A":
            return (False, None)
        
        user_prompt = f"""Analyze if this job requires applying externally (outside this portal).

Job Text:
{job_text[:1500]}

Look for phrases like:
- "Apply directly at..."
- "Apply on our website"
- "Use this link to apply"
- External job board URLs (Greenhouse, Lever, Workday, etc.)

Respond with ONLY valid JSON (no markdown):
{{"requires_external": true/false, "url": "http://..." or null}}

JSON:"""
        
        try:
            result, input_tokens, output_tokens = self._call_llm(
                prompt=user_prompt,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=0.1,
                max_tokens=150
            )
            
            self._track_usage(
                input_tokens,
                output_tokens,
                "External application detection"
            )
            
            # Parse JSON
            result = result.strip().replace('```json', '').replace('```', '').strip()
            data = json.loads(result)
            
            requires = data.get("requires_external", False)
            url = data.get("url") if requires else None
            
            return (requires, url)
            
        except Exception as e:
            print(f"  ⚠️  External application detection failed: {e}")
            return (False, None)


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
        """Load default agent configuration"""
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
    
    def get_cover_letter_agent(self) -> CoverLetterAgent:
        """Get or create cover letter agent"""
        if "cover_letter" not in self._agents:
            config = self.config.get("cover_letter_agent", {})
            self._agents["cover_letter"] = CoverLetterAgent(
                provider=config.get("provider", "gemini"),
                model=config.get("model", "gemini-1.5-flash"),
                tracker=self.tracker
            )
        return self._agents["cover_letter"]
    
    def get_keyword_extractor_agent(self) -> KeywordExtractorAgent:
        """Get or create keyword extractor agent"""
        if "keyword_extractor" not in self._agents:
            config = self.config.get("keyword_extractor_agent", {})
            self._agents["keyword_extractor"] = KeywordExtractorAgent(
                provider=config.get("provider", "groq"),
                model=config.get("model", "llama-3.1-8b-instant"),
                tracker=self.tracker
            )
        return self._agents["keyword_extractor"]
    
    def get_document_classifier_agent(self) -> DocumentClassifierAgent:
        """Get or create document classifier agent"""
        if "document_classifier" not in self._agents:
            config = self.config.get("document_classifier_agent", {})
            self._agents["document_classifier"] = DocumentClassifierAgent(
                provider=config.get("provider", "groq"),
                model=config.get("model", "llama-3.1-8b-instant"),
                tracker=self.tracker
            )
        return self._agents["document_classifier"]
    
    def get_usage_summary(self) -> Dict:
        """Get token usage summary across all agents"""
        if self.tracker:
            return self.tracker.get_summary()
        return {"message": "Tracking disabled"}
    
    def print_usage_summary(self):
        """Print formatted usage summary"""
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
