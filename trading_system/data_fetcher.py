import os
import json
from dhanhq import dhanhq
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def get_dhan_client():
    with open("token_store.json") as f:
        data = json.load(f)
    return dhanhq(data["client_id"], data["access_token"])

def get_portfolio():
    dhan = get_dhan_client()
    holdings = dhan.get_holdings()
    print("=== Portfolio Holdings ===")
    print(holdings)
    return holdings

def get_funds():
    dhan = get_dhan_client()
    funds = dhan.get_fund_limits()
    print("=== Fund Details ===")
    print(funds)
    return funds

if __name__ == "__main__":
    print(f"Time: {datetime.now()}")
    get_funds()
    get_portfolio()
