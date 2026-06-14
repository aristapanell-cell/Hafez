# main.py
import asyncio
import aiohttp

from config import *
from cache import load_cache, check_and_update_cache
from github_api import fetch_release
from telegram_api import send_file, send_link
from utils import (
    get_repo_key,
    get_repo_name,
    detect_arch,
    is_valid_asset,
    format_size,
    build_caption,
    detect_system
)
from logger import log_info, log_error, log_success

semaphore = asyncio.Semaphore(MAX_CONCURRENT)

async def download(session, url, retries=3):
    for attempt in range(retries):
        try:
            timeout = aiohttp.ClientTimeout(total=120, connect=30)
            async with session.get(url, timeout=timeout) as r:
                if r.status == 200:
                    data = await r.read()
                    log_info(f"Downloaded {len(data)} bytes from {url.split('/')[-1]}")
                    return data
                else:
                    log_error(f"Download failed: HTTP {r.status} (attempt {attempt+1}/{retries})")
                    if attempt < retries - 1:
                        await asyncio.sleep(3)
                        continue
                    return None
        except asyncio.TimeoutError:
            log_error(f"Timeout downloading (attempt {attempt+1}/{retries})")
            if attempt < retries - 1:
                await asyncio.sleep(3)
        except Exception as e:
            log_error(f"Download error: {e} (attempt {attempt+1}/{retries})")
            if attempt < retries - 1:
                await asyncio.sleep(3)
    return None

async def process(session, session_tg, url, cache):
    async with semaphore:
        try:
            release = await fetch_release(session, url)
            if not release:
                return

            repo_key = get_repo_key(url)
            repo_name = get_repo_name(url)

            release_id = release["id"]
            tag = release["tag_name"]

            if release.get("prerelease", False):
                log_info(f"skip prerelease {repo_name} - {tag}")
                return

            if not await check_and_update_cache(repo_key, release_id, tag):
                log_info(f"skip {repo_name}")
                return

            assets = release.get("assets", [])
            if not assets:
                return

            sent = False
            sent_combinations = set()

            for idx, a in enumerate(assets):
                filename = a["name"]

                if not is_valid_asset(filename):
                    continue

                arch = detect_arch(filename, url, tag, repo_name)
                system = detect_system(filename, url, repo_name)

                combo = f"{system}_{arch}"
                if combo in sent_combinations:
                    log_info(f"skip duplicate {combo} for {filename}")
                    continue
                sent_combinations.add(combo)

                size = format_size(a["size"])
                url_dl = a["browser_download_url"]
                is_large = a["size"] > SIZE_LIMIT

                caption = build_caption(repo_name, tag, system, arch, size, is_large=is_large)

                log_info(f"FILE {idx+1}: {filename} | arch={arch} | system={system} | size={a['size']} | large={is_large}")

                data = await download(session, url_dl)

                if data and len(data) < SIZE_LIMIT:
                    ok = await send_file(session_tg, BOT_TOKEN, CHAT_ID, data, filename, caption, url_dl)
                    if not ok:
                        log_info(f"File send failed, sending as link")
                        await send_link(session_tg, BOT_TOKEN, CHAT_ID, caption, url_dl)
                else:
                    if data:
                        log_info(f"File too large ({len(data)} bytes), sending as link")
                    else:
                        log_info(f"Download failed, sending as link")
                    await send_link(session_tg, BOT_TOKEN, CHAT_ID, caption, url_dl)

                sent = True
                await asyncio.sleep(2)

            if sent:
                log_success(repo_name, tag)
                await asyncio.sleep(3)

        except Exception as e:
            log_error(str(e), exc=True)

async def main():
    log_info("bot started")

    cache = load_cache()

    connector = aiohttp.TCPConnector(limit=10, ttl_dns_cache=300)
    async with aiohttp.ClientSession(connector=connector) as session, aiohttp.ClientSession(connector=connector) as session_tg:
        await asyncio.gather(*[
            process(session, session_tg, url, cache)
            for url in REPOS
        ])

    log_info("done")

if __name__ == "__main__":
    asyncio.run(main())
