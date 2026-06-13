import aiohttp
import json
from logger import log_error, log_info

async def send_file(session, token, chat_id, file_bytes, filename, caption, url):
    api = f"https://api.telegram.org/bot{token}/sendDocument"

    markup = json.dumps({
        "inline_keyboard": [[{"text": "📥 دانلود", "url": url}]]
    })

    data = aiohttp.FormData()
    data.add_field("chat_id", str(chat_id))
    data.add_field("caption", caption)
    data.add_field("parse_mode", "HTML")
    data.add_field("reply_markup", markup)
    data.add_field("document", file_bytes, filename=filename)

    try:
        async with session.post(api, data=data) as resp:
            if resp.status != 200:
                log_error(await resp.text())
                return False
            log_info("sent file")
            return True
    except Exception as e:
        log_error(str(e))
        return False


async def send_link(session, token, chat_id, text, url):
    api = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [[{"text": "📥 دانلود", "url": url}]]
        }
    }

    try:
        await session.post(api, json=payload)
    except Exception as e:
        log_error(str(e))
