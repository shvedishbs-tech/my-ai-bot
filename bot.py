import asyncio
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from aiogram import Bot, Dispatcher, types
import google.generativeai as genai

# --- СЕКЦИЯ ДЛЯ RENDER (ЧТОБЫ НЕ ВЫКЛЮЧАЛСЯ) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_health_check():
    # Render передает порт в переменную окружения PORT
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# Запуск мини-сервера в фоновом потоке
threading.Thread(target=run_health_check, daemon=True).start()

# --- НАСТРОЙКИ ИИ И ТЕЛЕГРАМ ---
TG_TOKEN = os.getenv("TG_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Настраиваем Google Gemini
genai.configure(api_key=GOOGLE_API_KEY)
# Используем самую стабильную версию модели
model = genai.GenerativeModel('gemini-1.5-flash-latest')

bot = Bot(token=TG_TOKEN)
dp = Dispatcher()

@dp.message()
async def handle_messages(message: types.Message):
    # Проверяем: личка или упоминание в группе
    is_private = message.chat.type == 'private'
    
    bot_info = await bot.get_me()
    is_mention = message.text and f"@{bot_info.username}" in message.text

    if is_private or is_mention:
        try:
            # Очищаем текст от упоминания бота
            clean_text = message.text.replace(f"@{bot_info.username}", "").strip()
            if not clean_text:
                clean_text = "Привет!"

            # Запрос к нейросети
            response = model.generate_content(clean_text)
            
            # Ответ пользователю
            if response.text:
                await message.reply(response.text)
            else:
                await message.reply("ИИ прислал пустой ответ, попробуйте еще раз.")
                
        except Exception as e:
            # Если ошибка — бот напишет её в чат (удобно для отладки)
            error_message = str(e)
            if "location is not supported" in error_message.lower():
                await message.reply("Ошибка: Google блокирует запросы из этого региона. Измените регион в Render на USA.")
            else:
                await message.reply(f"Произошла ошибка: {error_message}")

async def main():
    print("Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
