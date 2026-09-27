"""Diagnostic: test a real Gemini extraction and trace every step."""

import sys
import json
import httpx

sys.path.insert(0, ".")
from app.core.config import settings
from app.schemas.analysis import ExtractedRequirements

SAMPLE_TEXT = """Supply and installation of LED street lights.
Quantity: 500 units.
Rated power: 90 W.
Input voltage: 230 V AC.
Frequency: 50 Hz.
Power factor: minimum 0.95.
Operating voltage range: 180 V AC to 270 V AC.
Ingress protection: minimum IP66.
Housing material: Aluminium.
CCT: 5700 K.
LED efficacy: minimum 120 lm/W.
CRI: minimum 70.
Operating temperature: -10 °C to 50 °C.
Application: outdoor road and street lighting.
Warranty: minimum 3 years.
Testing shall include electrical safety, insulation, photometric performance, ingress protection and functional testing.
Supplier shall provide product datasheet, test reports, warranty documentation and applicable conformity/certification documents."""

def main():
    print(f"=== LLM Provider: {settings.llm_provider}")
    print(f"=== LLM Model:    {settings.llm_model}")
    print(f"=== API key set:  {bool(settings.llm_api_key)}")
    print(f"=== API key len:  {len(settings.llm_api_key)}")
    print()

    if settings.llm_provider != "gemini":
        print("ERROR: LLM_PROVIDER is not 'gemini'. Exiting.")
        return

    model = settings.llm_model
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    print(f"=== Gemini URL: {api_url}")
    print()

    prompt = f"""
Extract the following procurement requirements from the text below.
Return ONLY a valid JSON object. No markdown, no explanation, no code fences.

Required fields (use null for unknown strings, [] for unknown lists):
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

Do NOT invent or fabricate any information. Only extract what is explicitly stated.

Text:
{SAMPLE_TEXT}
"""

    headers = {"Content-Type": "application/json"}
    params = {"key": settings.llm_api_key}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json",
        },
        "systemInstruction": {
            "parts": [{
                "text": "You are a helpful assistant that extracts structured information from procurement documents. You must return ONLY valid JSON matching the requested schema."
            }]
        },
    }

    print("=== Sending request to Gemini...")
    try:
        with httpx.Client() as client:
            response = client.post(api_url, headers=headers, params=params, json=data, timeout=60.0)
        print(f"=== HTTP status: {response.status_code}")
        print(f"=== Response length: {len(response.content)} bytes")
        print()
    except Exception as e:
        print(f"=== HTTP request FAILED: {type(e).__name__}: {e}")
        return

    # Parse response JSON
    try:
        result = response.json()
    except Exception as e:
        print(f"=== Response JSON parse FAILED: {e}")
        print(f"=== Raw response (first 500 chars): {response.text[:500]}")
        return

    # Show top-level keys
    print(f"=== Response top-level keys: {list(result.keys())}")
    print()

    # Check for error
    if "error" in result:
        print(f"=== Gemini API error: {result['error']}")
        return

    # Navigate candidates
    candidates = result.get("candidates", [])
    print(f"=== Number of candidates: {len(candidates)}")
    if not candidates:
        print("=== No candidates returned!")
        print(f"=== Full response: {json.dumps(result, indent=2)[:1000]}")
        return

    candidate = candidates[0]
    print(f"=== Candidate keys: {list(candidate.keys())}")

    # Check finish reason
    finish_reason = candidate.get("finishReason", "UNKNOWN")
    print(f"=== Finish reason: {finish_reason}")

    content = candidate.get("content", {})
    print(f"=== Content keys: {list(content.keys())}")

    parts = content.get("parts", [])
    print(f"=== Number of parts: {len(parts)}")

    if not parts:
        print("=== No parts in content!")
        return

    raw_text = parts[0].get("text", "")
    print(f"=== Raw text length: {len(raw_text)}")
    print(f"=== Raw text type: {type(raw_text).__name__}")
    print()
    print("=== RAW TEXT (first 1500 chars) ===")
    print(raw_text[:1500])
    print("=== END RAW TEXT ===")
    print()

    # Try to strip markdown fences if present
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        print("=== DETECTED: markdown code fences around JSON")
        # Strip opening fence (```json or ```)
        first_newline = cleaned.index("\n")
        cleaned = cleaned[first_newline + 1:]
        # Strip closing fence
        if cleaned.rstrip().endswith("```"):
            cleaned = cleaned.rstrip()[:-3].rstrip()
        print(f"=== Cleaned text length: {len(cleaned)}")
        print(f"=== Cleaned text (first 500 chars): {cleaned[:500]}")
        print()

    # Try json.loads
    try:
        parsed = json.loads(cleaned)
        print("=== json.loads: SUCCESS")
        print(f"=== Parsed keys: {list(parsed.keys())}")
        print(f"=== Parsed data: {json.dumps(parsed, indent=2)}")
        print()
    except json.JSONDecodeError as e:
        print(f"=== json.loads FAILED: {e}")
        print(f"=== Failed on text: {cleaned[:300]}")
        return

    # Try Pydantic
    try:
        req = ExtractedRequirements(**parsed)
        print("=== Pydantic validation: SUCCESS")
        print(f"=== product:       {req.product}")
        print(f"=== category:      {req.category}")
        print(f"=== quantity:      {req.quantity}")
        print(f"=== application:   {req.application}")
        print(f"=== environment:   {req.environment}")
        print(f"=== tech_reqs:     {req.technical_requirements}")
        print(f"=== materials:     {req.materials}")
        print(f"=== perf_reqs:     {req.performance_requirements}")
        print(f"=== safety_reqs:   {req.safety_requirements}")
        print(f"=== test_reqs:     {req.testing_requirements}")
        print(f"=== cert_mentions: {req.certification_mentions}")
        print(f"=== ref_standards: {req.referenced_standards}")
    except Exception as e:
        print(f"=== Pydantic validation FAILED: {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()
