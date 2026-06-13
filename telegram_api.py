import aiohttp
import json
from logger import log_error, log_info

async def send_file(session, bot_token, chat_id, file_bytes, filename, caption, button_url):
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    
    reply_markup = json.dumps({
        "inline_keyboard": [[{"text": "📥 دانلود مستقیم", "url": button_url}]]
    })
    
    data = aiohttp.FormData()
    data.add_field("chat_id", str(chat_id))
    data.add_field("caption", caption)
    data.add_field("parse_mode", "HTML")
    data.add_field("reply_markup", reply_markup)
    data.add_field("document", file_bytes, filename=filename)
    
    try:
        async with session.post(url, data=data) as resp:
            if resp.status != 200:
                text = await resp.text()
                log_error(f"Telegram send_file failed: {resp.status} - {text[:200]}")
                return False
            else:
                log_info("File uploaded successfully")
                return True
    except Exception as e:
        log_error(f"Telegram send_file failed: {e}")
        return False

async def send_link(session, bot_token, chat_id, text, button_url):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [[{"text": "📥 دانلود مستقیم", "url": button_url}]]
        }
    }
    try:
        await session.post(url, json=payload)
    except Exception as e:
        log_error(f"Telegram send_link failed: {e}")
