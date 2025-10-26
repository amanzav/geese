"""
LLM Assistant Module
Handles LLM-based tasks like compensation extraction
"""

import os
import json
import re
from typing import Optional, Dict
from dotenv import load_dotenv
from .config import load_app_config

# Load environment variables
load_dotenv()


class CompensationExtractor:
    """Extract and normalize compensation information from job postings using LLM"""

    def __init__(self, provider: str = "gemini"):
        """
        Initialize compensation extractor

        Args:
            provider: LLM provider ("gemini" or "openai")
        """
        self.provider = provider.lower()
        self.client = None
        self.config = load_app_config()
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the LLM client based on provider"""
        if self.provider == "gemini":
            try:
                import google.generativeai as genai

                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    raise ValueError(
                        "GEMINI_API_KEY not found in environment variables"
                    )
                genai.configure(api_key=api_key)
                model_name = self.config.matcher.llm_models.get("gemini_lite", "gemini-2.0-flash-lite")
                self.client = genai.GenerativeModel(model_name)
                print("✅ Gemini API initialized")
            except ImportError:
                raise ImportError(
                    "google-generativeai package not installed. Run: pip install google-generativeai"
                )
            except Exception as e:
                raise Exception(f"Failed to initialize Gemini: {e}")

        elif self.provider == "openai":
            try:
                from openai import OpenAI

                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError(
                        "OPENAI_API_KEY not found in environment variables"
                    )
                self.client = OpenAI(api_key=api_key)
                print("✅ OpenAI API initialized")
            except ImportError:
                raise ImportError(
                    "openai package not installed. Run: pip install openai"
                )
            except Exception as e:
                raise Exception(f"Failed to initialize OpenAI: {e}")
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def extract_compensation(self, compensation_text: str) -> Dict:
        """
        Extract compensation information from text using LLM

        Args:
            compensation_text: Raw compensation text from job posting

        Returns:
            Dict with keys:
                - value: Single numeric value (highest if range) or None
                - currency: "CAD", "USD", or None
                - original_text: Original text for reference
                - time_period: "hourly", "monthly", "yearly", or None
        """
        if not compensation_text or compensation_text.strip() in ["N/A", "", "None"]:
            return {
                "value": None,
                "currency": None,
                "original_text": compensation_text,
                "time_period": None,
            }

        prompt = f"""
You are an expert at extracting compensation information from job postings.

Given the following compensation text, extract:
1. A SINGLE numeric compensation value (if there's a range, use the HIGHEST value)
2. The currency (CAD or USD)
3. The time period (hourly, monthly, or yearly)

Rules:
- If text says "to be discussed", "TBD", "competitive", or similar → return null for value
- If there's a range (e.g., "$25-$35/hour") → return the HIGHEST value (35)
- Always return just the number (no dollar signs, no commas)
- Currency should be "CAD" or "USD" (assume CAD if not specified)
- Time period should be "hourly", "monthly", or "yearly"

Text to analyze:
"{compensation_text}"

Respond ONLY with valid JSON in this exact format (no markdown, no explanation):
{{"value": 35.0, "currency": "CAD", "time_period": "hourly"}}

OR if compensation is unknown:
{{"value": null, "currency": null, "time_period": null}}
"""

        try:
            if self.provider == "gemini":
                response = self.client.generate_content(prompt)
                response_text = response.text.strip()
            else:  # openai
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=100,
                )
                response_text = response.choices[0].message.content.strip()

            # Clean up response (remove markdown code blocks if present)
            response_text = re.sub(r"```json\s*|\s*```", "", response_text).strip()

            # Parse JSON response
            result = json.loads(response_text)

            # Add original text
            result["original_text"] = compensation_text

            # Validate and clean the result
            if result.get("value") is not None:
                try:
                    result["value"] = float(result["value"])
                except (ValueError, TypeError):
                    result["value"] = None

            # Ensure currency is uppercase
            if result.get("currency"):
                result["currency"] = result["currency"].upper()
                if result["currency"] not in ["CAD", "USD"]:
                    result["currency"] = "CAD"  # Default to CAD

            # Validate time_period
            if result.get("time_period"):
                result["time_period"] = result["time_period"].lower()
                if result["time_period"] not in ["hourly", "monthly", "yearly"]:
                    result["time_period"] = None

            # Convert to hourly rate
            # Assumptions: 40 hours/week, 4 weeks/month, 52 weeks/year
            if result.get("value") is not None and result.get("time_period"):
                original_value = result["value"]
                original_period = result["time_period"]

                if original_period == "monthly":
                    # Monthly to hourly: divide by (4 weeks * 40 hours)
                    result["value"] = original_value / (4 * 40)
                    result["original_value"] = original_value
                    result["original_period"] = "monthly"
                elif original_period == "yearly":
                    # Yearly to hourly: divide by (52 weeks * 40 hours)
                    result["value"] = original_value / (52 * 40)
                    result["original_value"] = original_value
                    result["original_period"] = "yearly"

                # Always set time_period to hourly
                result["time_period"] = "hourly"

            return result

        except json.JSONDecodeError as e:
            print(f"  ⚠️  Failed to parse LLM response as JSON: {e}")
            print(f"  Response was: {response_text[:200]}")
            return {
                "value": None,
                "currency": None,
                "original_text": compensation_text,
                "time_period": None,
            }
        except Exception as e:
            print(f"  ⚠️  Error extracting compensation: {e}")
            return {
                "value": None,
                "currency": None,
                "original_text": compensation_text,
                "time_period": None,
            }

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


def extract_compensation_from_text(text: str, provider: str = "gemini") -> Dict:
    """
    Convenience function to extract compensation from text

    Args:
        text: Compensation text from job posting
        provider: LLM provider to use

    Returns:
        Compensation dict
    """
    extractor = CompensationExtractor(provider=provider)
    return extractor.extract_compensation(text)
