"""
India ke sabhi trading charges calculate karo
Sirf tab trade karo jab GUARANTEED profit ho
"""

def calculate_charges(buy_price, sell_price, quantity, segment="EQ"):
    """
    Har trade ke exact charges calculate karo
    
    Segments:
    EQ    = Equity Delivery
    INTRA = Intraday
    FO    = Futures & Options
    """
    
    buy_value  = buy_price  * quantity
    sell_value = sell_price * quantity
    gross_pnl  = sell_value - buy_value

    if segment == "INTRA":
        # Intraday
        brokerage = min(buy_value  * 0.0003, 20) + \
                    min(sell_value * 0.0003, 20)
        stt       = sell_value * 0.00025  # Sirf sell pe
    else:
        # Delivery
        brokerage = 0  # Dhan free delivery
        stt       = (buy_value + sell_value) * 0.001

    # Exchange charges
    exchange  = (buy_value + sell_value) * 0.0000345

    # SEBI charges
    sebi      = (buy_value + sell_value) * 0.000001

    # GST (18% on brokerage + exchange)
    gst       = (brokerage + exchange) * 0.18

    # Stamp duty (sirf buy pe)
    stamp     = buy_value * 0.00015

    # DP charges (delivery sell pe)
    dp        = 15.93 if segment == "EQ" else 0

    total_charges = brokerage + stt + exchange + \
                    sebi + gst + stamp + dp

    net_pnl    = gross_pnl - total_charges
    breakeven  = (total_charges / buy_value) * 100

    return {
        "buy_value"     : round(buy_value, 2),
        "sell_value"    : round(sell_value, 2),
        "gross_pnl"     : round(gross_pnl, 2),
        "brokerage"     : round(brokerage, 2),
        "stt"           : round(stt, 2),
        "exchange"      : round(exchange, 2),
        "sebi"          : round(sebi, 2),
        "gst"           : round(gst, 2),
        "stamp"         : round(stamp, 2),
        "dp"            : round(dp, 2),
        "total_charges" : round(total_charges, 2),
        "net_pnl"       : round(net_pnl, 2),
        "breakeven_pct" : round(breakeven, 3),
        "is_profitable" : net_pnl > 0
    }

def min_target_price(buy_price, quantity, segment="EQ", min_profit=1):
    """
    Minimum price calculate karo jahan
    GUARANTEED ek rupee bhi loss na ho
    """
    for target in range(int(buy_price), int(buy_price * 1.20)):
        result = calculate_charges(
            buy_price, target, quantity, segment
        )
        if result["net_pnl"] >= min_profit:
            return target, result
    return None, None

if __name__ == "__main__":
    print("=" * 45)
    print("   ZERO LOSS CALCULATOR")
    print("=" * 45)

    # Example: RELIANCE
    buy   = 1350
    qty   = 10
    sell  = 1400

    result = calculate_charges(buy, sell, qty, "EQ")

    print(f"\nStock    : RELIANCE")
    print(f"Buy      : ₹{buy} x {qty} = ₹{result['buy_value']}")
    print(f"Sell     : ₹{sell} x {qty} = ₹{result['sell_value']}")
    print(f"\n--- Charges Breakdown ---")
    print(f"Brokerage: ₹{result['brokerage']}")
    print(f"STT      : ₹{result['stt']}")
    print(f"Exchange : ₹{result['exchange']}")
    print(f"SEBI     : ₹{result['sebi']}")
    print(f"GST      : ₹{result['gst']}")
    print(f"Stamp    : ₹{result['stamp']}")
    print(f"DP       : ₹{result['dp']}")
    print(f"\nTotal    : ₹{result['total_charges']}")
    print(f"Gross PnL: ₹{result['gross_pnl']}")
    print(f"Net PnL  : ₹{result['net_pnl']}")
    print(f"Breakeven: {result['breakeven_pct']}%")

    status = "✅ PROFIT" if result['is_profitable'] else "❌ LOSS"
    print(f"Status   : {status}")

    # Min target
    target, t_result = min_target_price(buy, qty, "EQ")
    print(f"\nMin Target for ₹1 profit: ₹{target}")
    print(f"Net PnL at target       : ₹{t_result['net_pnl']}")
