import re
from typing import Optional, Dict, Set, Tuple
from config import REPO_NAMES, REPO_PATTERNS

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

ARCH_PATTERNS = {
    "arm64-v8a": re.compile(r'(arm64|aarch64|arm64-v8a)', re.IGNORECASE),
    "armeabi-v7a": re.compile(r'(armeabi-v7a|armv7|armv7a|armeabi)(?!.*64)', re.IGNORECASE),
    "x86_64": re.compile(r'(x86_64|amd64|x64|64bit|64-bit)', re.IGNORECASE),
    "x86": re.compile(r'(x86|win32|i386|i686|32bit|32-bit)(?!.*64)', re.IGNORECASE),
    "universal": re.compile(r'(universal|all|multi|fat|any)', re.IGNORECASE)
}

def get_repo_key(url: str) -> str:
    return url.split("/repos/")[1].split("/releases")[0]

def get_repo_name(url: str) -> str:
    full_name = get_repo_key(url)
    for pattern, name in REPO_PATTERNS.items():
        if re.search(pattern, full_name):
            return name
    for key, value in REPO_NAMES.items():
        if full_name == key or full_name.endswith(key):
            return value
    return full_name.split("/")[-1]

def detect_arch(filename: str, repo_url: Optional[str] = None, release_name: Optional[str] = None, repo_name: Optional[str] = None) -> str:
    name_lower = filename.lower()
    
    for arch, pattern in ARCH_PATTERNS.items():
        if pattern.search(name_lower):
            return arch
    
    if repo_name == "V2rayN":
        if "win" in name_lower or "windows" in name_lower:
            return "x86_64"
        if "linux" in name_lower:
            return "x86_64"
        return "x86_64"
    
    if repo_name == "Happ":
        return "universal"
    
    if "win" in name_lower or "windows" in name_lower:
        return "x86_64"
    
    if name_lower.endswith('.apk'):
        if "x86" in name_lower:
            return "x86"
        return "universal"
    
    if name_lower.endswith('.deb') or name_lower.endswith('.rpm'):
        if "arm64" in name_lower:
            return "arm64-v8a"
        return "x86_64"
    
    if name_lower.endswith('.dmg') or name_lower.endswith('.pkg'):
        if "arm64" in name_lower:
            return "arm64-v8a"
        return "universal"
    
    return "unknown"

def detect_system(filename: str, repo_url: Optional[str] = None, repo_name: Optional[str] = None) -> str:
    name_lower = filename.lower()
    
    if "desktop" in name_lower and ("win" in name_lower or "windows" in name_lower):
        return "Windows Desktop"
    
    if name_lower.endswith('.apk'):
        return "Android"
    
    if name_lower.endswith('.deb') or name_lower.endswith('.rpm') or name_lower.endswith('.AppImage'):
        return "Linux"
    
    if name_lower.endswith('.dmg') or name_lower.endswith('.pkg'):
        return "macOS"
    
    if name_lower.endswith('.exe') or name_lower.endswith('.msi'):
        return "Windows"
    
    if repo_name == "V2rayN":
        if "linux" in name_lower:
            return "Linux"
        if "mac" in name_lower or "osx" in name_lower:
            return "macOS"
        if "win" in name_lower or "windows" in name_lower:
            if "desktop" in name_lower:
                return "Windows Desktop"
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
    
    if repo_name == "ClashMeta" or repo_name == "FlClash":
        if "desktop" in name_lower or "win" in name_lower or "linux" in name_lower:
            if "win" in name_lower:
                return "Windows"
            if "linux" in name_lower:
                return "Linux"
        return "Android"
    
    for system, keywords in SYSTEM_MAP.items():
        for keyword in keywords:
            if keyword in name_lower:
                if system == "Windows" and "desktop" in name_lower:
                    return "Windows Desktop"
                return system
    
    if any(x in name_lower for x in ["apk", "arm64", "armeabi"]):
        return "Android"
    
    if any(x in name_lower for x in ["exe", "msi", "win"]):
        if "desktop" in name_lower:
            return "Windows Desktop"
        return "Windows"
    
    if any(x in name_lower for x in ["dmg", "pkg", "mac"]):
        return "macOS"
    
    if any(x in name_lower for x in ["deb", "rpm", "linux", "appimage"]):
        return "Linux"
    
    return "Unknown"

def is_valid_asset(name: str) -> bool:
    low = name.lower()
    if "source code" in low:
        return False
    return any(low.endswith(ext) for ext in [".apk", ".exe", ".msi", ".zip", ".dmg", ".pkg", ".deb", ".rpm", ".AppImage"])

def format_size(size_bytes: int) -> str:
    if size_bytes < 1024 * 1024:
        return f"{size_bytes // 1024}KB"
    return f"{size_bytes // (1024 * 1024)}MB"

def build_caption(repo_name: str, tag: str, system: str, arch: str, size_str: str, is_large: bool = False) -> str:
    caption = f"""
✨ <b>بروزرسانی جدید</b> ✨

┌───────────────•
│ 🆔 <b>{repo_name}</b>
│ 📌 نسخه: <code>{tag}</code>
├───────────────•
│ 🖥 سیستم عامل: {system}
│ 🏗 معماری: <code>{arch}</code>
│ 💾 حجم: {size_str}
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
│ 💾 حجم: {size_str}
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
