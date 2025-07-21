from pyrogram.types import Message

# This function handles normal text messages as doubts
async def solve_doubt(client, message: Message):
    doubt = message.text
    response = f"🤖 You asked: '{doubt}'\nHere's an answer: [This is an AI-generated answer placeholder.]"
    await message.reply_text(response)

# This function handles /ask command
async def handle_doubt_command(client, message: Message):
    doubt = message.text.replace("/ask", "").strip()
    if not doubt:
        await message.reply_text("Please enter a doubt after the /ask command.")
        return
    response = f"🧠 Answer for: '{doubt}'\n[This is an AI-generated answer placeholder.]"
    await message.reply_text(response)

