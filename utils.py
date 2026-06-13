# utils.py

import re
from config import REPO_NAMES
from logger import log_info

ARCH_MAP = {
    "arm64-v8a": ["arm64-v8a", "aarch64", "arm64", "arm64-v8a"],
    "armeabi-v7a": ["armeabi-v7a", "armv7", "armv7a", "armeabi"],
    "x86_64": ["x86_64", "amd64", "x64", "64bit", "64-bit", "_64", ".64"],
    "x86": ["x86", "win32", "i386", "i686", "32bit", "32-bit", "_32", ".32"],
    "universal": ["universal", "all", "multi", "fat", "any"]
}

SYSTEM_MAP = {
    "Windows": ["windows", "win", ".exe", ".msi", "win64", "win32", "win-x64", "win-x86", "pc"],
    "Android": ["android", ".apk", "arm64", "armeabi", "aarch64", "android-arm64", "play"],
    "Linux": ["linux", "appimage", ".deb", ".rpm", "ubuntu", "debian", "linux-x64", "gnu"],
    "macOS": ["mac", "darwin", ".dmg", "osx", "macos", "macosx", ".pkg"]
}

def get_repo_key(url):
    return url.split("/repos/")[1].split("/releases")[0]

def get_repo_name(url):
    full_name = get_repo_key(url)
    for key, value in REPO_NAMES.items():
        if full_name == key or full_name.endswith(key):
            return value
    return full_name.split("/")[-1]

def detect_arch(filename, repo_url=None, release_name=None, repo_name=None):
    name_lower = filename.lower()
    
    if "arm64" in name_lower or "aarch64" in name_lower or "arm64-v8a" in name_lower:
        return "arm64-v8a"
    
    if "armeabi-v7a" in name_lower or "armv7" in name_lower:
        return "armeabi-v7a"
    
    if "armeabi" in name_lower and "64" not in name_lower:
        return "armeabi-v7a"
    
    if "x86_64" in name_lower or "amd64" in name_lower or "x64" in name_lower:
        if "arm" not in name_lower:
            return "x86_64"
    
    if "x86" in name_lower or "i386" in name_lower or "i686" in name_lower:
        if "64" not in name_lower and "arm" not in name_lower:
            return "x86"
    
    if "universal" in name_lower:
        return "universal"
    
    if repo_name == "V2rayN":
        if "win" in name_lower or "windows" in name_lower:
            return "x86_64"
        if "linux" in name_lower:
            return "x86_64"
        return "x86_64"
    
    if "win" in name_lower or "windows" in name_lower:
        return "x86_64"
    
    return "unknown"

def detect_system(filename, repo_url=None, repo_name=None):
    name_lower = filename.lower()
    
    if name_lower.endswith('.apk'):
        return "Android"
    
    if name_lower.endswith('.deb') or name_lower.endswith('.rpm') or name_lower.endswith('.AppImage'):
        return "Linux"
    
    if name_lower.endswith('.dmg'):
        return "macOS"
    
    if name_lower.endswith('.exe') or name_lower.endswith('.msi'):
        return "Windows"
    
    if repo_name == "V2rayN":
        if "linux" in name_lower:
            return "Linux"
        if "mac" in name_lower or "osx" in name_lower:
            return "macOS"
        if "win" in name_lower or "windows" in name_lower:
            return "Windows"
        if ".deb" in name_lower:
            return "Linux"
        if ".dmg" in name_lower:
            return "macOS"
        return "Windows"
    
    if repo_name == "Clash Verge":
        if "android" in name_lower:
            return "Android"
        if "linux" in name_lower:
            return "Linux"
        if "mac" in name_lower or "darwin" in name_lower:
            return "macOS"
        if "win" in name_lower or "windows" in name_lower:
            return "Windows"
        return "Windows"
    
    if repo_name == "Hiddify":
        if "android" in name_lower:
            return "Android"
        if "linux" in name_lower:
            return "Linux"
        if "mac" in name_lower or "darwin" in name_lower:
            return "macOS"
        if "win" in name_lower or "windows" in name_lower:
            return "Windows"
        return "Windows"
    
    for system, keywords in SYSTEM_MAP.items():
        for keyword in keywords:
            if keyword in name_lower:
                return system
    
    if any(x in name_lower for x in ["apk", "arm64", "armeabi"]):
        return "Android"
    
    if any(x in name_lower for x in ["exe", "msi", "win"]):
        return "Windows"
    
    if any(x in name_lower for x in ["dmg", "pkg", "mac"]):
        return "macOS"
    
    if any(x in name_lower for x in ["deb", "rpm", "linux", "appimage"]):
        return "Linux"
    
    return "Unknown"

def is_valid_asset(name):
    low = name.lower()
    if "source code" in low:
        return False
    return any(low.endswith(ext) for ext in [".apk", ".exe", ".msi", ".zip", ".tar.gz", ".dmg", ".pkg", ".deb", ".rpm", ".AppImage"])

def format_size(size_bytes):
    if size_bytes < 1024 * 1024:
        return f"{size_bytes // 1024}KB"
    return f"{size_bytes // (1024 * 1024)}MB"

def build_caption(repo_name, tag, system, arch, size_mb, is_large=False):
    caption = f"""
✨ <b>بروزرسانی جدید</b> ✨

┌───────────────•
│ 🆔 <b>{repo_name}</b>
│ 📌 نسخه: <code>{tag}</code>
├───────────────•
│ 🖥 سیستم عامل: {system}
│ 🏗 معماری: <code>{arch}</code>
│ 💾 حجم: {size_mb}
└───────────────•"""

    if is_large:
        caption = f"""
✨ <b>بروزرسانی جدید</b> ✨

┌───────────────•
│ 🆔 <b>{repo_name}</b>
│ 📌 نسخه: <code>{tag}</code>
├───────────────•
│ 🖥 سیستم عامل: {system}
│ 🏗 معماری: <code>{arch}</code>
│ 💾 حجم: {size_mb}
├───────────────•
│ ⚠️ <b>توجه:</b> حجم فایل بیشتر از ۵۰ مگابایت
│ 📎 دانلود فقط از طریق لینک مستقیم
└───────────────•"""

    caption += f"""

➖➖➖➖➖➖➖➖
<blockquote>@aristapanel</blockquote>
➖➖➖➖➖➖➖➖

#Arista #{repo_name} #بروزرسانی"""

    return caption
