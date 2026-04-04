import requests
import time
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000"

def run_test():
    print("Testing /api/knowledge/upload...")
    with open("test_contract.txt", "rb") as f:
        res = requests.post(f"{BASE_URL}/api/knowledge/upload", files={"file": ("test_contract.txt", f, "text/plain")})
    print("Upload Contract Response:", res.json())
    
    print("\nTesting /api/invoice/upload...")
    with open("test_invoice.txt", "rb") as f:
        res2 = requests.post(f"{BASE_URL}/api/invoice/upload", files={"file": ("test_invoice.txt", f, "text/plain")})
    invoice_data = res2.json()
    print("Upload Invoice Response:", invoice_data)
    
    print("\nTesting /api/invoice/validate (Agentic RAG)...")
    res3 = requests.post(f"{BASE_URL}/api/invoice/validate", json={"invoice_path": invoice_data["path"]})
    print("Validation Response Code:", res3.status_code)
    try:
        report = res3.json()
        print("\n=== Validation Report ===")
        print(report.get("validation_report", report))
        print("=========================")
    except Exception as e:
        print("Failed to parse JSON:", res3.text)

if __name__ == "__main__":
    # give server a second to boot if we run script immediately
    time.sleep(2)
    try:
        run_test()
    except Exception as e:
        print("Test failed:", str(e))
        sys.exit(1)
