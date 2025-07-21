from fastapi import FastAPI
import uvicorn
import asyncio
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN
from handlers import register_handlers

# Telegram Bot
app_bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# FastAPI app (for Render)
app = FastAPI()

@app.get("/")
def home():
    return {"message": "Bot is running!"}

async def run_bot():
    await app_bot.start()
    print("Bot started.")
    await idle()  # optional: from pyrogram import idle

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(run_bot())

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000)
