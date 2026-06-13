# utils.py

import re
from config import REPO_NAMES

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

ARCH_SYSTEM_MAP = {
    "arm64": ("Android", "arm64-v8a"),
    "aarch64": ("Android", "arm64-v8a"),
    "arm64-v8a": ("Android", "arm64-v8a"),
    "armeabi-v7a": ("Android", "armeabi-v7a"),
    "armv7": ("Android", "armeabi-v7a"),
    "armeabi": ("Android", "armeabi-v7a"),
    "x86_64": ("Windows", "x86_64"),
    "amd64": ("Windows", "x86_64"),
    "x64": ("Windows", "x86_64"),
    "x86": ("Windows", "x86"),
    "win32": ("Windows", "x86"),
    "i386": ("Linux", "x86"),
    "i686": ("Linux", "x86")
}

def get_repo_key(url):
    return url.split("/repos/")[1].split("/releases")[0]

def get_repo_name(url):
    full_name = get_repo_key(url)
    for key, value in REPO_NAMES.items():
        if full_name == key or full_name.endswith(key):
            return value
    return full_name.split("/")[-1]

def detect_arch(filename, repo_url=None, release_name=None):
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
    
    for arch, keys in ARCH_MAP.items():
        for key in keys:
            if key in name_lower:
                if arch == "arm64-v8a" and ("arm64" in name_lower or "aarch64" in name_lower):
                    return arch
                elif arch == "armeabi-v7a" and ("armeabi" in name_lower or "armv7" in name_lower):
                    return arch
                elif key in name_lower:
                    return arch
    
    if release_name:
        release_lower = release_name.lower()
        for arch, keys in ARCH_MAP.items():
            for key in keys:
                if key in release_lower:
                    return arch
    
    if repo_url:
        repo_lower = repo_url.lower()
        if "arm64" in repo_lower or "aarch64" in repo_lower:
            return "arm64-v8a"
        elif "x86_64" in repo_lower or "amd64" in repo_lower:
            return "x86_64"
    
    if "win" in name_lower or "windows" in name_lower:
        return "x86_64"
    
    return "unknown"

def detect_system(filename, repo_url=None, repo_name=None):
    name_lower = filename.lower()
    
    if name_lower.endswith('.apk'):
        return "Android"
    
    if name_lower.endswith(('.exe', '.msi')):
        return "Windows"
    
    if name_lower.endswith('.dmg'):
        return "macOS"
    
    if name_lower.endswith(('.deb', '.rpm', '.AppImage')):
        return "Linux"
    
    if repo_name and "v2ray" in repo_name.lower():
        if "win" in name_lower or "windows" in name_lower or "exe" in name_lower:
            return "Windows"
        if "linux" in name_lower:
            return "Linux"
        if "mac" in name_lower or "osx" in name_lower:
            return "macOS"
        return "Windows"
    
    for system, keywords in SYSTEM_MAP.items():
        for keyword in keywords:
            if keyword in name_lower:
                return system
    
    for system, keywords in SYSTEM_MAP.items():
        for keyword in keywords:
            if repo_url and keyword in repo_url.lower():
                return system
            if repo_name and keyword in repo_name.lower():
                return system
    
    if any(x in name_lower for x in ["apk", "arm64", "armeabi", "v7a"]):
        return "Android"
    
    if any(x in name_lower for x in ["exe", "msi", "win"]):
        return "Windows"
    
    if any(x in name_lower for x in ["dmg", "pkg", "mac"]):
        return "macOS"
    
    if any(x in name_lower for x in ["appimage", "deb", "rpm", "linux"]):
        return "Linux"
    
    return "Unknown"

def normalize_arch(arch, filename, system="Unknown"):
    if arch != "unknown":
        return arch
    
    name_lower = filename.lower()
    
    if system == "Windows":
        if "64" in name_lower or "x64" in name_lower or "amd64" in name_lower:
            return "x86_64"
        return "x86"
    elif system == "Android":
        if "arm64" in name_lower or "aarch64" in name_lower:
            return "arm64-v8a"
        elif "arm" in name_lower or "armeabi" in name_lower:
            return "armeabi-v7a"
        return "universal"
    elif system == "macOS":
        if "arm64" in name_lower or "aarch64" in name_lower:
            return "arm64-v8a"
        return "x86_64"
    elif system == "Linux":
        if "arm64" in name_lower or "aarch64" in name_lower:
            return "arm64-v8a"
        elif "arm" in name_lower:
            return "armeabi-v7a"
        return "x86_64"
    
    return "unknown"

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
