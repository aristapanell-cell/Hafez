import asyncio
import aiohttp
from config import *
from cache import load_cache, update_cache
from github_api import fetch_release
from telegram_api import send_file, send_link
from utils import get_repo_name, detect_arch, is_valid_asset, build_caption, format_size
from logger import log_info, log_error, log_success

semaphore = asyncio.Semaphore(MAX_CONCURRENT)

async def download_file(session, url):
    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                return await resp.read()
            log_error(f"Download HTTP {resp.status}: {url}")
            return None
    except Exception as e:
        log_error(f"Download failed: {url} -> {e}")
        return None

async def process_repo(session, repo_url, cache, tg_session):
    async with semaphore:
        try:
            release = await fetch_release(session, repo_url)
            if not release:
                log_error(f"No release: {repo_url}")
                return

            repo_name = get_repo_name(repo_url)
            release_id = release["id"]
            tag = release["tag_name"]

            if repo_name in cache and cache[repo_name]["release_id"] == release_id:
                log_info(f"⏩ {repo_name} | already sent ({tag})")
                return

            log_info(f"🔄 {repo_name} | new release: {tag}")

            assets = release.get("assets", [])
            if not assets:
                log_info(f"⚠️ {repo_name} | no assets")
                return

            sent_any = False

            for asset in assets:
                filename = asset["name"]
                if not is_valid_asset(filename):
                    continue

                arch = detect_arch(filename)
                if not arch:
                    continue

                system = "Android" if ".apk" in filename.lower() else "Windows"
                file_size = asset["size"]
                download_url = asset["browser_download_url"]
                size_mb = format_size(file_size)
                is_large = file_size > SIZE_LIMIT
                
                caption = build_caption(repo_name, tag, system, arch, size_mb, is_large)

                log_info(f"📥 {repo_name} | {arch} | size: {file_size//1024}KB")

                if file_size > SIZE_LIMIT:
                    await send_link(tg_session, BOT_TOKEN, CHAT_ID, caption, download_url)
                    log_info(f"📎 {repo_name} | {arch} (link only)")
                    sent_any = True
                else:
                    file_bytes = await download_file(session, download_url)
                    if file_bytes:
                        log_info(f"⬆️ Uploading {filename} to Telegram...")
                        success = await send_file(tg_session, BOT_TOKEN, CHAT_ID, file_bytes, filename, caption, download_url)
                        if success:
                            log_info(f"📦 {repo_name} | {arch} (uploaded)")
                            sent_any = True
                        else:
                            await send_link(tg_session, BOT_TOKEN, CHAT_ID, caption, download_url)
                            log_info(f"📎 {repo_name} | {arch} (upload failed, link only)")
                            sent_any = True
                    else:
                        await send_link(tg_session, BOT_TOKEN, CHAT_ID, caption, download_url)
                        log_info(f"📎 {repo_name} | {arch} (download failed, link only)")
                        sent_any = True

                await asyncio.sleep(1)

            if sent_any:
                await update_cache(repo_name, release_id, tag)
                log_success(repo_name, tag)

        except Exception as e:
            log_error(f"{repo_url} | {e}", exc=True)

async def main():
    log_info("🚀 Bot started")
    cache = load_cache()
    log_info(f"📦 Loaded cache: {len(cache)} repos")

    async with aiohttp.ClientSession() as session, aiohttp.ClientSession() as tg_session:
        tasks = [process_repo(session, url, cache, tg_session) for url in REPOS]
        await asyncio.gather(*tasks)

    log_info("✅ Bot finished")

if __name__ == "__main__":
    asyncio.run(main())
