import json
import numpy as np

def get_available_capital():
    try:
        with open("token_store.json") as f:
            data = json.load(f)
        return float(data.get("capital", 10000))
    except:
        return 10000

def kelly_position_size(capital, win_rate=0.55, risk_reward=2.0):
    """Kelly Criterion - Optimal position size"""
    kelly = win_rate - ((1 - win_rate) / risk_reward)
    kelly = max(0, min(kelly, 0.25))  # Max 25% capital
    return round(capital * kelly, 2)

def calculate_var(returns_list, confidence=0.95):
    """Value at Risk calculation"""
    if len(returns_list) < 10:
        return 0
    returns = np.array(returns_list)
    var = np.percentile(returns, (1 - confidence) * 100)
    return round(abs(var), 4)

def check_drawdown(peak_capital, current_capital):
    """Drawdown protection"""
    if peak_capital == 0:
        return 0, True
    drawdown = (peak_capital - current_capital) / peak_capital * 100
    is_safe = drawdown < 10  # Max 10% drawdown allowed
    return round(drawdown, 2), is_safe

def get_stop_loss(entry_price, action, risk_pct=0.02):
    """Dynamic stop loss - 2% default"""
    if action == "BUY":
        return round(entry_price * (1 - risk_pct), 2)
    else:
        return round(entry_price * (1 + risk_pct), 2)

def get_target(entry_price, action, reward_pct=0.04):
    """Target price - 4% default (2:1 RR)"""
    if action == "BUY":
        return round(entry_price * (1 + reward_pct), 2)
    else:
        return round(entry_price * (1 - reward_pct), 2)

def evaluate_trade(action, entry_price, capital):
    """Full trade risk evaluation"""
    position_size = kelly_position_size(capital)
    quantity = int(position_size / entry_price)
    stop_loss = get_stop_loss(entry_price, action)
    target = get_target(entry_price, action)
    max_loss = round(abs(entry_price - stop_loss) * quantity, 2)
    max_profit = round(abs(target - entry_price) * quantity, 2)

    print(f"\n=== Risk Evaluation ===")
    print(f"Action      : {action}")
    print(f"Entry Price : ₹{entry_price}")
    print(f"Capital     : ₹{capital}")
    print(f"Position    : ₹{position_size}")
    print(f"Quantity    : {quantity} shares")
    print(f"Stop Loss   : ₹{stop_loss}")
    print(f"Target      : ₹{target}")
    print(f"Max Loss    : ₹{max_loss}")
    print(f"Max Profit  : ₹{max_profit}")

    if quantity == 0:
        print("❌ Capital too low for this trade")
        return None

    return {
        "action": action,
        "entry": entry_price,
        "quantity": quantity,
        "stop_loss": stop_loss,
        "target": target,
        "max_loss": max_loss,
        "max_profit": max_profit
    }

if __name__ == "__main__":
    capital = get_available_capital()
    result = evaluate_trade("BUY", 1500.0, capital)
    print("\n✅ Risk check complete!")
