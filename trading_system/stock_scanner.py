"""
NSE 4500+ Stocks Scanner
- Sabhi stocks scan karo
- Sirf best opportunities dhundo
- Zero loss filter lagao
"""
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import time
import json
import os
from datetime import datetime
from trading_system.strategy_engine import get_signal
from trading_system.charges_calculator import (
    calculate_charges, min_target_price
)

# ===== NSE ALL STOCKS FETCH =====
def get_all_nse_stocks():
    """NSE se sabhi 4500+ stocks ki list lo"""
    try:
        # NSE official list
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/json"
        }

        # NSE equity list
        url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        df  = pd.read_csv(url)
        
        symbols = []
        for sym in df["SYMBOL"].tolist():
            symbols.append({
                "symbol"  : sym,
                "yf_symbol": f"{sym}.NS",
                "name"    : df[df["SYMBOL"]==sym]["NAME OF COMPANY"].values[0]
                            if "NAME OF COMPANY" in df.columns else sym
            })
        
        print(f"✅ NSE Total Stocks: {len(symbols)}")
        
        # Save karo
        with open("nse_stocks.json", "w") as f:
            json.dump(symbols, f)
        
        return symbols

    except Exception as e:
        print(f"❌ NSE fetch error: {e}")
        print("📋 Backup list use kar raha hoon...")
        return get_backup_stocks()

def get_backup_stocks():
    """Agar NSE down ho to backup list"""
    
    # Top NSE stocks by category
    stocks = [
        # NIFTY 50
        "RELIANCE","TCS","HDFCBANK","INFY","ICICIBANK",
        "HINDUNILVR","ITC","SBIN","BHARTIARTL","KOTAKBANK",
        "LT","AXISBANK","ASIANPAINT","MARUTI","TITAN",
        "SUNPHARMA","ULTRACEMCO","BAJFINANCE","WIPRO","NESTLEIND",
        "TECHM","POWERGRID","NTPC","ONGC","HCLTECH",
        "TATASTEEL","JSWSTEEL","INDUSINDBK","BAJAJ-AUTO","GRASIM",
        
        # NIFTY NEXT 50
        "ADANIENT","ADANIPORTS","AMBUJACEM","AUROPHARMA","BAJAJFINSV",
        "BANKBARODA","BEL","BERGEPAINT","BOSCHLTD","BRITANNIA",
        "CHOLAFIN","CIPLA","COLPAL","DABUR","DLF",
        "EICHERMOT","GAIL","GODREJCP","HAVELLS","HEROMOTOCO",
        "HINDALCO","HINDPETRO","ICICIPRULI","IDFCFIRSTB","IOC",
        
        # MIDCAP
        "ABCAPITAL","ABFRL","APOLLOHOSP","ASHOKLEY","ASTRAL",
        "ATUL","AUBANK","BALKRISIND","BATAINDIA","BHARATFORG",
        "BIOCON","CADILAHC","CANFINHOME","CARBORUNIV","CASTROLIND",
        "CEATLTD","CENTURYTEX","CGPOWER","CHAMBLFERT","CONCOR",
        "COROMANDEL","CUMMINSIND","CYIENT","DEEPAKNTR","DELTACORP",
        
        # SMALLCAP
        "AAVAS","ABSL","ACCELYA","ADANIGAS","ADANITRANS",
        "AFFLE","AGCNET","AHLUCONT","AIAENG","AJANTPHARM",
        "ALKEM","ALKYLAMINE","ALLCARGO","AMBER","AMCREDY",
        "ANGELONE","ANURAS","APOLLOPIPE","APTUS","ARVINDFASN",
        
        # BANKING
        "AUBANK","BANDHANBNK","CUB","DCBBANK","FEDERALBNK",
        "IDBI","IDFCFIRSTB","INDUSINDBK","J&KBANK","KARURVYSYA",
        "LAKSHVILAS","MAHABANK","NAINITAL","PNB","RBLBANK",
        "SOUTHBANK","TMVFINANCE","UCOBANK","UJJIVANSFB","YESBANK",
        
        # PHARMA
        "ABIOCHEM","ABBOTINDIA","AJANTPHARM","ALEMBICLTD","ALKEM",
        "APLLTD","AUROPHARMA","BIOCON","BLISSGVS","CAPLIPOINT",
        "CENTURYPLY","CIPLA","DIVI","DRREDDY","ERIS",
        "GLAND","GLAXO","GRANULES","GUJGASLTD","IPCA",
        
        # IT
        "COFORGE","HAPPSTMNDS","HEXAWARE","INFY","KPITTECH",
        "LTIM","LTTS","MASTEK","MINDTREE","MPHASIS",
        "NAUKRI","NIITTECH","OFSS","PERSISTENT","ROUTE",
        "SONATSOFTW","SUBEXLTD","TANLA","TCS","TECHM",
        
        # AUTO
        "AMARAJABAT","APOLLOTYRE","ASHOKLEY","BAJAJ-AUTO","BALKRISIND",
        "BOSCHLTD","EICHERMOT","ESCORTS","EXIDEIND","FORCEMOT",
        "HEROMOTOCO","MAHINDCIE","MARUTI","MRF","MOTHERSON",
        "ROLLCONTA","SUPRAJIT","TATAMOTORS","TVSMOTOR","WABCOINDIA"
    ]
    
    result = [{"symbol": s, "yf_symbol": f"{s}.NS", "name": s} 
              for s in stocks]
    print(f"✅ Backup stocks loaded: {len(result)}")
    return result

# ===== STOCK SCREENER =====
def screen_stock(stock_info):
    """
    Ek stock ko screen karo:
    1. Data lo
    2. Signal check karo
    3. Charges calculate karo
    4. Zero loss check karo
    """
    symbol    = stock_info["symbol"]
    yf_symbol = stock_info["yf_symbol"]

    try:
        # Data fetch
        ticker = yf.Ticker(yf_symbol)
        hist   = ticker.history(period="6mo")

        if hist.empty or len(hist) < 30:
            return None

        closes       = hist["Close"].tolist()
        current_price= round(closes[-1], 2)
        volume       = hist["Volume"].iloc[-1]

        # Low volume skip karo
        avg_volume = hist["Volume"].mean()
        if volume < 10000 or avg_volume < 50000:
            return None

        # Strategy signal
        signal = get_signal(closes)
        if signal["action"] != "BUY":
            return None

        # Capital se quantity calculate karo
        capital  = 10000  # Per trade capital
        quantity = max(1, int(capital / current_price))
        
        # Min target calculate karo
        target, charges = min_target_price(
            current_price, quantity, "EQ", min_profit=1
        )

        if not target:
            return None

        target_pct = round(
            (target - current_price) / current_price * 100, 2
        )

        # Sirf wo stocks jo 5% se kam mein target hit karen
        if target_pct > 5:
            return None

        return {
            "symbol"      : symbol,
            "name"        : stock_info.get("name", symbol),
            "price"       : current_price,
            "quantity"    : quantity,
            "target"      : target,
            "target_pct"  : target_pct,
            "rsi"         : signal["rsi"],
            "total_charges": charges["total_charges"],
            "net_pnl"     : charges["net_pnl"],
            "volume"      : int(volume),
            "signal_score": signal["score"]
        }

    except Exception as e:
        return None

def run_full_scan(max_stocks=500, save_results=True):
    """
    Sabhi stocks scan karo
    Best opportunities return karo
    """
    print("=" * 50)
    print(f"🔍 FULL NSE SCAN STARTING")
    print(f"   Time  : {datetime.now().strftime('%H:%M:%S')}")
    print(f"   Stocks: {max_stocks}")
    print("=" * 50)

    # Stock list lo
    if os.path.exists("nse_stocks.json"):
        with open("nse_stocks.json") as f:
            all_stocks = json.load(f)
        print(f"✅ Loaded {len(all_stocks)} stocks from cache")
    else:
        all_stocks = get_all_nse_stocks()

    # Limit lagao
    stocks_to_scan = all_stocks[:max_stocks]
    
    opportunities = []
    scanned       = 0
    errors        = 0

    for i, stock in enumerate(stocks_to_scan):
        result = screen_stock(stock)
        scanned += 1

        if result:
            opportunities.append(result)
            print(f"✅ {result['symbol']:15} | "
                  f"₹{result['price']:8} | "
                  f"Target: ₹{result['target']} "
                  f"(+{result['target_pct']}%) | "
                  f"PnL: ₹{result['net_pnl']}")

        # Progress
        if (i+1) % 50 == 0:
            print(f"\n📊 Progress: {i+1}/{len(stocks_to_scan)} | "
                  f"Found: {len(opportunities)}\n")

        # Rate limit
        time.sleep(0.1)

    # Sort by best opportunity
    opportunities.sort(
        key=lambda x: x["net_pnl"], reverse=True
    )

    # Save results
    if save_results:
        with open("scan_results.json", "w") as f:
            json.dump(opportunities, f, indent=2)
        print(f"\n✅ Results saved: scan_results.json")

    # Summary
    print("\n" + "=" * 50)
    print(f"📊 SCAN COMPLETE!")
    print(f"   Scanned      : {scanned}")
    print(f"   Opportunities: {len(opportunities)}")
    print(f"=" * 50)

    if opportunities:
        print(f"\n🏆 TOP 10 OPPORTUNITIES:")
        print(f"{'Symbol':15} {'Price':8} {'Target':8} {'%':6} {'Net PnL':10}")
        print("-" * 55)
        for o in opportunities[:10]:
            print(f"{o['symbol']:15} "
                  f"₹{o['price']:7} "
                  f"₹{o['target']:7} "
                  f"+{o['target_pct']:5}% "
                  f"₹{o['net_pnl']:8}")

    return opportunities

if __name__ == "__main__":
    # Pehle NSE list download karo
    print("📥 NSE stocks list fetch ho rahi hai...")
    get_all_nse_stocks()
    
    # Phir scan karo
    results = run_full_scan(max_stocks=200)
