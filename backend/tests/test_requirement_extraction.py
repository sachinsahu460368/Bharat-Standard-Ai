"""Tests for requirement extraction service — OpenAI and Gemini providers."""

import json
import pytest
from unittest.mock import MagicMock, patch

import httpx

from app.schemas.analysis import ExtractedRequirements
from app.services.requirement_extraction_service import (
    GeminiProvider,
    OpenAIProvider,
    RequirementExtractionService,
    _strip_markdown_fences,
)


# ---------------------------------------------------------------------------
# Helper: build a Gemini-shaped HTTP response body
# ---------------------------------------------------------------------------

def _gemini_response_body(text: str) -> dict:
    """Build a dict matching the Gemini generateContent response shape."""
    return {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": text}]
                },
                "finishReason": "STOP",
            }
        ]
    }


VALID_EXTRACTION_JSON = json.dumps({
    "product": "Cement",
    "category": "Construction Materials",
    "quantity": "500 tonnes",
    "application": "Road construction",
    "environment": "Outdoor, tropical",
    "technical_requirements": [
        "Compressive strength >= 33 MPa at 28 days",
        "Initial setting time >= 30 minutes",
    ],
    "materials": ["Portland clinker", "Gypsum"],
    "performance_requirements": ["Fineness >= 225 m²/kg"],
    "safety_requirements": ["Low heat of hydration"],
    "testing_requirements": ["IS 4031 compressive strength test"],
    "certification_mentions": ["ISI mark", "BIS certification"],
    "referenced_standards": ["IS 269", "IS 8112"],
})


# ---------------------------------------------------------------------------
# _strip_markdown_fences
# ---------------------------------------------------------------------------

class TestStripMarkdownFences:

    def test_plain_json_unchanged(self):
        raw = '{"product": "Laptop"}'
        assert _strip_markdown_fences(raw) == raw.strip()

    def test_strips_json_fence(self):
        raw = '```json\n{"product": "Laptop"}\n```'
        assert _strip_markdown_fences(raw) == '{"product": "Laptop"}'

    def test_strips_bare_fence(self):
        raw = '```\n{"product": "Laptop"}\n```'
        assert _strip_markdown_fences(raw) == '{"product": "Laptop"}'

    def test_strips_with_trailing_whitespace(self):
        raw = '```json\n{"product": "Laptop"}\n```  \n'
        assert _strip_markdown_fences(raw) == '{"product": "Laptop"}'

    def test_no_fence_no_change(self):
        raw = '  {"product": "Laptop"}  '
        assert _strip_markdown_fences(raw) == '{"product": "Laptop"}'


# ---------------------------------------------------------------------------
# OpenAI provider — existing tests preserved
# ---------------------------------------------------------------------------

class TestOpenAIProvider:

    def test_extraction_with_mock_provider(self):
        service = RequirementExtractionService()
        service.provider = MagicMock()
        service.provider.generate.return_value = (
            '{"product": "Laptop", "category": "IT", '
            '"technical_requirements": ["Intel i7", "16GB RAM"]}'
        )

        result = service.extract("Procurement of Laptop, IT category")

        assert result.product == "Laptop"
        assert result.category == "IT"
        assert "Intel i7" in result.technical_requirements
        assert "16GB RAM" in result.technical_requirements

    def test_extraction_fallback_on_malformed_json(self):
        service = RequirementExtractionService()
        service.provider = MagicMock()
        service.provider.generate.return_value = '{"product": "Laptop", "category": "IT"'

        result = service.extract("Some text")

        assert isinstance(result, ExtractedRequirements)
        assert result.product is None


# ---------------------------------------------------------------------------
# GeminiProvider unit tests (mocked HTTP)
# ---------------------------------------------------------------------------

class TestGeminiProvider:

    def test_generate_parses_valid_response(self):
        provider = GeminiProvider(api_key="test-key", model="gemini-3.8-flash")
        mock_response = httpx.Response(
            200,
            json=_gemini_response_body(VALID_EXTRACTION_JSON),
            request=httpx.Request("POST", provider.api_url),
        )

        with patch("httpx.Client") as MockClient:
            MockClient.return_value.__enter__ = lambda s: s
            MockClient.return_value.__exit__ = MagicMock(return_value=False)
            MockClient.return_value.post.return_value = mock_response

            text = provider.generate("extract requirements")

        data = json.loads(text)
        assert data["product"] == "Cement"
        assert "IS 269" in data["referenced_standards"]

    def test_generate_raises_on_http_error(self):
        provider = GeminiProvider(api_key="test-key", model="gemini-3.8-flash")
        mock_response = httpx.Response(
            403,
            json={"error": {"message": "Forbidden"}},
            request=httpx.Request("POST", provider.api_url),
        )

        with patch("httpx.Client") as MockClient:
            MockClient.return_value.__enter__ = lambda s: s
            MockClient.return_value.__exit__ = MagicMock(return_value=False)
            MockClient.return_value.post.return_value = mock_response

            with pytest.raises(httpx.HTTPStatusError):
                provider.generate("test prompt")

    def test_generate_raises_on_404_deprecated_model(self):
        """Reproduces the actual production bug: Gemini returns 404 for deprecated model."""
        provider = GeminiProvider(api_key="test-key", model="gemini-2.5-flash")
        mock_response = httpx.Response(
            404,
            json={"error": {
                "code": 404,
                "message": "This model models/gemini-2.5-flash is no longer available.",
                "status": "NOT_FOUND",
            }},
            request=httpx.Request("POST", provider.api_url),
        )

        with patch("httpx.Client") as MockClient:
            MockClient.return_value.__enter__ = lambda s: s
            MockClient.return_value.__exit__ = MagicMock(return_value=False)
            MockClient.return_value.post.return_value = mock_response

            with pytest.raises(httpx.HTTPStatusError):
                provider.generate("test prompt")

    def test_generate_raises_on_network_error(self):
        provider = GeminiProvider(api_key="test-key", model="gemini-3.8-flash")

        with patch("httpx.Client") as MockClient:
            MockClient.return_value.__enter__ = lambda s: s
            MockClient.return_value.__exit__ = MagicMock(return_value=False)
            MockClient.return_value.post.side_effect = httpx.ConnectError("DNS failure")

            with pytest.raises(httpx.ConnectError):
                provider.generate("test prompt")

    def test_generate_raises_on_malformed_structure(self):
        """Gemini returns 200 but the JSON structure is unexpected."""
        provider = GeminiProvider(api_key="test-key", model="gemini-3.8-flash")
        mock_response = httpx.Response(
            200,
            json={"candidates": []},
            request=httpx.Request("POST", provider.api_url),
        )

        with patch("httpx.Client") as MockClient:
            MockClient.return_value.__enter__ = lambda s: s
            MockClient.return_value.__exit__ = MagicMock(return_value=False)
            MockClient.return_value.post.return_value = mock_response

            with pytest.raises(ValueError, match="unexpected response format"):
                provider.generate("test prompt")

    def test_api_url_uses_model_name(self):
        provider = GeminiProvider(api_key="k", model="gemini-3.8-flash")
        assert "gemini-3.8-flash" in provider.api_url
        assert provider.api_url.startswith("https://generativelanguage.googleapis.com/")

    def test_api_key_not_in_url_path(self):
        """The API key must be passed as a query param, not embedded in the path."""
        provider = GeminiProvider(api_key="secret-key-123", model="gemini-3.8-flash")
        assert "secret-key-123" not in provider.api_url


# ---------------------------------------------------------------------------
# Provider initialization
# ---------------------------------------------------------------------------

class TestProviderInitialization:

    @patch("app.services.requirement_extraction_service.settings")
    def test_gemini_provider_selected(self, mock_settings):
        mock_settings.llm_provider = "gemini"
        mock_settings.llm_api_key = "test-gemini-key"
        mock_settings.llm_model = "gemini-3.8-flash"

        service = RequirementExtractionService()

        assert isinstance(service.provider, GeminiProvider)
        assert service.provider.model == "gemini-3.8-flash"

    @patch("app.services.requirement_extraction_service.settings")
    def test_openai_provider_selected(self, mock_settings):
        mock_settings.llm_provider = "openai"
        mock_settings.llm_api_key = "test-openai-key"
        mock_settings.llm_model = "gpt-4o"

        service = RequirementExtractionService()

        assert isinstance(service.provider, OpenAIProvider)
        assert service.provider.model == "gpt-4o"

    @patch("app.services.requirement_extraction_service.settings")
    def test_unsupported_provider_logs_warning(self, mock_settings):
        mock_settings.llm_provider = "anthropic"
        mock_settings.llm_api_key = ""
        mock_settings.llm_model = ""

        service = RequirementExtractionService()

        assert service.provider is None

    @patch("app.services.requirement_extraction_service.settings")
    def test_no_provider_returns_empty_requirements(self, mock_settings):
        mock_settings.llm_provider = "unsupported"
        mock_settings.llm_api_key = ""
        mock_settings.llm_model = ""

        service = RequirementExtractionService()
        result = service.extract("Some procurement text")

        assert isinstance(result, ExtractedRequirements)
        assert result.product is None
        assert result.technical_requirements == []


# ---------------------------------------------------------------------------
# End-to-end extraction through RequirementExtractionService with Gemini mock
# ---------------------------------------------------------------------------

class TestGeminiExtraction:

    def test_valid_gemini_json_to_extracted_requirements(self):
        """Gemini returns valid JSON → fully populated ExtractedRequirements."""
        service = RequirementExtractionService()
        service.provider = MagicMock()
        service.provider.generate.return_value = VALID_EXTRACTION_JSON

        result = service.extract("Supply of 500 tonnes OPC cement for road construction")

        assert result.product == "Cement"
        assert result.category == "Construction Materials"
        assert result.quantity == "500 tonnes"
        assert result.application == "Road construction"
        assert result.environment == "Outdoor, tropical"
        assert len(result.technical_requirements) == 2
        assert "IS 269" in result.referenced_standards
        assert "ISI mark" in result.certification_mentions

    def test_malformed_gemini_response_returns_empty(self):
        """Gemini returns non-JSON text → safe fallback."""
        service = RequirementExtractionService()
        service.provider = MagicMock()
        service.provider.generate.return_value = "Sorry, I cannot parse that document."

        result = service.extract("invalid input")

        assert isinstance(result, ExtractedRequirements)
        assert result.product is None
        assert result.technical_requirements == []

    def test_gemini_api_failure_returns_empty(self):
        """Gemini provider raises an exception → safe fallback."""
        service = RequirementExtractionService()
        service.provider = MagicMock()
        service.provider.generate.side_effect = httpx.HTTPStatusError(
            "403 Forbidden",
            request=httpx.Request("POST", "https://example.com"),
            response=httpx.Response(403),
        )

        result = service.extract("Some text")

        assert isinstance(result, ExtractedRequirements)
        assert result.product is None

    def test_gemini_404_deprecated_model_returns_empty(self):
        """Reproduces the actual bug: Gemini 404 on deprecated model → safe fallback."""
        service = RequirementExtractionService()
        service.provider = MagicMock()
        service.provider.generate.side_effect = httpx.HTTPStatusError(
            "404 Not Found",
            request=httpx.Request("POST", "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"),
            response=httpx.Response(404),
        )

        result = service.extract("Supply of LED street lights")

        assert isinstance(result, ExtractedRequirements)
        assert result.product is None
        assert result.technical_requirements == []

    def test_gemini_network_error_returns_empty(self):
        """Network failure → safe fallback, no crash."""
        service = RequirementExtractionService()
        service.provider = MagicMock()
        service.provider.generate.side_effect = httpx.ConnectError("connection refused")

        result = service.extract("Some text")

        assert isinstance(result, ExtractedRequirements)
        assert result.product is None

    def test_gemini_partial_json_returns_partial_requirements(self):
        """Gemini returns valid JSON with only some fields populated."""
        service = RequirementExtractionService()
        service.provider = MagicMock()
        service.provider.generate.return_value = json.dumps({
            "product": "Steel Bars",
            "category": "Structural Steel",
        })

        result = service.extract("Procurement of steel bars")

        assert result.product == "Steel Bars"
        assert result.category == "Structural Steel"
        assert result.quantity is None
        assert result.technical_requirements == []

    def test_gemini_markdown_fenced_json_extracted(self):
        """Gemini wraps JSON in ```json ... ``` fences → still parsed correctly."""
        service = RequirementExtractionService()
        service.provider = MagicMock()
        fenced = '```json\n' + VALID_EXTRACTION_JSON + '\n```'
        service.provider.generate.return_value = fenced

        result = service.extract("Supply of OPC cement")

        assert result.product == "Cement"
        assert result.category == "Construction Materials"
        assert len(result.technical_requirements) == 2

    def test_gemini_bare_fenced_json_extracted(self):
        """Gemini wraps JSON in bare ``` ... ``` fences → still parsed correctly."""
        service = RequirementExtractionService()
        service.provider = MagicMock()
        fenced = '```\n{"product": "Laptop", "category": "IT"}\n```'
        service.provider.generate.return_value = fenced

        result = service.extract("Procurement of laptop")

        assert result.product == "Laptop"
        assert result.category == "IT"
