import requests
import json


def test_ocr_service(file_path: str, endpoint: str = "pdf"):
    """
    Test the OCR service with a file
    """
    url = f"http://localhost:8000/ocr/{endpoint}"

    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, files=files)

    if response.status_code == 200:
        result = response.json()
        print("=" * 70)
        print("SUCCESS!")
        print("=" * 70)
        print("\n📄 PARSED DATA:")
        print(json.dumps(result['parsed_data'], indent=2, ensure_ascii=False))
        print("\n" + "=" * 70)

        # Save results
        with open('result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("✅ Full results saved to result.json")

    else:
        print(f"❌ ERROR: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    # Test with your bill
    test_ocr_service("storm_bill.pdf", endpoint="pdf")
    # or for images:
    # test_ocr_service("bill_image.jpg", endpoint="image")
