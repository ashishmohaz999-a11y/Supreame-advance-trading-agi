import pandas as pd
import numpy as np

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_ema(prices, period):
    return prices.ewm(span=period, adjust=False).mean()

def calculate_macd(prices):
    ema12 = calculate_ema(prices, 12)
    ema26 = calculate_ema(prices, 26)
    macd = ema12 - ema26
    signal = calculate_ema(macd, 9)
    return macd, signal

def get_signal(prices_list):
    prices = pd.Series(prices_list)
    
    rsi = calculate_rsi(prices).iloc[-1]
    ema9 = calculate_ema(prices, 9).iloc[-1]
    ema21 = calculate_ema(prices, 21).iloc[-1]
    macd, signal = calculate_macd(prices)
    macd_val = macd.iloc[-1]
    signal_val = signal.iloc[-1]
    
    score = 0
    
    # RSI Logic
    if rsi < 35:
        score += 2   # Oversold = BUY
    elif rsi > 65:
        score -= 2   # Overbought = SELL
    
    # EMA Logic
    if ema9 > ema21:
        score += 1   # Uptrend
    else:
        score -= 1   # Downtrend
    
    # MACD Logic
    if macd_val > signal_val:
        score += 1   # Bullish
    else:
        score -= 1   # Bearish
    
    # Final Decision
    if score >= 2:
        action = "BUY"
    elif score <= -2:
        action = "SELL"
    else:
        action = "HOLD"
    
    return {
        "action": action,
        "score": score,
        "rsi": round(rsi, 2),
        "ema9": round(ema9, 2),
        "ema21": round(ema21, 2),
        "macd": round(macd_val, 4)
    }

if __name__ == "__main__":
    # Test data
    import random
    prices = [100 + random.uniform(-5, 5) for _ in range(50)]
    result = get_signal(prices)
    print("=== Strategy Signal ===")
    for k, v in result.items():
        print(f"{k}: {v}")
