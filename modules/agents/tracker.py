"""Token usage tracking for AI agents"""

import os
import json
from typing import Dict, Optional
from datetime import datetime


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
    
    def __init__(self, log_path: Optional[str] = None):
        if log_path is None:
            from ..config import load_app_config
            config = load_app_config()
            log_path = config.get("paths", {}).get("token_usage_log", "data/token_usage.json")
        self.log_path = log_path
        self.usage_log = self._load_log()
    
    def _load_log(self) -> Dict:
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {"sessions": [], "total_by_agent": {}}
        return {"sessions": [], "total_by_agent": {}}
    
    def _save_log(self):
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
