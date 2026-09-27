import pytest
from app.services.local_extraction_service import LocalRequirementExtractor
from app.schemas.analysis import ExtractedRequirements

@pytest.fixture
def extractor():
    return LocalRequirementExtractor()

def test_extract_led_streetlight_text(extractor):
    text = """
    SUBJECT: Procurement of Outdoor LED Street Lighting Systems

    Quantity: 500

    Wattage: 90W
    Input Voltage: 230 V AC
    IP Rating: IP66
    CCT: 5700K

    Power Factor: >= 0.95
    CRI: 70

    BIS certification is mandatory. (Test reports are NOT certification)
    Referenced standards: IS 10322 Part 5/Sec 3

    Application: Outdoor road/street lighting
    Operating Temperature: -10 °C to 50 °C

    Material: Aluminium
    Test: Routine tests, Test reports, Factory tests.
    """

    reqs = extractor.extract(text)

    assert reqs.product == "Procurement of Outdoor LED Street Lighting Systems"
    assert reqs.quantity == "500"
    assert "Wattage: 90W" in reqs.technical_requirements
    assert "Input voltage: 230 V AC" in reqs.technical_requirements
    assert "Ingress protection: IP66" in reqs.technical_requirements
    assert "CCT: 5700K" in reqs.technical_requirements

    assert "Power factor: >= 0.95" in reqs.technical_requirements # Moved from perf per mapping
    assert "CRI: 70" in reqs.technical_requirements

    assert "Aluminium" in reqs.materials

    assert "BIS certification" in reqs.certification_mentions
    assert "test reports" not in reqs.certification_mentions

    assert "IS 10322 Part 5/Sec 3" in reqs.referenced_standards
    assert reqs.application == "Outdoor road/street lighting"
    assert reqs.environment == "-10 °C to 50 °C"

def test_deduplication(extractor):
    text = "Power Factor: 0.95\nPower Factor: 0.95"
    reqs = extractor.extract(text)
    assert len(reqs.technical_requirements) == 1

def test_empty_fields(extractor):
    text = "SUBJECT: Procurement of Transformers"
    reqs = extractor.extract(text)
    assert reqs.product == "Procurement of Transformers"
    assert reqs.quantity is None
