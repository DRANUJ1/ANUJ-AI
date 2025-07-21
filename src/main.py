from fastapi import FastAPI
import uvicorn
import asyncio
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN
from handlers import register_handlers

# Pyrogram client
app_bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
register_handlers(app_bot)  # ✅ Register handlers

# FastAPI app
app = FastAPI()

@app.get("/")
def home():
    return {"message": "Bot is running!"}

@app.on_event("startup")
async def startup_event():
    await app_bot.start()
    print("✅ Bot started.")

@app.on_event("shutdown")
async def shutdown_event():
    await app_bot.stop()
    print("⛔ Bot stopped.")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000)
