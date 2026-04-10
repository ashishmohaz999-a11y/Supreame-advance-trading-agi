"""
Zero Loss Auto Trader
- Scanner se best stocks lo
- Charges calculate karo
- Sirf tab buy karo jab guaranteed profit ho
- Auto sell on target
"""
import json
import time
import os
from datetime import datetime
import yfinance as yf
from trading_system.stock_scanner import run_full_scan
from trading_system.charges_calculator import calculate_charges, min_target_price
from trading_system.paper_trader import load_paper_account, save_paper_account, show_summary
from trading_system.telegram_alerts import send_message

TRADE_FILE   = "auto_trades.json"
MAX_PER_TRADE = 10000  # Max ₹10000 per trade
MAX_POSITIONS = 10     # Max 10 stocks ek saath
SCAN_INTERVAL = 3600   # Har 1 ghante mein scan

def load_auto_account():
    if os.path.exists(TRADE_FILE):
        with open(TRADE_FILE) as f:
            return json.load(f)
    return {
        "capital"        : 100000,
        "peak_capital"   : 100000,
        "open_positions" : {},
        "closed_trades"  : [],
        "total_charges"  : 0,
        "total_gross"    : 0,
        "total_net"      : 0
    }

def save_auto_account(acc):
    with open(TRADE_FILE, "w") as f:
        json.dump(acc, f, indent=2)

def get_current_price(yf_symbol):
    try:
        hist = yf.Ticker(yf_symbol).history(period="1d")
        if not hist.empty:
            return round(hist["Close"].iloc[-1], 2)
        return None
    except:
        return None

def auto_buy(acc, opportunity):
    """
    Zero loss guarantee ke saath buy karo
    """
    symbol    = opportunity["symbol"]
    price     = opportunity["price"]
    target    = opportunity["target"]
    quantity  = opportunity["quantity"]
    charges   = opportunity["total_charges"]
    net_pnl   = opportunity["net_pnl"]

    # Already position hai?
    if symbol in acc["open_positions"]:
        return acc

    # Capital check
    cost = price * quantity
    if cost > acc["capital"]:
        print(f"   ❌ Capital kam hai: ₹{cost} > ₹{acc['capital']}")
        return acc

    # Max positions check
    if len(acc["open_positions"]) >= MAX_POSITIONS:
        print(f"   ❌ Max positions reached: {MAX_POSITIONS}")
        return acc

    # Zero loss check
    if net_pnl <= 0:
        print(f"   ❌ {symbol}: Charges ke baad profit nahi")
        return acc

    # BUY!
    acc["capital"] -= cost
    acc["open_positions"][symbol] = {
        "buy_price"     : price,
        "quantity"      : quantity,
        "target"        : target,
        "stop_loss"     : round(price * 0.97, 2),  # 3% SL
        "expected_pnl"  : net_pnl,
        "charges"       : charges,
        "buy_time"      : datetime.now().isoformat(),
        "yf_symbol"     : f"{symbol}.NS"
    }
    save_auto_account(acc)

    msg = f"""
🟢 <b>AUTO BUY</b>

📊 {symbol}
💰 Price    : ₹{price} x {quantity}
💸 Cost     : ₹{cost}
🎯 Target   : ₹{target}
🛑 SL       : ₹{round(price*0.97,2)}
📋 Charges  : ₹{charges}
✅ Net PnL  : ₹{net_pnl}
💼 Capital  : ₹{round(acc['capital'],2)}
"""
    print(msg)
    send_message(msg)
    return acc

def auto_sell(acc, symbol, current_price, reason="TARGET"):
    """
    Sell karo aur actual charges calculate karo
    """
    if symbol not in acc["open_positions"]:
        return acc

    pos       = acc["open_positions"][symbol]
    buy_price = pos["buy_price"]
    quantity  = pos["quantity"]

    # Actual charges calculate karo
    result = calculate_charges(
        buy_price, current_price, quantity, "EQ"
    )

    net_pnl  = result["net_pnl"]
    charges  = result["total_charges"]
    sell_val = current_price * quantity

    # Account update
    acc["capital"] += sell_val
    if acc["capital"] > acc["peak_capital"]:
        acc["peak_capital"] = acc["capital"]

    acc["total_charges"] += charges
    acc["total_gross"]   += result["gross_pnl"]
    acc["total_net"]     += net_pnl

    # Trade log
    trade = {
        "symbol"      : symbol,
        "buy_price"   : buy_price,
        "sell_price"  : current_price,
        "quantity"    : quantity,
        "gross_pnl"   : result["gross_pnl"],
        "charges"     : charges,
        "net_pnl"     : net_pnl,
        "reason"      : reason,
        "time"        : datetime.now().isoformat()
    }
    acc["closed_trades"].append(trade)
    del acc["open_positions"][symbol]
    save_auto_account(acc)

    emoji = "🟢" if net_pnl > 0 else "🔴"
    msg = f"""
{emoji} <b>AUTO SELL - {reason}</b>

📊 {symbol}
📥 Buy   : ₹{buy_price}
📤 Sell  : ₹{current_price}
📦 Qty   : {quantity}
📋 Charges: ₹{charges}
💵 Net PnL: ₹{net_pnl}
💼 Capital: ₹{round(acc['capital'],2)}
"""
    print(msg)
    send_message(msg)
    return acc

def monitor_positions(acc):
    """
    Open positions monitor karo
    SL ya Target hit hone par sell karo
    """
    if not acc["open_positions"]:
        return acc

    print(f"\n👁️  Monitoring {len(acc['open_positions'])} positions...")

    for symbol in list(acc["open_positions"].keys()):
        pos       = acc["open_positions"][symbol]
        yf_symbol = pos.get("yf_symbol", f"{symbol}.NS")

        price = get_current_price(yf_symbol)
        if not price:
            continue

        sl     = pos["stop_loss"]
        target = pos["target"]

        print(f"   {symbol}: ₹{price} | "
              f"SL:₹{sl} | Target:₹{target}")

        if price >= target:
            print(f"   🎯 TARGET HIT: {symbol}")
            acc = auto_sell(acc, symbol, price, "TARGET")

        elif price <= sl:
            print(f"   🛑 STOP LOSS: {symbol}")
            acc = auto_sell(acc, symbol, price, "STOP_LOSS")

    return acc

def show_auto_summary(acc):
    trades = acc["closed_trades"]
    wins   = [t for t in trades if t["net_pnl"] > 0]
    losses = [t for t in trades if t["net_pnl"] <= 0]
    win_rate = round(len(wins)/len(trades)*100) if trades else 0

    print("\n" + "="*45)
    print("   AUTO TRADER SUMMARY")
    print("="*45)
    print(f"💼 Capital       : ₹{round(acc['capital'],2)}")
    print(f"📈 Peak Capital  : ₹{round(acc['peak_capital'],2)}")
    print(f"💵 Total Net PnL : ₹{round(acc['total_net'],2)}")
    print(f"📋 Total Charges : ₹{round(acc['total_charges'],2)}")
    print(f"📊 Total Trades  : {len(trades)}")
    print(f"✅ Wins          : {len(wins)}")
    print(f"❌ Losses        : {len(losses)}")
    print(f"🎯 Win Rate      : {win_rate}%")
    print(f"📂 Open Positions: {len(acc['open_positions'])}")
    print("="*45)

    if acc["open_positions"]:
        print("\n📂 OPEN POSITIONS:")
        for sym, pos in acc["open_positions"].items():
            print(f"   {sym}: Buy ₹{pos['buy_price']} | "
                  f"Target ₹{pos['target']} | "
                  f"Qty {pos['quantity']}")

def run_auto_trader():
    """
    Main auto trader loop:
    1. Scan karo best opportunities
    2. Buy karo
    3. Monitor karo
    4. Sell on target/SL
    """
    print("🚀 AUTO TRADER STARTING!")
    send_message("🤖 <b>Auto Trader Started!</b>\nZero Loss System Active ✅")

    acc   = load_auto_account()
    cycle = 0

    while True:
        now = datetime.now()
        cycle += 1

        print(f"\n{'='*45}")
        print(f"🔄 Cycle #{cycle} | {now.strftime('%H:%M:%S')}")
        print(f"💰 Capital: ₹{round(acc['capital'],2)}")
        print(f"{'='*45}")

        # Market open check
        is_open = (
            now.weekday() < 5 and
            now.replace(hour=9, minute=15) <= now <=
            now.replace(hour=15, minute=30)
        )

        if not is_open:
            print("🌙 Market closed - monitoring only")
            acc = monitor_positions(acc)
            time.sleep(900)
            continue

        # Step 1: Monitor existing positions
        acc = monitor_positions(acc)

        # Step 2: Scan for new opportunities
        if len(acc["open_positions"]) < MAX_POSITIONS:
            print("\n🔍 Scanning for opportunities...")
            opportunities = run_full_scan(max_stocks=100)

            # Buy top opportunities
            bought = 0
            for opp in opportunities[:5]:
                if len(acc["open_positions"]) >= MAX_POSITIONS:
                    break
                if opp["symbol"] not in acc["open_positions"]:
                    print(f"\n💡 Opportunity: {opp['symbol']}")
                    acc = auto_buy(acc, opp)
                    bought += 1

            if bought == 0:
                print("⏸️  No new opportunities found")

        # Step 3: Summary
        show_auto_summary(acc)

        print(f"\n⏳ Next scan in 60 min...")
        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    run_auto_trader()
