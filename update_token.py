from trading_system.core.token_manager import save_token, test_token

print("=" * 40)
print("   DHAN TOKEN UPDATE SYSTEM")
print("=" * 40)

client_id = input("Client ID daalo: ").strip()
access_token = input("Access Token daalo: ").strip()

save_token(access_token, client_id)

print("Token test ho raha hai...")
if test_token():
    print("System ready!")
else:
    print("Token check karo.")
