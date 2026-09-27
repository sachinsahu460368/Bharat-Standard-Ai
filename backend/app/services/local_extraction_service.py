import re
import logging
from typing import Optional
from app.schemas.analysis import ExtractedRequirements

logger = logging.getLogger(__name__)

class LocalRequirementExtractor:
    """Fallback extractor using regex patterns."""

    def extract(self, text: str) -> ExtractedRequirements:
        """Extract requirements using deterministic regex patterns."""
        logger.info("Running local fallback extraction.")

        reqs = ExtractedRequirements()

        # Helper to extract a single pattern
        def get_pattern(pattern: str, text: str, group: int = 1) -> Optional[str]:
            match = re.search(pattern, text, re.IGNORECASE)
            return match.group(group).strip() if match else None

        # Helper to extract a list pattern
        def get_list_pattern(pattern: str, text: str, group: int = 1) -> list[str]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            # Filter, clean and deduplicate
            cleaned = []
            for m in matches:
                val = m.strip()
                if val and val not in cleaned:
                    cleaned.append(val)
            return cleaned

        # 1. Product (Cleaned)
        product_match = get_pattern(r"SUBJECT:\s*(.*)", text) or \
                        get_pattern(r"Procurement of (.*)", text)
        if product_match:
            product_match = re.sub(r'[\r\n]+', ' ', product_match)
            reqs.product = product_match.strip()

        # 2. Category (GUESS based on streetlight context as requested)
        reqs.category = "Outdoor Lighting"

        # 3. Quantity
        quantity_match = get_pattern(r"(?:Total|Quantity):\s*([\d,]+)", text)
        reqs.quantity = quantity_match.replace(',', '') if quantity_match else None

        # 4. Technical Requirements
        # Updated patterns for cleanliness
        tech_map = {
            "Wattage": [r"Wattage:\s*([0-9W\s-]+)"],
            "Input voltage": [r"Input Voltage:\s*([0-9\.\sVAC]+)"],
            "Power factor": [r"Power Factor:\s*([>=0-9\.\s]+)"],
            "Ingress protection": [r"IP Rating:\s*([A-Za-z0-9]+)", r"Protection:\s*([A-Za-z0-9]+)"],
            "Luminous Efficacy": [r"Efficacy:\s*([0-9\.\s\w/]+)"],
            "CCT": [r"CCT:\s*([0-9\sKk]+)", r"Colour temperature:\s*([0-9\sKk]+)"],
            "CRI": [r"CRI:\s*([>=0-9\.]+)"],
        }

        for label, patterns in tech_map.items():
            for pat in patterns:
                if match := get_pattern(pat, text, group=1):
                    val = match.strip()
                    formatted_val = f"{label}: {val}"
                    reqs.technical_requirements.append(formatted_val)
                    break
        reqs.technical_requirements = list(dict.fromkeys(reqs.technical_requirements))

        # 5. Materials
        materials_raw = get_list_pattern(r"Material:\s*([^\n\r]+)", text, group=1)
        reqs.materials = [re.split(r'[\r\n]+', m.strip())[0].capitalize() for m in materials_raw]

        # 6. Certifications (Cleaned)
        possible_certs = get_list_pattern(r"(BIS certification|ISI Mark)", text, group=0)
        reqs.certification_mentions = possible_certs

        # Referenced Standards
        # Modified to capture more of the string
        reqs.referenced_standards = get_list_pattern(r"IS\s+\d+\s*(?:Part|Sec)?\s*[\d/]*(?:Sec\s*[\d/]+)?", text, group=0)

        # 7. Application & Environment (Cleaned)
        if app_match := get_pattern(r"Application:\s*([^\n\r]+)", text):
            # Remove leading bullets, dashes
            reqs.application = re.sub(r'^[\s\-]+', '', app_match).strip()

        if env_match := get_pattern(r"Operating Temperature:\s*([^\n\r]+)", text):
            reqs.environment = env_match.strip()

        return reqs
