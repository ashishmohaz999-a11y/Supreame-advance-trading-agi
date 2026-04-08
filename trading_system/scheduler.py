import time
import logging
import os
from datetime import datetime
from trading_system.dhan_live import run_live_cycle
from trading_system.paper_trader import (
    load_paper_account, show_summary
)

# Logs setup
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/trading_log.txt",
    level=logging.INFO,
    format="%(asctime)s | %(message)s"
)

def log(msg):
    print(msg)
    logging.info(msg)

def is_market_open():
    """NSE market hours check"""
    now = datetime.now()
    
    # Weekend check
    if now.weekday() >= 5:
        return False
    
    # 9:15 AM to 3:30 PM
    open_time  = now.replace(hour=9,  minute=15, second=0)
    close_time = now.replace(hour=15, minute=30, second=0)
    
    return open_time <= now <= close_time

def run_scheduler():
    log("🚀 AUTO SCHEDULER STARTED!")
    log(f"   Market Hours: 9:15 AM - 3:30 PM (Mon-Fri)")
    log(f"   Cycle every : 30 minutes")
    
    account = load_paper_account()
    cycle = 0
    
    while True:
        now = datetime.now()
        
        if is_market_open():
            cycle += 1
            log(f"\n🔄 Cycle #{cycle} | {now.strftime('%H:%M:%S')}")
            
            try:
                account = run_live_cycle(account)
                log(f"💰 Capital: ₹{round(account['capital'],2)}")
            except Exception as e:
                log(f"❌ Error: {e}")
            
            # Har 30 min mein
            log(f"⏳ Next cycle in 30 min...")
            time.sleep(1800)
        
        else:
            # Market band hai
            if now.weekday() >= 5:
                log(f"📅 Weekend - Market Closed")
            elif now.hour < 9:
                log(f"🌅 Market opens at 9:15 AM")
            else:
                log(f"🌙 Market Closed for today")
                log("📈 Final Summary:")
                show_summary(account)
            
            # 15 min baad check karo
            time.sleep(900)

if __name__ == "__main__":
    run_scheduler()
