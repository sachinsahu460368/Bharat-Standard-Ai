import httpx
import json

def run_e2e_test():
    url = "http://localhost:8000/api/v1/analyze"
    text = b"Procure 200 LED streetlights for municipal roads. IS 10322."

    # Assuming standard base url, adjust if needed
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                url,
                files={"file": ("led_analysis_test.txt", text, "text/plain")},
            )
            data = resp.json()

            # Print important verification fields
            print(f"Status: {data['status']}")
            print(f"Recommendations count: {len(data['recommendations'])}")

            for i, rec in enumerate(data['recommendations']):
                print(f"\nRecommendation {i+1}: {rec.get('standard_number')}")
                print(f"Match Reason: {rec.get('reason')}")
                print(f"Evidence: {rec.get('evidence')}")

                # Check for "MOCK"
                json_str = json.dumps(rec)
                if "MOCK" in json_str.upper():
                    print("ERROR: Found MOCK in recommendation!")

            print("\nCompliance checks:")
            for comp in data.get('compliance', []):
                print(f"Standard: {comp.get('standard_id')}, Status: {comp.get('status')}")

    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    run_e2e_test()
