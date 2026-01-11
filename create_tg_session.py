from telethon.sync import TelegramClient

API_ID = int(input("Enter API_ID: ").strip())
API_HASH = input("Enter API_HASH: ").strip()
PHONE = input("Enter phone number (+91...): ").strip()

client = TelegramClient("trendscope_session", API_ID, API_HASH)

client.start(phone=PHONE)

print("✅ Session Created Successfully!")
print("📌 File created: trendscope_session.session")
