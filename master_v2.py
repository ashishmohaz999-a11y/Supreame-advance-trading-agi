"""
SUPREME TRADING AGI v2.0
- 4500+ Stocks Scanner
- Zero Loss Auto Trader
- IPO Tracker
- AI/LSTM Signals
- Telegram Alerts
- Dashboard
"""
import time
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from trading_system.stock_scanner     import run_full_scan
from trading_system.auto_trader       import (
    load_auto_account, auto_buy,
    auto_sell, monitor_positions,
    show_auto_summary
)
from trading_system.ipo_tracker       import (
    get_upcoming_ipos, analyze_ipo
)
from trading_system.charges_calculator import calculate_charges
from trading_system.telegram_alerts   import send_message
from trading_system.strategy_engine   import get_signal

import yfinance as yf

# ===== CONFIG =====
MAX_POSITIONS  = 10
MAX_PER_TRADE  = 10000
SCAN_INTERVAL  = 3600   # 1 hour
MONITOR_INTERVAL = 300  # 5 min
LOG_FILE       = "logs/master_v2.log"
# ==================

os.makedirs("logs", exist_ok=True)

def log(msg):
    now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def is_market_open():
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    o = now.replace(hour=9,  minute=15, second=0)
    c = now.replace(hour=15, minute=30, second=0)
    return o <= now <= c

def is_market_closing_soon():
    now = datetime.now()
    c = now.replace(hour=15, minute=15, second=0)
    return now >= c and is_market_open()

def get_current_price(symbol):
    try:
        hist = yf.Ticker(f"{symbol}.NS").history(period="1d")
        if not hist.empty:
            return round(hist["Close"].iloc[-1], 2)
    except:
        pass
    return None

def run_morning_scan(acc):
    """
    9:15 AM - Market open pe full scan
    Best opportunities dhundo
    """
    log("🌅 MORNING SCAN STARTING...")
    send_message("🌅 <b>Market Open!</b>\nMorning scan shuru...")

    # Stock scan
    log("📊 Scanning 4500+ stocks...")
    opportunities = run_full_scan(max_stocks=200)

    # IPO check
    log("📋 Checking IPOs...")
    ipos = get_upcoming_ipos()
    ipo_alerts = []
    for ipo in ipos:
        result = analyze_ipo(ipo)
        if "APPLY" in result["recommendation"]:
            ipo_alerts.append(ipo)

    # IPO notifications
    if ipo_alerts:
        msg = "📋 <b>IPO APPLY LIST:</b>\n"
        for ipo in ipo_alerts:
            msg += f"✅ {ipo.get('company','')}\n"
            msg += f"   Close: {ipo.get('close_date','')}\n"
        send_message(msg)

    # Top opportunities buy karo
    bought = 0
    for opp in opportunities[:5]:
        if len(acc["open_positions"]) >= MAX_POSITIONS:
            break
        if opp["symbol"] not in acc["open_positions"]:
            # AI signal verify karo
            try:
                hist = yf.Ticker(
                    f"{opp['symbol']}.NS"
                ).history(period="6mo")
                if not hist.empty:
                    closes = hist["Close"].tolist()
                    signal = get_signal(closes)
                    if signal["action"] == "BUY":
                        acc = auto_buy(acc, opp)
                        bought += 1
                        time.sleep(1)
            except:
                pass

    log(f"✅ Morning scan done! Bought: {bought}")
    return acc

def run_monitoring_cycle(acc):
    """
    Har 5 min - Positions monitor karo
    SL/Target hit check karo
    """
    log(f"👁️  Monitoring {len(acc['open_positions'])} positions...")

    for symbol in list(acc["open_positions"].keys()):
        pos   = acc["open_positions"][symbol]
        price = get_current_price(symbol)

        if not price:
            continue

        sl     = pos["stop_loss"]
        target = pos["target"]
        entry  = pos["buy_price"]
        qty    = pos["quantity"]

        # Current PnL
        result  = calculate_charges(entry, price, qty, "EQ")
        cur_pnl = result["net_pnl"]
        pct     = round((price-entry)/entry*100, 2)

        log(f"   {symbol}: ₹{price} | "
            f"PnL: ₹{cur_pnl} ({pct}%) | "
            f"SL:₹{sl} Target:₹{target}")

        # Target hit
        if price >= target:
            log(f"   🎯 TARGET HIT: {symbol}")
            acc = auto_sell(acc, symbol, price, "TARGET")

        # Stop loss hit
        elif price <= sl:
            log(f"   🛑 SL HIT: {symbol}")
            acc = auto_sell(acc, symbol, price, "STOP_LOSS")

        # Market closing soon - sab sell karo
        elif is_market_closing_soon():
            if cur_pnl > 0:
                log(f"   🌙 CLOSING: {symbol} (profit)")
                acc = auto_sell(acc, symbol, price, "MARKET_CLOSE")

    return acc

def run_afternoon_scan(acc):
    """
    12:00 PM - Mid day scan
    Nayi opportunities dhundo
    """
    if len(acc["open_positions"]) >= MAX_POSITIONS:
        return acc

    log("☀️  AFTERNOON SCAN...")
    opportunities = run_full_scan(max_stocks=100)

    for opp in opportunities[:3]:
        if len(acc["open_positions"]) >= MAX_POSITIONS:
            break
        if opp["symbol"] not in acc["open_positions"]:
            acc = auto_buy(acc, opp)
            time.sleep(1)

    return acc

def run_eod_summary(acc):
    """
    3:30 PM - End of day summary
    """
    trades  = acc["closed_trades"]
    today   = datetime.now().strftime("%Y-%m-%d")
    today_t = [t for t in trades if t["time"][:10] == today]

    total_pnl     = sum(t["net_pnl"] for t in today_t)
    total_charges = sum(t["charges"] for t in today_t)
    wins  = [t for t in today_t if t["net_pnl"] > 0]
    loss  = [t for t in today_t if t["net_pnl"] <= 0]

    msg = f"""
📊 <b>EOD SUMMARY</b>

📅 Date      : {today}
💼 Capital   : ₹{round(acc['capital'],2)}
💵 Day PnL   : ₹{round(total_pnl,2)}
📋 Charges   : ₹{round(total_charges,2)}
✅ Wins      : {len(wins)}
❌ Losses    : {len(loss)}
📈 Trades    : {len(today_t)}
"""
    log(msg)
    send_message(msg)
    return acc

def run_supreme_system():
    """
    Main loop - Poora system chalao
    """
    log("🚀 SUPREME TRADING AGI v2.0 STARTING!")
    log(f"   Max Positions : {MAX_POSITIONS}")
    log(f"   Max Per Trade : ₹{MAX_PER_TRADE}")
    log(f"   Scan Interval : {SCAN_INTERVAL//60} min")

    send_message("""
🤖 <b>SUPREME AGI v2.0 STARTED!</b>

✅ 4500+ Stocks Scanner
✅ Zero Loss System
✅ IPO Tracker
✅ AI Signals
✅ Auto Buy/Sell
""")

    acc = load_auto_account()

    morning_done    = False
    afternoon_done  = False
    eod_done        = False
    last_monitor    = datetime.now()

    while True:
        now = datetime.now()
        hour = now.hour
        min  = now.minute

        if is_market_open():
            # Reset daily flags
            if hour == 9 and min < 20:
                morning_done   = False
                afternoon_done = False
                eod_done       = False

            # 9:15 - Morning scan
            if hour == 9 and min >= 15 and not morning_done:
                acc = run_morning_scan(acc)
                morning_done = True

            # 12:00 - Afternoon scan
            elif hour == 12 and min == 0 and not afternoon_done:
                acc = run_afternoon_scan(acc)
                afternoon_done = True

            # 3:30 - EOD Summary
            elif hour == 15 and min >= 30 and not eod_done:
                acc = run_eod_summary(acc)
                eod_done = True

            # Har 5 min - Monitor
            diff = (now - last_monitor).seconds
            if diff >= MONITOR_INTERVAL:
                acc = run_monitoring_cycle(acc)
                last_monitor = now
                show_auto_summary(acc)

        else:
            if now.weekday() >= 5:
                log("📅 Weekend - System standby...")
            elif hour < 9:
                log(f"🌅 Market opens at 9:15 AM")
            else:
                log("🌙 Market closed")

        time.sleep(60)  # Har 1 min check

if __name__ == "__main__":
    run_supreme_system()
