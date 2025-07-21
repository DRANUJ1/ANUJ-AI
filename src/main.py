from handlers import setup_handlers
from pyrogram import Client
import config

app = Client("personal_bot", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=config.BOT_TOKEN)

setup_handlers(app)

if __name__ == "__main__":
    print("Bot is running...")
    app.run()
