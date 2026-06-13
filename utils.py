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

def get_repo_key(url):
    return url.split("/repos/")[1].split("/releases")[0]

def get_repo_name(url):
    full_name = get_repo_key(url)
    for key, value in REPO_NAMES.items():
        if full_name == key or full_name.endswith(key):
            return value
    return full_name.split("/")[-1]

def detect_arch(filename):
    name = filename.lower()
    for arch, keys in ARCH_MAP.items():
        if any(x in name for x in keys):
            return arch
    return "unknown"

def detect_system(filename, repo_url=None, repo_name=None):
    text = filename.lower()
    if repo_url:
        text += " " + repo_url.lower()
    if repo_name:
        text += " " + repo_name.lower()

    if any(x in text for x in SYSTEM_MAP["Android"]):
        return "Android"
    if any(x in text for x in SYSTEM_MAP["Windows"]):
        return "Windows"
    if any(x in text for x in SYSTEM_MAP["Linux"]):
        return "Linux"
    if any(x in text for x in SYSTEM_MAP["macOS"]):
        return "macOS"

    return "Unknown"

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
