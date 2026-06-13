import json
import os
import asyncio

CACHE_FILE = "cache.json"
cache_lock = asyncio.Lock()

def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    with open(CACHE_FILE, "r") as f:
        return json.load(f)

def save_cache(data):
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=2)

async def update_cache(repo_key, release_id, tag):
    async with cache_lock:
        cache = load_cache()
        cache[repo_key] = {"release_id": release_id, "tag": tag}
        save_cache(cache)
