# main.py
import asyncio
import aiohttp

from config import *
from cache import load_cache, check_and_update_cache, clear_old_cache
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

async def process(session, session_tg, url):
    async with semaphore:
        release = None
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

                file_size = a["size"]
                arch = detect_arch(filename, url, tag, repo_name)
                system = detect_system(filename, url, repo_name)
                size_str = format_size(file_size)
                url_dl = a["browser_download_url"]

                if file_size > SIZE_LIMIT:
                    log_info(f"SKIP DOWNLOAD: {filename} | size={file_size} bytes exceeds {SIZE_LIMIT} bytes, sending as link only")
                    caption = build_caption(repo_name, tag, system, arch, size_str, is_large=True)
                    await send_link(session_tg, BOT_TOKEN, CHAT_ID, caption, url_dl)
                    sent = True
                    continue

                combo = f"{system}_{arch}"
                if combo in sent_combinations:
                    log_info(f"skip duplicate {combo} for {filename}")
                    continue
                sent_combinations.add(combo)

                caption = build_caption(repo_name, tag, system, arch, size_str, is_large=False)

                log_info(f"FILE {idx+1}: {filename} | arch={arch} | system={system} | size={file_size}")

                data = None
                download_success = False
                for retry in range(2):
                    try:
                        timeout = aiohttp.ClientTimeout(total=120, connect=30)
                        async with session.get(url_dl, timeout=timeout) as r:
                            if r.status == 200:
                                data = await r.read()
                                if len(data) <= SIZE_LIMIT:
                                    download_success = True
                                    log_info(f"Downloaded {len(data)} bytes from {filename}")
                                    break
                                else:
                                    log_info(f"Downloaded file too large: {len(data)} bytes")
                                    download_success = False
                                    break
                            else:
                                log_error(f"Download failed: HTTP {r.status} for {filename}")
                    except asyncio.TimeoutError:
                        log_error(f"Timeout downloading {filename} (retry {retry+1}/2)")
                    except Exception as e:
                        log_error(f"Download error for {filename}: {e} (retry {retry+1}/2)")
                    
                    if retry < 1:
                        await asyncio.sleep(3)

                if download_success and data and len(data) <= SIZE_LIMIT:
                    ok = await send_file(session_tg, BOT_TOKEN, CHAT_ID, data, filename, caption, url_dl)
                    if not ok:
                        log_info(f"File send failed, sending as link")
                        await send_link(session_tg, BOT_TOKEN, CHAT_ID, caption, url_dl)
                else:
                    if data and len(data) > SIZE_LIMIT:
                        log_info(f"File too large after download ({len(data)} bytes), sending as link")
                    else:
                        log_info(f"Download failed, sending as link")
                    await send_link(session_tg, BOT_TOKEN, CHAT_ID, caption, url_dl)

                sent = True
                await asyncio.sleep(2)

            if sent:
                log_success(repo_name, tag)

        except Exception as e:
            log_error(f"Error processing {url}: {str(e)}", exc=True)
        finally:
            await asyncio.sleep(1)

async def main():
    log_info("bot started")

    current_repos = {}
    for url in REPOS:
        repo_key = get_repo_key(url)
        current_repos[repo_key] = True
    
    await clear_old_cache(current_repos)

    connector = aiohttp.TCPConnector(limit=20, ttl_dns_cache=300)
    async with aiohttp.ClientSession(connector=connector) as session, aiohttp.ClientSession(connector=connector) as session_tg:
        tasks = [process(session, session_tg, url) for url in REPOS]
        await asyncio.gather(*tasks)

    log_info("done")

if __name__ == "__main__":
    asyncio.run(main())
