from pyrogram import Client, filters
from pyrogram.types import Message
from quiz_handler import handle_quiz_command
from doubt_solver import handle_doubt_command

def register_handlers(app: Client):

    @app.on_message(filters.command("start"))
    async def start_handler(client, message: Message):
        await message.reply_text(f"Hi {message.from_user.first_name}, I'm your Personal AI Assistant!")

    @app.on_message(filters.command("quiz"))
    async def quiz_handler(client, message: Message):
        await handle_quiz_command(client, message)

    @app.on_message(filters.command("ask"))
    async def doubt_handler(client, message: Message):
        await handle_doubt_command(client, message)
