import asyncio
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from aiogram import Bot, Dispatcher, types
import google.generativeai as genai

# --- 1. Мини-сервер для Render ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive")

def run_health_check():
    port = int(os.environ.get("PORT", 8080))
    httpd = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    httpd.serve_forever()

# --- 2. Настройки ---
TG_TOKEN = os.getenv("TG_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

bot = Bot(token=TG_TOKEN)
dp = Dispatcher()

# --- 3. Логика ответов ---
@dp.message()
async def talk_to_ai(message: types.Message):
    # Если личка или упоминание
    bot_info = await bot.get_me()
    if message.chat.type == 'private' or (message.text and f"@{bot_info.username}" in message.text):
        try:
            print(f"Запрос от {message.from_user.first_name}: {message.text}")
            user_text = message.text.replace(f"@{bot_info.username}", "").strip()
            response = model.generate_content(user_text if user_text else "Привет")
            await message.reply(response.text)
        except Exception as e:
            print(f"Ошибка ИИ: {e}")
            await message.reply(f"Произошла ошибка: {e}")

# --- 4. Главная функция запуска ---
async def main():
    # Сначала запускаем веб-сервер в отдельном потоке
    server_thread = threading.Thread(target=run_health_check, daemon=True)
    server_thread.start()
    
    print("Бот запускается и начинает слушать Telegram...")
    # Затем запускаем опрос Телеграма
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
