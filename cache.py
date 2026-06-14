import json
import os
import asyncio
from typing import Dict, Any
from logger import log_error, log_info

CACHE_FILE = "cache.json"
cache_lock = asyncio.Lock()

def load_cache() -> Dict[str, Any]:
    if not os.path.exists(CACHE_FILE):
        log_info("Cache file not found, creating new cache")
        return {}
    try:
        with open(CACHE_FILE, "r") as f:
            cache_data = json.load(f)
            log_info(f"Cache loaded with {len(cache_data)} entries")
            return cache_data
    except (json.JSONDecodeError, IOError) as e:
        log_error(f"Cache load failed: {e}")
        return {}

def save_cache(data: Dict[str, Any]) -> None:
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f, indent=2)
        log_info(f"Cache saved with {len(data)} entries")
    except IOError as e:
        log_error(f"Cache save failed: {e}")

async def update_cache(repo_key: str, release_id: int, tag: str) -> None:
    async with cache_lock:
        cache = load_cache()
        old_tag = cache.get(repo_key, {}).get("tag", "None")
        cache[repo_key] = {"release_id": release_id, "tag": tag}
        save_cache(cache)
        log_info(f"Cache updated for {repo_key}: {old_tag} -> {tag}")

async def check_and_update_cache(repo_key: str, release_id: int, tag: str) -> bool:
    async with cache_lock:
        cache = load_cache()
        if repo_key in cache:
            cached_release_id = cache[repo_key].get("release_id")
            cached_tag = cache[repo_key].get("tag", "Unknown")
            if cached_release_id == release_id:
                log_info(f"Cache HIT for {repo_key}: current tag {cached_tag} == {tag}, skipping")
                return False
            else:
                log_info(f"Cache MISS for {repo_key}: cached tag {cached_tag} != new tag {tag}, will process")
        else:
            log_info(f"Cache MISS for {repo_key}: no previous cache entry, will process")
        
        cache[repo_key] = {"release_id": release_id, "tag": tag}
        save_cache(cache)
        return True

async def clear_old_cache(current_releases: Dict[str, bool]) -> None:
    async with cache_lock:
        cache = load_cache()
        updated = False
        for repo_key in list(cache.keys()):
            if repo_key not in current_releases:
                log_info(f"Removing obsolete cache entry: {repo_key}")
                del cache[repo_key]
                updated = True
        if updated:
            save_cache(cache)
        else:
            log_info("No obsolete cache entries to remove")

async def clear_all_cache() -> None:
    async with cache_lock:
        log_info("Clearing all cache entries")
        save_cache({})
