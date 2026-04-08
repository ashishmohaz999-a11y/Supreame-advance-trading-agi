import json
import os
from datetime import datetime
from trading_system.strategy_engine import get_signal
from trading_system.risk_manager import evaluate_trade

PAPER_FILE = "paper_trades.json"

def load_paper_account():
    if os.path.exists(PAPER_FILE):
        with open(PAPER_FILE) as f:
            return json.load(f)
    return {
        "capital": 100000,
        "peak_capital": 100000,
        "trades": [],
        "open_positions": {}
    }

def save_paper_account(account):
    with open(PAPER_FILE, "w") as f:
        json.dump(account, f, indent=2)

def paper_buy(symbol, price, account):
    signal_data = {"action": "BUY", "entry": price}
    trade = evaluate_trade("BUY", price, account["capital"])
    
    if not trade or trade["quantity"] == 0:
        print(f"❌ {symbol}: Capital insufficient")
        return account

    cost = price * trade["quantity"]
    if cost > account["capital"]:
        print(f"❌ {symbol}: Not enough capital")
        return account

    account["capital"] -= cost
    account["open_positions"][symbol] = {
        "quantity": trade["quantity"],
        "entry_price": price,
        "stop_loss": trade["stop_loss"],
        "target": trade["target"],
        "entry_time": datetime.now().isoformat()
    }

    log = {
        "type": "BUY",
        "symbol": symbol,
        "price": price,
        "quantity": trade["quantity"],
        "cost": cost,
        "stop_loss": trade["stop_loss"],
        "target": trade["target"],
        "time": datetime.now().isoformat()
    }
    account["trades"].append(log)
    save_paper_account(account)

    print(f"\n✅ PAPER BUY: {symbol}")
    print(f"   Price    : ₹{price}")
    print(f"   Qty      : {trade['quantity']}")
    print(f"   Cost     : ₹{cost}")
    print(f"   SL       : ₹{trade['stop_loss']}")
    print(f"   Target   : ₹{trade['target']}")
    print(f"   Capital  : ₹{round(account['capital'],2)}")
    return account

def paper_sell(symbol, price, account):
    if symbol not in account["open_positions"]:
        print(f"❌ {symbol}: No open position")
        return account

    pos = account["open_positions"][symbol]
    qty = pos["quantity"]
    entry = pos["entry_price"]
    pnl = round((price - entry) * qty, 2)

    account["capital"] += price * qty
    if account["capital"] > account["peak_capital"]:
        account["peak_capital"] = account["capital"]

    log = {
        "type": "SELL",
        "symbol": symbol,
        "price": price,
        "quantity": qty,
        "pnl": pnl,
        "time": datetime.now().isoformat()
    }
    account["trades"].append(log)
    del account["open_positions"][symbol]
    save_paper_account(account)

    emoji = "🟢" if pnl > 0 else "🔴"
    print(f"\n{emoji} PAPER SELL: {symbol}")
    print(f"   Entry    : ₹{entry}")
    print(f"   Exit     : ₹{price}")
    print(f"   Qty      : {qty}")
    print(f"   PnL      : ₹{pnl}")
    print(f"   Capital  : ₹{round(account['capital'],2)}")
    return account

def show_summary(account):
    trades = account["trades"]
    sells = [t for t in trades if t["type"] == "SELL"]
    total_pnl = sum(t["pnl"] for t in sells)
    wins = [t for t in sells if t["pnl"] > 0]
    
    print("\n" + "="*35)
    print("   PAPER TRADING SUMMARY")
    print("="*35)
    print(f"Capital     : ₹{round(account['capital'],2)}")
    print(f"Total Trades: {len(sells)}")
    print(f"Wins        : {len(wins)}")
    print(f"Losses      : {len(sells)-len(wins)}")
    print(f"Total PnL   : ₹{round(total_pnl,2)}")
    print(f"Open Pos    : {list(account['open_positions'].keys())}")
    print("="*35)

if __name__ == "__main__":
    acc = load_paper_account()
    
    # Test trades
    acc = paper_buy("RELIANCE", 2850.0, acc)
    acc = paper_buy("TCS", 3500.0, acc)
    acc = paper_sell("RELIANCE", 2920.0, acc)
    acc = paper_sell("TCS", 3420.0, acc)
    
    show_summary(acc)
