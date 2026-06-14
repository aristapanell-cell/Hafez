import aiohttp
import json
import asyncio
from typing import Optional
from logger import log_error, log_info
from config import REQUEST_TIMEOUT

async def send_file(session: aiohttp.ClientSession, token: str, chat_id: str, file_bytes: bytes, filename: str, caption: str, url: str, retries: int = 3) -> bool:
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

    for attempt in range(retries):
        try:
            async with session.post(api, data=data, timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)) as resp:
                if resp.status == 429:
                    retry_after = int((await resp.json()).get("parameters", {}).get("retry_after", 5))
                    log_info(f"Rate limited, waiting {retry_after}s (attempt {attempt+1}/{retries})")
                    await asyncio.sleep(retry_after)
                    continue
                if resp.status != 200:
                    error_text = await resp.text()
                    log_error(f"Telegram API error {resp.status}: {error_text}")
                    if attempt < retries - 1:
                        await asyncio.sleep(2)
                        continue
                    return False
                log_info(f"File sent successfully: {filename}")
                return True
        except asyncio.TimeoutError:
            log_error(f"Timeout sending file (attempt {attempt+1}/{retries})")
            if attempt < retries - 1:
                await asyncio.sleep(2)
        except Exception as e:
            log_error(f"Send error: {e} (attempt {attempt+1}/{retries})")
            if attempt < retries - 1:
                await asyncio.sleep(2)
    
    return False

async def send_link(session: aiohttp.ClientSession, token: str, chat_id: str, text: str, url: str, retries: int = 3) -> bool:
    api = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [[{"text": "📥 دانلود", "url": url}]]
        }
    }

    for attempt in range(retries):
        try:
            async with session.post(api, json=payload, timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)) as resp:
                if resp.status == 429:
                    retry_after = int((await resp.json()).get("parameters", {}).get("retry_after", 5))
                    log_info(f"Rate limited on link, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    continue
                if resp.status != 200:
                    error_text = await resp.text()
                    log_error(f"Telegram API error {resp.status}: {error_text}")
                    if attempt < retries - 1:
                        await asyncio.sleep(2)
                        continue
                log_info(f"Link sent successfully: {url}")
                return True
        except asyncio.TimeoutError:
            log_error(f"Timeout sending link (attempt {attempt+1}/{retries})")
            if attempt < retries - 1:
                await asyncio.sleep(2)
        except Exception as e:
            log_error(f"Send link error: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(2)
    
    return False

async def check_telegram_bot(session: aiohttp.ClientSession, token: str, chat_id: str) -> bool:
    try:
        api = f"https://api.telegram.org/bot{token}/getMe"
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        async with session.get(api, timeout=timeout) as resp:
            if resp.status == 200:
                log_info("Telegram bot health check passed")
                return True
            log_error(f"Telegram bot health check failed: {resp.status}")
            return False
    except Exception as e:
        log_error(f"Telegram bot health check error: {e}")
        return False
