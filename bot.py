import asyncio
import os
from aiogram import Bot, Dispatcher, types
import google.generativeai as genai

# Эти данные мы подставим позже в настройках хостинга
TG_TOKEN = os.getenv("TG_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

bot = Bot(token=TG_TOKEN)
dp = Dispatcher()

@dp.message()
async def talk_to_ai(message: types.Message):
    # Бот ответит, если написать ему в личку или упомянуть в группе через @имя_бота
    is_private = message.chat.type == 'private'
    is_mention = message.text and f"@{ (await bot.get_me()).username }" in message.text

    if is_private or is_mention:
        try:
            # Убираем упоминание бота из текста, чтобы ИИ не путался
            user_text = message.text.replace(f"@{ (await bot.get_me()).username }", "").strip()
            response = model.generate_content(user_text)
            await message.reply(response.text)
        except Exception as e:
            print(f"Ошибка: {e}")
            await message.reply("Я призадумался. Попробуй еще раз чуть позже.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
