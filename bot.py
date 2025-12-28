import asyncio
import os
from aiogram import Bot, Dispatcher, types
import google.generativeai as genai
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# Заглушка для Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive")

def run_health_check():
    server = HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 8080))), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=run_health_check, daemon=True).start()

# Настройки
TG_TOKEN = os.getenv("TG_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

bot = Bot(token=TG_TOKEN)
dp = Dispatcher()

@dp.message()
async def talk_to_ai(message: types.Message):
    # Бот отправит это сообщение ПЕРЕД тем, как идти к нейросети
    print(f"Получено сообщение: {message.text}")
    
    try:
        response = model.generate_content(message.text)
        await message.reply(response.text)
    except Exception as e:
        # Если нейросеть выдает ошибку, бот напишет, какую именно
        error_text = f"Ошибка нейросети: {str(e)}"
        print(error_text)
        await message.reply(error_text)

async def main():
    print("Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
