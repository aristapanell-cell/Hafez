# cache.py
import json
import os
import asyncio

CACHE_FILE = "cache.json"
cache_lock = asyncio.Lock()

def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_cache(data):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except IOError:
        pass

async def update_cache(repo_key, release_id, tag):
    async with cache_lock:
        cache = load_cache()
        cache[repo_key] = {"release_id": release_id, "tag": tag}
        save_cache(cache)

async def check_and_update_cache(repo_key, release_id, tag):
    async with cache_lock:
        cache = load_cache()
        if repo_key in cache and cache[repo_key].get("release_id") == release_id:
            return False
        cache[repo_key] = {"release_id": release_id, "tag": tag}
        save_cache(cache)
        return True

async def clear_old_cache(current_releases):
    async with cache_lock:
        cache = load_cache()
        updated = False
        for repo_key in list(cache.keys()):
            if repo_key not in current_releases:
                del cache[repo_key]
                updated = True
        if updated:
            save_cache(cache)
