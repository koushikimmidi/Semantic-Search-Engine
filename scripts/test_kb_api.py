import requests
import os

BASE_URL = "http://localhost:8000"

def test_flow():
    print("1. Listing documents...")
    r = requests.get(f"{BASE_URL}/documents")
    print("Status:", r.status_code)
    docs = r.json()
    print("Initial documents count:", len(docs))
    
    test_file_path = r"C:\Users\koush\.gemini\antigravity-ide\brain\8f841003-20cf-49af-b9ff-92766e17308a\scratch\gemini_agents_rule.txt"
    if not os.path.exists(test_file_path):
        print(f"Error: Test file not found at {test_file_path}")
        return

    print("\n2. Uploading test file...")
    with open(test_file_path, "rb") as f:
        files = {"files": ("gemini_agents_rule.txt", f, "text/plain")}
        data = {"paths": ["gemini_agents_rule.txt"]}
        r = requests.post(f"{BASE_URL}/documents/upload", files=files, data=data)
    print("Status:", r.status_code)
    print("Upload response:", r.json())

    print("\n3. Listing documents after upload...")
    r = requests.get(f"{BASE_URL}/documents")
    docs = r.json()
    print("New documents count:", len(docs))
    matching_docs = [d for d in docs if d["path"] == "gemini_agents_rule.txt"]
    print("Is test file listed?", len(matching_docs) > 0)
    if matching_docs:
        print("Details:", matching_docs[0])

    print("\n4. Viewing document content...")
    r = requests.get(f"{BASE_URL}/documents/content", params={"path": "gemini_agents_rule.txt"})
    print("Status:", r.status_code)
    print("Content response:", r.json())

    print("\n5. Searching for grounded info...")
    r = requests.post(f"{BASE_URL}/search", json={"query": "Who rules the universe?"})
    print("Status:", r.status_code)
    res = r.json()
    print("Generated Answer:", res.get("answer"))
    print("Sources retrieved:")
    for src in res.get("sources", []):
        print(f" - {src.get('source')} (score: {src.get('cross_score')})")

    print("\n6. Deleting test file...")
    r = requests.delete(f"{BASE_URL}/documents", params={"path": "gemini_agents_rule.txt"})
    print("Status:", r.status_code)
    print("Delete response:", r.json())

    print("\n7. Listing documents after delete...")
    r = requests.get(f"{BASE_URL}/documents")
    docs = r.json()
    matching_docs = [d for d in docs if d["path"] == "gemini_agents_rule.txt"]
    print("Is test file still listed?", len(matching_docs) > 0)

    print("\n8. Searching after delete...")
    r = requests.post(f"{BASE_URL}/search", json={"query": "Who rules the universe?"})
    res = r.json()
    print("Answer after deletion:", res.get("answer"))

if __name__ == "__main__":
    test_flow()
