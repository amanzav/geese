"""Base agent class with LLM client management"""

import os
from typing import Optional
from dotenv import load_dotenv

from .tracker import TokenBudgetTracker

# Load environment variables
load_dotenv()


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
        if self.provider == "groq":
            self._initialize_groq()
        elif self.provider == "gemini":
            self._initialize_gemini()
        elif self.provider == "openai":
            self._initialize_openai()
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _initialize_groq(self):
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
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            self.client = OpenAI(api_key=api_key)
            print(f"✅ {self.agent_name}: OpenAI initialized ({self.model})")
        except ImportError:
            raise ImportError("openai package not installed")
    
    def _build_messages(self, prompt: str, system_prompt: Optional[str] = None) -> list:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages
    
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
        if self.provider in ["groq", "openai"]:
            return self._call_chat_based_llm(prompt, system_prompt, temperature, max_tokens)
        elif self.provider == "gemini":
            return self._call_gemini(prompt, system_prompt, temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _call_chat_based_llm(
        self, 
        prompt: str, 
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> tuple[str, int, int]:
        messages = self._build_messages(prompt, system_prompt)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return (
            response.choices[0].message.content,
            response.usage.prompt_tokens,
            response.usage.completion_tokens
        )
    
    def _call_gemini(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> tuple[str, int, int]:
        # Gemini doesn't support system prompts directly, prepend to user message
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        
        response = self.client.generate_content(full_prompt, generation_config=generation_config)
        result = response.text
        
        # Try to get token counts, estimate if unavailable
        try:
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count
        except AttributeError:
            # Rough estimate: ~4 chars per token
            input_tokens = len(full_prompt) // 4
            output_tokens = len(result) // 4
        
        return result, input_tokens, output_tokens
    
    def _track_usage(
        self, 
        input_tokens: int, 
        output_tokens: int,
        task_description: str = ""
    ):
        if self.tracker:
            self.tracker.track_usage(
                agent_name=self.agent_name,
                provider=self.provider,
                model=self.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                task_description=task_description
            )
