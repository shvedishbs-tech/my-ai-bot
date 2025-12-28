import asyncio
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from aiogram import Bot, Dispatcher, types
import google.generativeai as genai

# Заглушка для Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_server():
    server = HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 8080))), HealthCheckHandler)
    server.serve_forever()

# Настройка с явным указанием версии
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Пробуем более стабильное имя модели
model = genai.GenerativeModel(model_name='models/gemini-1.5-flash')
bot = Bot(token=os.getenv("TG_TOKEN"))
dp = Dispatcher()

@dp.message()
async def handle_msg(message: types.Message):
    if message.chat.type == 'private' or f"@{ (await bot.get_me()).username }" in (message.text or ""):
        try:
            # Очистка текста от тега бота
            text = message.text.replace(f"@{ (await bot.get_me()).username }", "").strip()
            res = model.generate_content(text or "Привет")
            await message.reply(res.text)
        except Exception as e:
            await message.reply(f"Ошибка: {e}")

async def main():
    threading.Thread(target=run_server, daemon=True).start()
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
