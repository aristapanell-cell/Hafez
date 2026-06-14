import aiohttp
import re
from typing import Optional, Dict, Any
from logger import log_error, log_info
from config import GITHUB_TOKEN, REQUEST_TIMEOUT

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "release-bot"
}

if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

async def fetch_release(session: aiohttp.ClientSession, url: str) -> Optional[Dict[str, Any]]:
    try:
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        async with session.get(url, headers=HEADERS, timeout=timeout) as resp:
            if resp.status != 200:
                log_error(f"GitHub API error {resp.status}: {url}")
                return None

            data = await resp.json()
            if not data or not isinstance(data, list):
                log_info(f"No releases found for {url}")
                return None

            release = next(
                (r for r in data if not r.get("prerelease") and not r.get("draft")),
                None
            )

            if not release:
                log_info(f"No stable release found for {url}")
                return None

            log_info(f"Found release: {release.get('tag_name')} for {url}")
            return release

    except Exception as e:
        log_error(f"Fetch failed: {url} -> {e}")
        return None

async def check_github_api(session: aiohttp.ClientSession) -> bool:
    try:
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        async with session.get("https://api.github.com/zen", headers=HEADERS, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False
