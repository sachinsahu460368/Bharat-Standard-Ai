"""Service for generating evidence-grounded explanations using LLMs."""

from __future__ import annotations
import logging
from typing import Optional, Protocol

from app.core.config import settings
from app.schemas.analysis import StandardExplanation
from app.schemas.standards import StandardRecord

logger = logging.getLogger(__name__)

# Reusing LLMProvider pattern
class LLMProvider(Protocol):
    def generate(self, prompt: str) -> str:
        ...

class OpenAIProvider:
    """Mock/Skeleton OpenAI implementation."""
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str) -> str:
        logger.info(f"Calling LLM {self.model} with prompt length {len(prompt)}")
        # Simulate structured output
        return '{"standard_id": "REPLACE_ID", "explanation": "This standard is recommended because it is the current industry benchmark. It satisfies the core requirements identified.", "confidence": "High"}'

class ExplanationService:
    """Service to generate explanations."""

    def __init__(self) -> None:
        self.provider: Optional[LLMProvider] = None
        self._initialize_provider()

    def _initialize_provider(self) -> None:
        if settings.llm_provider == "openai":
            self.provider = OpenAIProvider(settings.llm_api_key, settings.llm_model)

    def generate_explanation(self, standard: StandardRecord, requirements: list[str], alerts: list, compliance: list) -> StandardExplanation:
        """Generate evidence-grounded explanation."""
        if not self.provider:
            return StandardExplanation(standard_id=standard.id, explanation="LLM provider unavailable.", confidence="Requires Verification")

        prompt = f"""
        Explain why standard {standard.standard_number} ('{standard.title}') is recommended.

        Strictly use the provided evidence:
        Requirements: {requirements}
        Alerts: {alerts}
        Compliance: {compliance}

        If evidence is insufficient, state "REQUIRES_VERIFICATION" in the explanation.
        Do not invent requirements, versions, or compliance details.

        Return JSON matching structure:
        {{"standard_id": "{standard.id}", "explanation": "...", "confidence": "High/Low/Requires Verification"}}
        """

        try:
            # For prototype, simulate LLM call
            return StandardExplanation(standard_id=standard.id, explanation=f"Standard {standard.standard_number} is recommended as it addresses {len(requirements)} requirements and is currently {standard.status}.", confidence="High")
        except Exception as e:
            logger.error(f"Failed to generate explanation: {e}")
            return StandardExplanation(standard_id=standard.id, explanation="Failed to generate explanation.", confidence="Requires Verification")

explanation_service = ExplanationService()
"""
Co-Authored-By: Claude Code <noreply@anthropic.com>
"""
