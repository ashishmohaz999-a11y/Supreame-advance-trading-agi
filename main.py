import time
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Sab modules import
from trading_system.strategy_engine import get_signal
from trading_system.risk_manager import evaluate_trade
from trading_system.paper_trader import (
    load_paper_account, paper_buy,
    paper_sell, show_summary
)
from trading_system.ai_signal import get_ai_signal
from trading_system.telegram_alerts import (
    alert_buy, alert_sell,
    alert_market_open, alert_market_close,
    alert_sl_hit, alert_target_hit
)

import yfinance as yf

# ===== CONFIG =====
SYMBOLS = {
    "RELIANCE" : "RELIANCE.NS",
    "TCS"      : "TCS.NS",
    "INFY"     : "INFY.NS",
    "HDFCBANK" : "HDFCBANK.NS",
    "SBIN"     : "SBIN.NS",
    "WIPRO"    : "WIPRO.NS"
}
CYCLE_DELAY  = 1800  # 30 min
LOG_FILE     = "logs/master_bot.log"
# ==================

os.makedirs("logs", exist_ok=True)

def log(msg):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def is_market_open():
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    open_t  = now.replace(hour=9,  minute=15, second=0)
    close_t = now.replace(hour=15, minute=30, second=0)
    return open_t <= now <= close_t

def get_data(symbol):
    """Yahoo Finance se live data lo"""
    try:
        yf_sym = SYMBOLS[symbol]
        hist   = yf.Ticker(yf_sym).history(period="1y")
        if hist.empty:
            return None, None
        closes = hist["Close"].tolist()
        return closes[-1], closes
    except Exception as e:
        log(f"❌ Data error {symbol}: {e}")
        return None, None

def run_cycle(account):
    log(f"\n{'='*45}")
    log(f"🤖 MASTER BOT CYCLE | {datetime.now().strftime('%H:%M:%S')}")
    log(f"💰 Capital: ₹{round(account['capital'],2)}")
    log(f"{'='*45}")

    for symbol in SYMBOLS.keys():
        log(f"\n📊 {symbol}...")

        price, history = get_data(symbol)
        if not price or not history or len(history) < 60:
            log(f"   ⚠️  Data unavailable")
            continue

        # === SIGNAL LAYER ===
        # 1. Technical Signal (RSI+EMA+MACD)
        tech = get_signal(history)
        tech_action = tech["action"]

        # 2. AI Signal (LSTM)
        ai_action, ai_pred, ai_change = get_ai_signal(history)

        # 3. Combined Decision
        # Dono BUY   → Strong BUY
        # Dono SELL  → Strong SELL
        # Conflict   → HOLD
        if tech_action == "BUY" and ai_action == "BUY":
            final_action = "BUY"
            confidence   = "HIGH 🔥"
        elif tech_action == "SELL" and ai_action == "SELL":
            final_action = "SELL"
            confidence   = "HIGH 🔥"
        elif tech_action == ai_action:
            final_action = tech_action
            confidence   = "MEDIUM ⚡"
        else:
            final_action = "HOLD"
            confidence   = "LOW ❄️"

        log(f"   Tech   : {tech_action} (RSI:{tech['rsi']})")
        log(f"   AI     : {ai_action} (Pred:₹{ai_pred} {ai_change}%)")
        log(f"   Final  : {final_action} | {confidence}")

        in_position = symbol in account["open_positions"]

        # === SL/TARGET CHECK ===
        if in_position:
            pos = account["open_positions"][symbol]
            sl  = pos["stop_loss"]
            tgt = pos["target"]
            qty = pos["quantity"]

            if price <= sl:
                pnl = round((price - pos["entry_price"]) * qty, 2)
                log(f"🛑 SL HIT: {symbol} @ ₹{price}")
                alert_sl_hit(symbol, price, abs(pnl))
                account = paper_sell(symbol, price, account)
                continue

            if price >= tgt:
                pnl = round((price - pos["entry_price"]) * qty, 2)
                log(f"🎯 TARGET: {symbol} @ ₹{price}")
                alert_target_hit(symbol, price, pnl)
                account = paper_sell(symbol, price, account)
                continue

        # === TRADE EXECUTION ===
        if final_action == "BUY" and not in_position:
            trade = evaluate_trade("BUY", price, account["capital"])
            if trade and trade["quantity"] > 0:
                account = paper_buy(symbol, price, account)
                pos = account["open_positions"].get(symbol, {})
                alert_buy(
                    symbol, price,
                    trade["quantity"],
                    trade["stop_loss"],
                    trade["target"],
                    round(account["capital"], 2)
                )

        elif final_action == "SELL" and in_position:
            pos = account["open_positions"][symbol]
            pnl = round(
                (price - pos["entry_price"]) * pos["quantity"], 2
            )
            account = paper_sell(symbol, price, account)
            alert_sell(
                symbol,
                pos["entry_price"],
                price,
                pos["quantity"],
                pnl,
                round(account["capital"], 2)
            )

        else:
            log(f"   ⏸️  HOLD")

    return account

def run_master():
    log("🚀 SUPREME TRADING AGI STARTED!")
    log(f"   Symbols  : {list(SYMBOLS.keys())}")
    log(f"   Strategy : RSI + EMA + MACD + LSTM AI")
    log(f"   Mode     : Paper Trading")
    log(f"   Cycle    : Every 30 minutes")

    alert_market_open()
    account = load_paper_account()
    day_start_capital = account["capital"]
    cycle = 0

    while True:
        if is_market_open():
            cycle += 1
            log(f"\n🔄 Cycle #{cycle}")
            account = run_cycle(account)
            log(f"\n⏳ Next cycle in 30 min...")
            time.sleep(CYCLE_DELAY)

        else:
            now = datetime.now()

            # Market close par daily summary
            if now.hour == 15 and now.minute >= 30:
                trades = account.get("trades", [])
                sells  = [t for t in trades if t["type"] == "SELL"]
                day_pnl = sum(t.get("pnl", 0) for t in sells)
                alert_market_close(
                    round(account["capital"], 2),
                    round(day_pnl, 2)
                )
                log("🌙 Market Closed! Daily summary sent.")
                show_summary(account)

            if now.weekday() >= 5:
                log("📅 Weekend - Waiting for Monday...")
            elif now.hour < 9:
                log("🌅 Waiting for market open (9:15 AM)...")
            else:
                log("🌙 Market closed for today.")

            time.sleep(900)  # 15 min check

if __name__ == "__main__":
    run_master()
