from fastapi.testclient import TestClient
from app.main import app
from pathlib import Path

client = TestClient(app)

SAMPLE_DOC = Path("data/sample_documents/led_streetlight_procurement.txt").resolve()

def test_analyze_endpoint():
    print(f"Reading sample from: {SAMPLE_DOC}")
    content = SAMPLE_DOC.read_bytes()
    resp = client.post(
        "/api/v1/analyze",
        files={"file": ("led_streetlight.txt", content, "text/plain")},
    )

    print(f"Status Code: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Error Response: {resp.text}")
        return

    data = resp.json()
    req = data["requirements"]

    print("Product:", req.get("product"))
    print("Category:", req.get("category"))
    print("Quantity:", req.get("quantity"))
    print("Application:", req.get("application"))
    print("Technical Req count:", len(req.get("technical_requirements", [])))
    print("Performance Req count:", len(req.get("performance_requirements", [])))
    print("Safety Req count:", len(req.get("safety_requirements", [])))
    print("Testing Req count:", len(req.get("testing_requirements", [])))

    recommendations = data.get("recommendations", [])
    print("Recommendations count:", len(recommendations))
    if recommendations:
        print("Matched Requirements (first rec):", recommendations[0].get("matched_requirements"))

if __name__ == "__main__":
    test_analyze_endpoint()
