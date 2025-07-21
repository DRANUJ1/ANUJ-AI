from pyrogram.types import Message
import utils

async def handle_quiz_command(client, message: Message):
    text = "Here's your quiz:\n\n"
    questions = [
        {"q": "What is 2 + 2?", "a": "4"},
        {"q": "What is the capital of France?", "a": "Paris"}
    ]
    for q in questions:
        text += f"Q: {q['q']}\nA: ||{q['a']}||\n\n"
    await message.reply_text(text, quote=True, parse_mode="MarkdownV2")
