import asyncio
import aiohttp
from typing import Set, Dict, Optional

from config import *
from cache import load_cache, check_and_update_cache, clear_old_cache, clear_all_cache
from github_api import fetch_release, check_github_api
from telegram_api import send_file, send_link, check_telegram_bot
from utils import (
    get_repo_key,
    get_repo_name,
    detect_arch,
    is_valid_asset,
    format_size,
    build_caption,
    detect_system
)
from logger import log_info, log_error, log_success, update_stats, get_stats

semaphore = asyncio.Semaphore(MAX_CONCURRENT)

async def health_check(session: aiohttp.ClientSession, session_tg: aiohttp.ClientSession) -> bool:
    log_info("Running health check...")
    github_ok = await check_github_api(session)
    telegram_ok = await check_telegram_bot(session_tg, BOT_TOKEN, CHAT_ID)
    
    if not github_ok:
        log_error("Health check failed: GitHub API unreachable")
    if not telegram_ok:
        log_error("Health check failed: Telegram Bot unreachable")
    
    if github_ok and telegram_ok:
        log_info("Health check passed")
    
    return github_ok and telegram_ok

async def process(session: aiohttp.ClientSession, session_tg: aiohttp.ClientSession, url: str) -> None:
    async with semaphore:
        release = None
        try:
            log_info(f"Processing repository: {url}")
            release = await fetch_release(session, url)
            if not release:
                log_info(f"No release found for {url}")
                return

            repo_key = get_repo_key(url)
            repo_name = get_repo_name(url)
            release_id = release["id"]
            tag = release["tag_name"]
            
            log_info(f"Repository: {repo_name}, Tag: {tag}, Release ID: {release_id}")

            if release.get("prerelease", False):
                log_info(f"Skipping prerelease {repo_name} - {tag}")
                return

            is_new = await check_and_update_cache(repo_key, release_id, tag)
            if not is_new:
                log_info(f"Skipping {repo_name} - already processed (tag: {tag})")
                return
            
            log_info(f"New release detected for {repo_name}: {tag}")

            assets = release.get("assets", [])
            if not assets:
                log_info(f"No assets found for {repo_name} - {tag}")
                return

            sent = False
            sent_combinations: Set[str] = set()

            for idx, a in enumerate(assets):
                filename = a["name"]

                if not is_valid_asset(filename):
                    log_info(f"Skipping invalid asset: {filename}")
                    continue

                file_size = a["size"]
                arch = detect_arch(filename, url, tag, repo_name)
                system = detect_system(filename, url, repo_name)
                size_str = format_size(file_size)
                url_dl = a["browser_download_url"]
                
                log_info(f"Processing asset {idx+1}/{len(assets)}: {filename}")
                log_info(f"  Size: {file_size} bytes, Arch: {arch}, System: {system}")

                if file_size > SIZE_LIMIT:
                    log_info(f"  File exceeds size limit ({file_size} > {SIZE_LIMIT}), sending as link only")
                    caption = build_caption(repo_name, tag, system, arch, size_str, is_large=True)
                    await send_link(session_tg, BOT_TOKEN, CHAT_ID, caption, url_dl)
                    sent = True
                    update_stats(file_size, True)
                    continue

                combo = f"{system}_{arch}"
                if combo in sent_combinations:
                    log_info(f"  Skipping duplicate combo: {combo}")
                    continue
                sent_combinations.add(combo)

                caption = build_caption(repo_name, tag, system, arch, size_str, is_large=False)

                data = None
                download_success = False
                for retry in range(2):
                    try:
                        timeout = aiohttp.ClientTimeout(total=DOWNLOAD_TIMEOUT, connect=REQUEST_TIMEOUT)
                        async with session.get(url_dl, timeout=timeout) as r:
                            if r.status == 200:
                                data = await r.read()
                                if len(data) <= SIZE_LIMIT:
                                    download_success = True
                                    log_info(f"  Downloaded {len(data)} bytes successfully (attempt {retry+1})")
                                    break
                                else:
                                    log_info(f"  Downloaded file too large: {len(data)} bytes")
                                    download_success = False
                                    break
                            else:
                                log_error(f"  Download failed: HTTP {r.status} for {filename}")
                    except asyncio.TimeoutError:
                        log_error(f"  Timeout downloading {filename} (retry {retry+1}/2)")
                    except Exception as e:
                        log_error(f"  Download error for {filename}: {e} (retry {retry+1}/2)")
                    
                    if retry < 1:
                        log_info(f"  Retrying download in 3 seconds...")
                        await asyncio.sleep(3)

                if download_success and data and len(data) <= SIZE_LIMIT:
                    log_info(f"  Sending file to Telegram: {filename}")
                    ok = await send_file(session_tg, BOT_TOKEN, CHAT_ID, data, filename, caption, url_dl)
                    if not ok:
                        log_info(f"  File send failed, sending as link instead")
                        await send_link(session_tg, BOT_TOKEN, CHAT_ID, caption, url_dl)
                        update_stats(file_size, True)
                    else:
                        update_stats(file_size, True)
                else:
                    if data and len(data) > SIZE_LIMIT:
                        log_info(f"  File too large after download ({len(data)} bytes), sending as link")
                    else:
                        log_info(f"  Download failed, sending as link instead")
                    await send_link(session_tg, BOT_TOKEN, CHAT_ID, caption, url_dl)
                    update_stats(file_size, True)

                sent = True
                await asyncio.sleep(2)

            if sent:
                log_success(repo_name, tag)
            else:
                log_info(f"No valid assets sent for {repo_name} - {tag}")

        except Exception as e:
            log_error(f"Error processing {url}: {str(e)}", exc=True)
            update_stats(0, False)
        finally:
            await asyncio.sleep(1)

async def main() -> None:
    log_info("=" * 50)
    log_info("Release Bot Started")
    log_info("=" * 50)
    
    connector = aiohttp.TCPConnector(limit=20, ttl_dns_cache=300)
    async with aiohttp.ClientSession(connector=connector) as session, aiohttp.ClientSession(connector=connector) as session_tg:
        health_ok = await health_check(session, session_tg)
        if not health_ok:
            log_error("Health check failed, continuing anyway...")
        
        current_repos = {}
        for url in REPOS:
            repo_key = get_repo_key(url)
            current_repos[repo_key] = True
        
        log_info(f"Checking {len(current_repos)} repositories for updates")
        await clear_old_cache(current_repos)
        
        tasks = [process(session, session_tg, url) for url in REPOS]
        await asyncio.gather(*tasks)
        
        stats = get_stats()
        log_info("=" * 50)
        log_info("Final Statistics:")
        log_info(f"  Releases sent: {stats['releases_sent']}")
        log_info(f"  Total size: {stats['total_size_bytes']} bytes ({stats['total_size_bytes'] // (1024*1024)} MB)")
        log_info(f"  Success rate: {stats['success_rate']:.2f}%")
        log_info(f"  Total attempts: {stats['total_attempts']}")
        log_info(f"  Successful attempts: {stats['successful_attempts']}")
        log_info("=" * 50)

    log_info("Release Bot Finished")
    log_info("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
