import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

def send_message(text):
    if not BOT_TOKEN or not CHAT_ID:
        print(f"📢 Alert: {text[:50]}")
        return False
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }, timeout=5)
        return True
    except:
        return False

def alert_buy(symbol, price, qty, sl, target, capital):
    send_message(f"🟢 <b>BUY {symbol}</b>\n💰 ₹{price} x {qty}\n🛑 SL: ₹{sl}\n🎯 Target: ₹{target}\n💼 Capital: ₹{capital}")

def alert_sell(symbol, entry, exit_price, qty, pnl, capital):
    e = "🟢" if pnl > 0 else "🔴"
    send_message(f"{e} <b>SELL {symbol}</b>\n📥 ₹{entry} → ₹{exit_price}\n💵 PnL: ₹{pnl}\n💼 Capital: ₹{capital}")

def alert_sl_hit(symbol, price, loss):
    send_message(f"🛑 <b>SL HIT: {symbol}</b>\n📉 ₹{price}\n💸 Loss: ₹{loss}")

def alert_target_hit(symbol, price, profit):
    send_message(f"🎯 <b>TARGET HIT: {symbol}</b>\n📈 ₹{price}\n💰 Profit: ₹{profit}")

def alert_market_open():
    send_message("🔔 <b>Market Open!</b> 9:15 AM - Trading Started")

def alert_market_close(capital, pnl):
    e = "📈" if pnl > 0 else "📉"
    send_message(f"{e} <b>Market Closed</b>\n💼 Capital: ₹{capital}\n💵 Day PnL: ₹{pnl}")

def alert_token_expiry(hours_left):
    send_message(f"⚠️ <b>Token Expiry!</b>\n⏰ {hours_left:.0f} hours baki\nRun: python update_token.py")
