# github_api.py
import aiohttp
from logger import log_error
from config import GITHUB_TOKEN

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "release-bot"
}

if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

async def fetch_release(session, url):
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with session.get(url, headers=HEADERS, timeout=timeout) as resp:
            if resp.status != 200:
                log_error(f"GitHub API error {resp.status}: {url}")
                return None

            data = await resp.json()
            if not data:
                return None

            release = next(
                (r for r in data if not r.get("prerelease") and not r.get("draft")),
                None
            )

            if not release:
                return None

            return release

    except Exception as e:
        log_error(f"Fetch failed: {url} -> {e}")
        return None
