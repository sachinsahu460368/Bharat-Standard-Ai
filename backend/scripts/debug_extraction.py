from app.services.requirement_extraction_service import requirement_extraction_service
import logging

logging.basicConfig(level=logging.INFO)

text = """
SUBJECT: Procurement of Outdoor LED Street Lighting Systems

2. QUANTITY
-----------
Total: 500 units of LED street light luminaires

3. TECHNICAL REQUIREMENTS
--------------------------
3.1 Type: LED Street Light Luminaire
3.2 Wattage: 90W to 120W
6.3 BIS certification (ISI Mark) is mandatory.
"""

print("Extracting...")
try:
    reqs = requirement_extraction_service.extract(text)
    print("Product:", reqs.product)
    print("Quantity:", reqs.quantity)
    print("Certification mentions:", reqs.certification_mentions)
    print("Full object:", reqs.model_dump())
except Exception as e:
    print(f"Extraction failed: {e}")
