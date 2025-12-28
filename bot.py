import asyncio
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from aiogram import Bot, Dispatcher, types
import google.generativeai as genai

# --- 1. Мини-сервер для работы на Render ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive and kicking")

def run_health_check():
    port = int(os.environ.get("PORT", 8080))
    httpd = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    httpd.serve_forever()

# --- 2. Настройки ключей ---
TG_TOKEN = os.getenv("TG_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Настройка Google AI
genai.configure(api_key=GOOGLE_API_KEY)

# Мы используем прямой вызов модели без лишних префиксов
# Это решает проблему 404 в v1beta
model = genai.GenerativeModel('gemini-1.5-flash')

bot = Bot(token=TG_TOKEN)
dp = Dispatcher()

# --- 3. Обработка сообщений ---
@dp.message()
async def talk_to_ai(message: types.Message):
    # Бот отвечает в личке ИЛИ если его тегнули в группе
    bot_info = await bot.get_me()
    is_private = message.chat.type == 'private'
    is_mention = message.text and f"@{bot_info.username}" in message.text

    if is_private or is_mention:
        try:
            # Убираем имя бота из текста для ИИ
            clean_text = message.text.replace(f"@{bot_info.username}", "").strip()
            if not clean_text:
                clean_text = "Привет!"

            # Логируем в консоль Render для проверки
            print(f"Запрос от {message.from_user.first_name}: {clean_text}")

            # Генерация ответа
            response = model.generate_content(clean_text)
            
            if response and response.text:
                await message.reply(response.text)
            else:
                await message.reply("ИИ не смог сформировать текст, попробуйте другой вопрос.")

        except Exception as e:
            error_str = str(e)
            print(f"Ошибка: {error_str}")
            
            # Понятные подсказки для пользователя
            if "404" in error_str:
                await message.reply("Ошибка 404: Модель не найдена. Пожалуйста, убедитесь, что API включен в Google Cloud.")
            elif "location" in error_str.lower():
                await message.reply("Ошибка региона: Измените регион в настройках Render на Oregon (USA).")
            else:
                await message.reply(f"Произошла ошибка: {error_str}")

# --- 4. Запуск ---
async def main():
    # Запускаем "заглушку" для Render в отдельном потоке
    threading.Thread(target=run_health_check, daemon=True).start()
    
    print("Бот успешно запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен")
