# main.py

import asyncio
import aiohttp

from config import *
from cache import load_cache, update_cache
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

async def download(session, url):
    try:
        async with session.get(url) as r:
            if r.status == 200:
                return await r.read()
    except:
        return None

async def process(session, url, cache, tg):
    async with semaphore:
        try:
            release = await fetch_release(session, url)
            if not release:
                return

            repo_key = get_repo_key(url)
            repo_name = get_repo_name(url)

            release_id = release["id"]
            tag = release["tag_name"]

            if repo_key in cache and cache[repo_key]["release_id"] == release_id:
                log_info(f"skip {repo_name}")
                return

            assets = release.get("assets", [])
            if not assets:
                return

            sent = False

            for a in assets:
                filename = a["name"]

                if not is_valid_asset(filename):
                    continue

                arch = detect_arch(filename, url, tag)
                system = detect_system(filename, url, repo_name)

                size = format_size(a["size"])
                url_dl = a["browser_download_url"]
                is_large = a["size"] > SIZE_LIMIT

                caption = build_caption(repo_name, tag, system, arch, size, is_large=is_large)

                log_info(f"FILE: {filename} | arch={arch} | system={system} | size={a['size']}")

                data = await download(session, url_dl)

                if data and len(data) < SIZE_LIMIT:
                    ok = await send_file(tg, BOT_TOKEN, CHAT_ID, data, filename, caption, url_dl)
                    if not ok:
                        await send_link(tg, BOT_TOKEN, CHAT_ID, caption, url_dl)
                else:
                    await send_link(tg, BOT_TOKEN, CHAT_ID, caption, url_dl)

                sent = True
                await asyncio.sleep(1)

            if sent:
                await update_cache(repo_key, release_id, tag)
                log_success(repo_name, tag)

        except Exception as e:
            log_error(str(e), exc=True)

async def main():
    log_info("bot started")

    cache = load_cache()

    async with aiohttp.ClientSession() as session, aiohttp.ClientSession() as tg:
        await asyncio.gather(*[
            process(session, url, cache, tg)
            for url in REPOS
        ])

    log_info("done")

if __name__ == "__main__":
    asyncio.run(main())
