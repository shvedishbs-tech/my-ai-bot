import asyncio
import os
from aiogram import Bot, Dispatcher, types
import google.generativeai as genai
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# --- Обманка для Render (Web Service) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive")

def run_health_check():
    server = HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 8080))), HealthCheckHandler)
    server.serve_forever()

# Запускаем "сайт-заглушку" в отдельном потоке
threading.Thread(target=run_health_check, daemon=True).start()
# ---------------------------------------

TG_TOKEN = os.getenv("TG_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

bot = Bot(token=TG_TOKEN)
dp = Dispatcher()

@dp.message()
async def talk_to_ai(message: types.Message):
    is_private = message.chat.type == 'private'
    is_mention = message.text and f"@{ (await bot.get_me()).username }" in message.text
    
    if is_private or is_mention:
        try:
            user_text = message.text.replace(f"@{ (await bot.get_me()).username }", "").strip()
            response = model.generate_content(user_text)
            await message.reply(response.text)
        except Exception as e:
            print(f"Error: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
