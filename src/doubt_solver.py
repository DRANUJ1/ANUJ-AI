from pyrogram.types import Message

async def solve_doubt(client, message: Message):
    doubt = message.text
    response = f"🤖 You asked: '{doubt}'\nHere's an answer: [This is an AI-generated answer placeholder.]"
    await message.reply_text(response)
