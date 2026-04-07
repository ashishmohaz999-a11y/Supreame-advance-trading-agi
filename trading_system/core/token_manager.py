import os
import json
import time
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

TOKEN_FILE = "token_store.json"

def save_token(access_token: str, client_id: str):
    """Token ko file mein save karo with timestamp"""
    data = {
        "access_token": access_token,
        "client_id": client_id,
        "saved_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(hours=23)).isoformat()
    }
    with open(TOKEN_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Token saved at {data['saved_at']}")

def load_token():
    """File se token load karo"""
    if not os.path.exists(TOKEN_FILE):
        return None, None
    with open(TOKEN_FILE, "r") as f:
        data = json.load(f)
    return data["access_token"], data["client_id"]

def is_token_valid():
    """Check karo token abhi valid hai ya nahi"""
    if not os.path.exists(TOKEN_FILE):
        return False
    with open(TOKEN_FILE, "r") as f:
        data = json.load(f)
    expires_at = datetime.fromisoformat(data["expires_at"])
    remaining = expires_at - datetime.now()
    hours_left = remaining.total_seconds() / 3600
    print(f"⏰ Token expires in: {hours_left:.1f} hours")
    return hours_left > 0

def test_token():
    """Live API call karke token test karo"""
    token, client_id = load_token()
    if not token:
        return False
    try:
        headers = {
            "access-token": token,
            "client-id": client_id,
            "Content-Type": "application/json"
        }
        res = requests.get(
            "https://api.dhan.co/fundlimit",
            headers=headers,
            timeout=5
        )
        if res.status_code == 200:
            print("✅ Token VALID - API working")
            return True
        else:
            print(f"❌ Token INVALID - Status: {res.status_code}")
            return False
    except Exception as e:
        print(f"❌ API Error: {e}")
        return False

if __name__ == "__main__":
    print("=== Token Status Check ===")
    valid = test_token()
    if not valid:
        print("\n⚠️  Token expired! Run: python update_token.py")
