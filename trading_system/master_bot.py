import time
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from trading_system.strategy_engine import get_signal
from trading_system.risk_manager import evaluate_trade
from trading_system.paper_trader import (
    load_paper_account, paper_buy, 
    paper_sell, show_summary
)

load_dotenv()

# Symbols jo trade karne hain
SYMBOLS = [
    "RELIANCE", "TCS", "INFY", 
    "HDFCBANK", "SBIN", "WIPRO"
]

# Fake prices (baad mein Dhan API se live price aayega)
def get_mock_price(symbol):
    import random
    base_prices = {
        "RELIANCE": 2850, "TCS": 3500,
        "INFY": 1450, "HDFCBANK": 1650,
        "SBIN": 780, "WIPRO": 450
    }
    base = base_prices.get(symbol, 1000)
    return round(base * (1 + random.uniform(-0.02, 0.02)), 2)

def get_mock_price_history(symbol, length=50):
    import random
    base_prices = {
        "RELIANCE": 2850, "TCS": 3500,
        "INFY": 1450, "HDFCBANK": 1650,
        "SBIN": 780, "WIPRO": 450
    }
    base = base_prices.get(symbol, 1000)
    prices = [base]
    for _ in range(length - 1):
        prices.append(round(
            prices[-1] * (1 + random.uniform(-0.01, 0.01)), 2
        ))
    return prices

def check_stop_loss_target(symbol, current_price, account):
    """SL/Target hit check"""
    if symbol not in account["open_positions"]:
        return account
    
    pos = account["open_positions"][symbol]
    sl = pos["stop_loss"]
    target = pos["target"]
    
    if current_price <= sl:
        print(f"🛑 STOP LOSS HIT: {symbol} @ ₹{current_price}")
        account = paper_sell(symbol, current_price, account)
    elif current_price >= target:
        print(f"🎯 TARGET HIT: {symbol} @ ₹{current_price}")
        account = paper_sell(symbol, current_price, account)
    
    return account

def run_bot_cycle(account):
    print(f"\n{'='*40}")
    print(f"🤖 BOT CYCLE: {datetime.now().strftime('%H:%M:%S')}")
    print(f"💰 Capital: ₹{round(account['capital'], 2)}")
    print(f"{'='*40}")
    
    for symbol in SYMBOLS:
        current_price = get_mock_price(symbol)
        prices = get_mock_price_history(symbol)
        
        # SL/Target check
        account = check_stop_loss_target(
            symbol, current_price, account
        )
        
        # Signal generate karo
        signal = get_signal(prices)
        action = signal["action"]
        
        print(f"\n📊 {symbol} @ ₹{current_price}")
        print(f"   Signal: {action} | RSI: {signal['rsi']}")
        
        # Trade logic
        in_position = symbol in account["open_positions"]
        
        if action == "BUY" and not in_position:
            account = paper_buy(symbol, current_price, account)
        
        elif action == "SELL" and in_position:
            account = paper_sell(symbol, current_price, account)
        
        else:
            print(f"   ⏸️  HOLD - No action")
    
    return account

def run_master_bot(cycles=3, delay=5):
    print("🚀 MASTER BOT STARTING...")
    print(f"   Symbols  : {SYMBOLS}")
    print(f"   Cycles   : {cycles}")
    
    account = load_paper_account()
    
    for i in range(cycles):
        print(f"\n🔄 Cycle {i+1}/{cycles}")
        account = run_bot_cycle(account)
        
        if i < cycles - 1:
            print(f"\n⏳ Next cycle in {delay}s...")
            time.sleep(delay)
    
    print("\n" + "="*40)
    print("📈 FINAL RESULTS:")
    show_summary(account)

if __name__ == "__main__":
    run_master_bot(cycles=3, delay=5)
