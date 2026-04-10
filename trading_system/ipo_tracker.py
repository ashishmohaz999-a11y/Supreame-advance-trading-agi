"""
IPO Tracker:
- Upcoming IPOs dekho
- GMP (Grey Market Premium) track karo
- Listing gain predict karo
- Auto apply recommendation
"""
import requests
import json
import time
from datetime import datetime
from trading_system.telegram_alerts import send_message

def get_upcoming_ipos():
    """NSE/BSE se upcoming IPOs fetch karo"""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        url = "https://www.nseindia.com/api/ipo-current-allotment"
        res = requests.get(url, headers=headers, timeout=10)

        if res.status_code == 200:
            data = res.json()
            print(f"✅ NSE IPOs fetched!")
            return data
    except Exception as e:
        print(f"❌ NSE error: {e}")

    # Backup - manual list
    return get_backup_ipos()

def get_backup_ipos():
    """Backup IPO data"""
    return [
        {
            "company"     : "Example Corp Ltd",
            "open_date"   : "2026-04-15",
            "close_date"  : "2026-04-17",
            "price_band"  : "₹100-₹120",
            "lot_size"    : 125,
            "issue_size"  : "₹500 Cr",
            "category"    : "SME",
            "min_amount"  : 15000,
            "gmp"         : 25,
            "rating"      : "APPLY"
        }
    ]

def calculate_ipo_profit(price, lot_size, gmp, brokerage=0):
    """
    IPO listing profit calculate karo
    GMP = Grey Market Premium
    """
    listing_price  = price + gmp
    buy_cost       = price * lot_size
    listing_value  = listing_price * lot_size
    gross_profit   = listing_value - buy_cost

    # Charges
    stt      = listing_value * 0.001
    exchange = (buy_cost + listing_value) * 0.0000345
    gst      = exchange * 0.18
    dp       = 15.93
    total_ch = stt + exchange + gst + dp

    net_profit  = gross_profit - total_ch
    profit_pct  = round(net_profit / buy_cost * 100, 2)
    is_apply    = net_profit > 0 and profit_pct > 2

    return {
        "price"        : price,
        "lot_size"     : lot_size,
        "gmp"          : gmp,
        "listing_price": listing_price,
        "buy_cost"     : round(buy_cost, 2),
        "gross_profit" : round(gross_profit, 2),
        "charges"      : round(total_ch, 2),
        "net_profit"   : round(net_profit, 2),
        "profit_pct"   : profit_pct,
        "recommendation": "✅ APPLY" if is_apply else "❌ SKIP"
    }

def analyze_ipo(ipo):
    """IPO ka full analysis karo"""
    print(f"\n{'='*45}")
    print(f"📊 {ipo.get('company', 'Unknown')}")
    print(f"{'='*45}")
    print(f"Open     : {ipo.get('open_date', 'N/A')}")
    print(f"Close    : {ipo.get('close_date', 'N/A')}")
    print(f"Price    : {ipo.get('price_band', 'N/A')}")
    print(f"Lot Size : {ipo.get('lot_size', 'N/A')}")
    print(f"Size     : {ipo.get('issue_size', 'N/A')}")
    print(f"GMP      : ₹{ipo.get('gmp', 0)}")

    # Price band se max price lo
    price_band = ipo.get("price_band", "100-100")
    try:
        price = int(str(price_band).replace("₹","")
                   .split("-")[-1].strip())
    except:
        price = 100

    lot_size = ipo.get("lot_size", 100)
    gmp      = ipo.get("gmp", 0)

    result = calculate_ipo_profit(price, lot_size, gmp)

    print(f"\n--- Profit Analysis ---")
    print(f"Buy Cost      : ₹{result['buy_cost']}")
    print(f"Listing Price : ₹{result['listing_price']}")
    print(f"Gross Profit  : ₹{result['gross_profit']}")
    print(f"Charges       : ₹{result['charges']}")
    print(f"Net Profit    : ₹{result['net_profit']}")
    print(f"Return        : {result['profit_pct']}%")
    print(f"\n{result['recommendation']}")

    return result

def track_listing(symbol, issue_price):
    """
    Listing day pe price track karo
    Best time pe sell karo
    """
    import yfinance as yf

    print(f"\n📈 Tracking {symbol} listing...")
    yf_sym = f"{symbol}.NS"

    best_price  = issue_price
    best_profit = 0

    for i in range(10):
        try:
            hist  = yf.Ticker(yf_sym).history(period="1d")
            if not hist.empty:
                current = round(hist["Close"].iloc[-1], 2)
                profit  = current - issue_price
                pct     = round(profit/issue_price*100, 2)

                print(f"   ₹{current} | "
                      f"Profit: ₹{profit} ({pct}%)")

                if current > best_price:
                    best_price  = current
                    best_profit = profit

                # 20%+ pe sell karo
                if pct >= 20:
                    msg = f"🎯 IPO SELL ALERT!\n{symbol}: ₹{current}\nProfit: {pct}%"
                    send_message(msg)
                    print(f"   🎯 SELL NOW! {pct}% profit!")
                    return current

        except Exception as e:
            print(f"   ❌ Error: {e}")

        time.sleep(300)  # 5 min wait

    return best_price

def run_ipo_monitor():
    """
    IPO monitor loop:
    - Upcoming IPOs check karo
    - GMP dekho
    - Apply/Skip recommend karo
    - Listing pe track karo
    """
    print("🚀 IPO TRACKER STARTING!")

    while True:
        print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')}")
        print("📋 Fetching IPOs...")

        ipos = get_upcoming_ipos()

        apply_list = []
        skip_list  = []

        for ipo in ipos:
            result = analyze_ipo(ipo)
            if "APPLY" in result["recommendation"]:
                apply_list.append(ipo)
            else:
                skip_list.append(ipo)

        # Telegram summary
        if apply_list:
            msg = "📋 <b>IPO ALERT!</b>\n\n"
            for ipo in apply_list:
                msg += f"✅ <b>{ipo.get('company','')}</b>\n"
                msg += f"   Price : {ipo.get('price_band','')}\n"
                msg += f"   Close : {ipo.get('close_date','')}\n"
                msg += f"   GMP   : ₹{ipo.get('gmp',0)}\n\n"
            send_message(msg)

        print(f"\n✅ Apply : {len(apply_list)} IPOs")
        print(f"❌ Skip  : {len(skip_list)} IPOs")

        # 6 ghante baad check
        print("\n⏳ Next check in 6 hours...")
        time.sleep(21600)

if __name__ == "__main__":
    # Single IPO test
    print("=== IPO PROFIT CALCULATOR ===")
    result = calculate_ipo_profit(
        price=100,
        lot_size=150,
        gmp=30
    )
    print(f"Buy Cost     : ₹{result['buy_cost']}")
    print(f"Net Profit   : ₹{result['net_profit']}")
    print(f"Return       : {result['profit_pct']}%")
    print(f"Recommend    : {result['recommendation']}")

    print("\n=== UPCOMING IPOs ===")
    ipos = get_upcoming_ipos()
    for ipo in ipos:
        analyze_ipo(ipo)
