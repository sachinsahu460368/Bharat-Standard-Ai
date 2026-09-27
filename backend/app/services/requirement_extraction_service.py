
"""Service for extracting structured requirements from procurement text using LLMs."""

from __future__ import annotations

import httpx
import logging
import json
import re
import time
from typing import Optional, Protocol

from pydantic import ValidationError

from app.core.config import settings
from app.schemas.analysis import ExtractedRequirements
from app.services.local_extraction_service import LocalRequirementExtractor

logger = logging.getLogger(__name__)


def _strip_markdown_fences(text: str) -> str:
    """Remove markdown code fences (```json ... ```) wrapping JSON output.

    Some LLM models return JSON wrapped in markdown fences even when
    instructed not to (or when responseMimeType is not honoured).
    This normalises the text so json.loads() can succeed.
    """
    stripped = text.strip()
    if stripped.startswith("```"):
        # Remove opening fence line (```json, ```JSON, or bare ```)
        stripped = re.sub(r"^```[a-zA-Z]*\n?", "", stripped, count=1)
        # Remove closing fence
        stripped = re.sub(r"\n?```\s*$", "", stripped)
    return stripped.strip()


class LLMProvider(Protocol):
    """Protocol for LLM providers."""
    def generate(self, prompt: str) -> str:
        ...

class OpenAIProvider:
    """Real OpenAI implementation."""
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"

    def generate(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that extracts structured information from procurement documents."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"}
        }

        with httpx.Client() as client:
            response = client.post(self.api_url, headers=headers, json=data, timeout=30.0)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]


class GeminiProvider:
    """Google Gemini API implementation via REST (httpx)."""

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.api_url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        )

    def generate(self, prompt: str) -> str:
        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}
        data = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0,
                "responseMimeType": "application/json",
            },
            "systemInstruction": {
                "parts": [
                    {
                        "text": (
                            "You are a helpful assistant that extracts structured "
                            "information from procurement documents. You must return "
                            "ONLY valid JSON matching the requested schema."
                        )
                    }
                ]
            },
        }

        # Simple retry for 429
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with httpx.Client() as client:
                    response = client.post(
                        self.api_url,
                        headers=headers,
                        params=params,
                        json=data,
                        timeout=60.0,
                    )
                    if response.status_code == 429:
                        if attempt < max_retries - 1:
                            logger.warning("Gemini API rate limited (429), retrying in %d seconds...", 2 ** attempt)
                            time.sleep(2 ** attempt + 1)
                            continue
                    response.raise_for_status()
                    result = response.json()
                    break
            except httpx.HTTPStatusError as e:
                # Log the actual API error body (safe — it never contains the key)
                error_body = ""
                try:
                    error_body = e.response.json().get("error", {}).get("message", "")
                except Exception:
                    error_body = e.response.text[:300]
                logger.error(
                    "Gemini API HTTP error %s: %s",
                    e.response.status_code,
                    error_body,
                )
                raise
            except httpx.RequestError as e:
                logger.error("Gemini API network error: %s", type(e).__name__)
                raise
        else:
            # If we exhausted retries
            raise httpx.HTTPStatusError("Max retries exceeded for 429", request=None, response=response)

        # Navigate Gemini response structure:
        # { "candidates": [ { "content": { "parts": [ { "text": "..." } ] } } ] }
        try:
            text = result["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as e:
            logger.error("Unexpected Gemini response structure: %s", type(e).__name__)
            raise ValueError("Gemini returned an unexpected response format")

        return text


class RequirementExtractionService:
    """Service to extract structured procurement requirements."""

    EXTRACTION_PROMPT = """Extract procurement requirements from the text below.
Return ONLY a valid JSON object. No markdown, no explanation, no code fences.

Required fields — use null for unknown strings, [] for unknown lists.
Use these EXACT field names:
- "product": string or null
- "category": string or null
- "quantity": string or null
- "application": string or null
- "environment": string or null
- "technical_requirements": list of strings
- "materials": list of strings
- "performance_requirements": list of strings
- "safety_requirements": list of strings
- "testing_requirements": list of strings
- "certification_mentions": list of strings
- "referenced_standards": list of strings

Rules:
- Only extract what is explicitly stated in the text.
- Do NOT invent, fabricate, or assume any information.
- If a field has no corresponding information in the text, use null (strings) or [] (lists).

Text:
{text}
"""

    def __init__(self) -> None:
        self.provider: Optional[LLMProvider] = None
        self._initialize_provider()
        self.local_extractor = LocalRequirementExtractor()

    def _initialize_provider(self) -> None:
        if settings.llm_provider == "openai":
            self.provider = OpenAIProvider(settings.llm_api_key, settings.llm_model)
            logger.info("LLM provider initialized: openai (%s)", settings.llm_model)
        elif settings.llm_provider == "gemini":
            self.provider = GeminiProvider(settings.llm_api_key, settings.llm_model)
            logger.info("LLM provider initialized: gemini (%s)", settings.llm_model)
        else:
            logger.warning("Unsupported LLM provider: %s", settings.llm_provider)

    def extract(self, text: str) -> ExtractedRequirements:
        """Extract requirements from raw procurement text."""
        if not self.provider:
            logger.warning("No LLM provider initialized. Using local fallback.")
            return self.local_extractor.extract(text)

        prompt = self.EXTRACTION_PROMPT.format(text=text[:5000])

        try:
            raw_response = self.provider.generate(prompt)
            logger.info("LLM raw response: %r", raw_response) # DIAGNOSTIC
        except Exception as e:
            logger.error(
                "LLM provider call failed (%s): %s. Using local fallback.",
                type(e).__name__,
                str(e)[:200],
            )
            return self.local_extractor.extract(text)

        # Normalise: strip markdown fences if the model wrapped its JSON output
        cleaned_response = _strip_markdown_fences(raw_response)

        try:
            data = json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            logger.error(
                "LLM returned invalid JSON: %s. Using local fallback. Response preview: %r",
                e,
                cleaned_response[:200],
            )
            return self.local_extractor.extract(text)

        if not data:
            logger.warning("LLM returned empty JSON! Using local fallback.")
            return self.local_extractor.extract(text)

        try:
            requirements = ExtractedRequirements(**data)
        except ValidationError as e:
            logger.error("Pydantic validation failed on LLM output: %s. Using local fallback.", e.errors()) # Improved log
            return self.local_extractor.extract(text)

        logger.info(
            "Requirement extraction succeeded: product=%s, tech_reqs=%d, ref_stds=%d",
            requirements.product,
            len(requirements.technical_requirements),
            len(requirements.referenced_standards),
        )
        return requirements

# Module-level singleton
requirement_extraction_service = RequirementExtractionService()
