import os
import requests
from dotenv import load_dotenv

try:
    load_dotenv()
except:
    pass

def test_grok():
    api_key = os.getenv('GROK_API_KEY')
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messages": [
            {"role": "user", "content": "In 10 words or less, what is the capital of the moon?"}
        ],
        "model": "grok-4",
        "stream": False,
        "temperature": 0.7
    }
    
    response = requests.post("https://api.x.ai/v1/chat/completions", headers=headers, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    test_grok()