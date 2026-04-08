import json
import time
import yfinance as yf
from datetime import datetime
from trading_system.strategy_engine import get_signal
from trading_system.paper_trader import (
    load_paper_account, paper_buy,
    paper_sell, show_summary
)

# Yahoo Finance symbols (NSE)
SYMBOLS = {
    "RELIANCE": "RELIANCE.NS",
    "TCS"     : "TCS.NS",
    "INFY"    : "INFY.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "SBIN"    : "SBIN.NS",
    "WIPRO"   : "WIPRO.NS"
}

def get_live_data(symbol):
    """Yahoo Finance se free live data"""
    try:
        yf_symbol = SYMBOLS[symbol]
        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(period="60d")
        
        if hist.empty:
            print(f"   ⚠️  No data for {symbol}")
            return None, None
        
        closes = hist["Close"].tolist()
        price = closes[-1]
        print(f"📡 {symbol}: ₹{round(price,2)}")
        return price, closes
    except Exception as e:
        print(f"❌ Error {symbol}: {e}")
        return None, None

def run_live_cycle(account):
    print(f"\n{'='*40}")
    print(f"🤖 LIVE: {datetime.now().strftime('%H:%M:%S')}")
    print(f"💰 Capital: ₹{round(account['capital'],2)}")
    print(f"{'='*40}")

    for symbol in SYMBOLS.keys():
        print(f"\n📊 {symbol}...")

        price, history = get_live_data(symbol)

        if not price or not history or len(history) < 20:
            print(f"   ⚠️  Data unavailable")
            continue

        signal = get_signal(history)
        action = signal["action"]
        print(f"   Signal: {action} | RSI: {signal['rsi']}")

        in_position = symbol in account["open_positions"]

        if in_position:
            pos = account["open_positions"][symbol]
            if price <= pos["stop_loss"]:
                print(f"🛑 SL HIT: {symbol}")
                account = paper_sell(symbol, price, account)
                continue
            if price >= pos["target"]:
                print(f"🎯 TARGET: {symbol}")
                account = paper_sell(symbol, price, account)
                continue

        if action == "BUY" and not in_position:
            account = paper_buy(symbol, price, account)
        elif action == "SELL" and in_position:
            account = paper_sell(symbol, price, account)
        else:
            print(f"   ⏸️  HOLD")

    return account

def run_live_bot(cycles=3, delay=30):
    print("🚀 LIVE BOT STARTING! (Yahoo Finance)")
    account = load_paper_account()

    for i in range(cycles):
        print(f"\n🔄 Cycle {i+1}/{cycles}")
        account = run_live_cycle(account)
        if i < cycles - 1:
            print(f"\n⏳ {delay}s wait...")
            time.sleep(delay)

    print("\n📈 FINAL RESULTS:")
    show_summary(account)

if __name__ == "__main__":
    run_live_bot(cycles=3, delay=30)
