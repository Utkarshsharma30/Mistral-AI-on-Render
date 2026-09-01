import sys
import requests
import json

def test_health(base_url):
    print(f"\n[1] Testing Health Endpoint on {base_url}...")
    try:
        r = requests.get(f"{base_url}/health", timeout=10)
        print(f"Status Code: {r.status_code}")
        print("Response:", json.dumps(r.json(), indent=2))
        return r.status_code == 200
    except Exception as e:
        print(f"Failed health check: {e}")
        return False

def test_chat(base_url):
    print(f"\n[2] Testing Chat Completion Endpoint on {base_url}...")
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful chatbot assistant."},
            {"role": "user", "content": "Hello! What can you do?"}
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }
    try:
        r = requests.post(f"{base_url}/api/chat", json=payload, timeout=30)
        print(f"Status Code: {r.status_code}")
        if r.status_code == 200:
            print("Response Payload:\n", json.dumps(r.json(), indent=2))
        else:
            print("Error details:", r.text)
    except Exception as e:
        print(f"Failed chat completion test: {e}")

if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    print(f"Targeting server: {target_url}")
    if test_health(target_url):
        test_chat(target_url)
