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
        self.wfile.write(b"OK")

def run_server():
    httpd = HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 8080))), HealthCheckHandler)
    httpd.serve_forever()

# --- 2. Настройка ИИ ---
# ВАЖНО: используем прямую настройку через переменную окружения
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Пробуем универсальное имя модели, которое работает везде
model = genai.GenerativeModel('gemini-1.5-flash')

bot = Bot(token=os.getenv("TG_TOKEN"))
dp = Dispatcher()

# --- 3. Логика ответов ---
@dp.message()
async def talk_to_ai(message: types.Message):
    # Отвечаем, если это личка или если бота упомянули
    bot_info = await bot.get_me()
    if message.chat.type == 'private' or (message.text and f"@{bot_info.username}" in message.text):
        try:
            # Чистим текст
            user_text = message.text.replace(f"@{bot_info.username}", "").strip()
            if not user_text: user_text = "Привет"
            
            print(f"Запрос к ИИ: {user_text}")
            
            # Генерация контента
            response = model.generate_content(user_text)
            
            if response and response.text:
                await message.reply(response.text)
            else:
                await message.reply("ИИ вернул пустой ответ. Попробуйте другой вопрос.")
                
        except Exception as e:
            error_msg = str(e)
            print(f"Ошибка ИИ: {error_msg}")
            
            # Если опять 404, пробуем альтернативное имя модели прямо в ответе для теста
            if "404" in error_msg:
                await message.reply("Google все еще не видит модель. Проверьте, что в Google Cloud включен именно 'Generative Language API'.")
            else:
                await message.reply(f"Произошла ошибка: {error_msg}")

# --- 4. Запуск ---
async def main():
    threading.Thread(target=run_server, daemon=True).start()
    print("Бот запущен и готов отвечать!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
