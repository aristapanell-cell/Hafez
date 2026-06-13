from config import REPO_NAMES

ARCH_MAP = {
    "arm64-v8a": ["arm64-v8a", "aarch64", "arm64"],
    "armeabi-v7a": ["armeabi-v7a", "armv7", "armv7a"],
    "x86_64": ["x86_64", "amd64", "x64", "64bit"],
    "x86": ["x86", "win32", "i386", "i686"],
    "universal": ["universal", "all", "multi", "fat"]
}

SYSTEM_MAP = {
    "Android": ["android", "apk", "arm", "aarch64", "arm64", "armeabi", "v7a"],
    "Windows": ["windows", ".exe", ".msi", "win"],
    "Linux": ["linux", "appimage", "deb", "rpm", "ubuntu", "debian"],
    "macOS": ["mac", "darwin", "dmg", "osx", "macos"]
}

ARCH_SYSTEM_MAP = {
    "arm64": ("Android", "arm64-v8a"),
    "aarch64": ("Android", "arm64-v8a"),
    "arm64-v8a": ("Android", "arm64-v8a"),
    "armeabi-v7a": ("Android", "armeabi-v7a"),
    "armv7": ("Android", "armeabi-v7a"),
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
    name = filename.lower()

    for arch, keys in ARCH_MAP.items():
        if any(x in name for x in keys):
            return arch

    if repo_url:
        repo = repo_url.lower()
        for arch, keys in ARCH_MAP.items():
            if any(x in repo for x in keys):
                return arch

    if release_name:
        rel = release_name.lower()
        for arch, keys in ARCH_MAP.items():
            if any(x in rel for x in keys):
                return arch

    return "unknown"

def detect_system(filename, repo_url=None, repo_name=None):
    text = filename.lower()
    repo = (repo_url.split("/repos/")[1].split("/releases")[0].lower() if repo_url else "")
    combined = text + " " + repo + " " + (repo_name.lower() if repo_name else "")

    for key, (system, arch) in ARCH_SYSTEM_MAP.items():
        if key in combined:
            return system

    for sys, keys in SYSTEM_MAP.items():
        if any(x in combined for x in keys):
            return sys

    if "android" in repo or "android" in combined:
        return "Android"

    if any(x in repo for x in ["windows", "verge", "v2rayn"]):
        return "Windows"

    if any(x in combined for x in ["apk", "arm64", "armeabi", "v7a"]):
        return "Android"

    if any(x in combined for x in ["exe", "msi"]):
        return "Windows"

    if any(x in combined for x in ["dmg", "mac"]):
        return "macOS"

    if any(x in combined for x in ["linux", "appimage", "deb", "rpm"]):
        return "Linux"

    return "Unknown"

def normalize_arch(arch, filename):
    if arch != "unknown":
        return arch
    name = filename.lower()
    for k in ARCH_MAP:
        if k in name:
            return k
    return "unknown"

def is_valid_asset(name):
    low = name.lower()
    if "source code" in low:
        return False
    return any(low.endswith(ext) for ext in [".apk", ".exe", ".msi", ".zip", ".tar.gz"])

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
