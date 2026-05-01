import os
import requests
from pathlib import Path
from dotenv import load_dotenv
import asyncio
from fastapi import FastAPI, Request, BackgroundTasks

from utils.telegram import send_message, get_file_url, handle_message

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

#sessions: dict = {}

# ─────────────────────────────────────────────
# 📁 Make sure /data folder exists
# ─────────────────────────────────────────────
Path("data").mkdir(exist_ok=True)


# ─────────────────────────────────────────────
# 🚀 FastAPI app — direct webhook, no Claude
# ─────────────────────────────────────────────
app = FastAPI()

@app.post("/webhook")

async def webhook(request: Request):
    data = await request.json()
    message = data.get("message", {})
    chat_id = str(message.get("chat", {}).get("id"))

    if "photo" in message:
        file_id = message["photo"][-1]["file_id"]
        image_url = get_file_url(file_id)
        reply = handle_message(user_id=chat_id, image_url=image_url)

    #send_message(chat_id, "⏳ Processing your query, please wait...")
    elif "text" in message:
        text = message["text"]
        # Run heavy task in thread so FastAPI doesn't block
        loop = asyncio.get_event_loop()
        #reply = await loop.run_in_executor(None, handle_message, chat_id, text, None)
        #send_message(chat_id, reply)
        reply = handle_message(user_id=chat_id, text=text)

    else:
        reply = "⚠️ Please send text or images only."

    send_message(chat_id, reply)
    return {"ok": True}

# ─────────────────────────────────────────────
# Register webhook with Telegram on startup
# ─────────────────────────────────────────────
@app.on_event("startup")
async def set_webhook():
    webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL")
    requests.post(f"{TELEGRAM_API}/setWebhook", json={"url": f"{webhook_url}/webhook"})
    print(f"✅ Webhook set to {webhook_url}/webhook")

# Run with: uvicorn app:app --host 0.0.0.0 --port 8000