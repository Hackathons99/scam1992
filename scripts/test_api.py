import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_analyze_endpoint():
    print("Testing /analyze endpoint...")
    url = f"{BASE_URL}/analyze"
    
    payload = {
        "sessionId": "test-session-123",
        "message": {
            "sender": "scammer",
            "text": "Your bank account will be blocked today. Verify immediately.",
            "timestamp": "2026-01-21T10:15:30Z"
        },
        "conversationHistory": [],
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        print("Response:", json.dumps(data, indent=2))
        
        assert data["scamDetected"] == True
        print("✅ /analyze test passed (Scam Detected)")
    except Exception as e:
        print(f"❌ /analyze test failed: {e}")

def test_safe_message():
    print("\nTesting /analyze endpoint with safe message...")
    url = f"{BASE_URL}/analyze"
    
    payload = {
        "sessionId": "test-session-456",
        "message": {
            "sender": "user",
            "text": "Hello, how are you?",
            "timestamp": "2026-01-21T10:15:30Z"
        },
        "conversationHistory": []
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        print("Response:", json.dumps(data, indent=2))
        
        assert data["scamDetected"] == False
        print("✅ /analyze test passed (Safe Message)")
    except Exception as e:
        print(f"❌ /analyze test failed: {e}")

if __name__ == "__main__":
    # Wait for server to potentially start if running in parallel, 
    # but normally this script is run after server is up.
    try:
        test_analyze_endpoint()
        test_safe_message()
    except Exception as e:
        print(f"Test suite failed: {e}")
