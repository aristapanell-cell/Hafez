import json
import os
import asyncio
from typing import Dict, Any
from logger import log_error

CACHE_FILE = "cache.json"
cache_lock = asyncio.Lock()

def load_cache() -> Dict[str, Any]:
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        log_error(f"Cache load failed: {e}")
        return {}

def save_cache(data: Dict[str, Any]) -> None:
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        log_error(f"Cache save failed: {e}")

async def update_cache(repo_key: str, release_id: int, tag: str) -> None:
    async with cache_lock:
        cache = load_cache()
        cache[repo_key] = {"release_id": release_id, "tag": tag}
        save_cache(cache)

async def check_and_update_cache(repo_key: str, release_id: int, tag: str) -> bool:
    async with cache_lock:
        cache = load_cache()
        if repo_key in cache and cache[repo_key].get("release_id") == release_id:
            return False
        cache[repo_key] = {"release_id": release_id, "tag": tag}
        save_cache(cache)
        return True

async def clear_old_cache(current_releases: Dict[str, bool]) -> None:
    async with cache_lock:
        cache = load_cache()
        updated = False
        for repo_key in list(cache.keys()):
            if repo_key not in current_releases:
                del cache[repo_key]
                updated = True
        if updated:
            save_cache(cache)
