from config import REPO_NAMES

def get_repo_name(url):
    full_name = url.split("/repos/")[1].split("/releases")[0]
    for key, value in REPO_NAMES.items():
        if key in full_name:
            return value
    return full_name.split("/")[-1]

def detect_arch(filename):
    name = filename.lower()
    if any(x in name for x in ["arm64-v8a", "aarch64", "arm64"]):
        return "arm64-v8a"
    if any(x in name for x in ["armeabi-v7a", "armv7"]):
        return "armeabi-v7a"
    if any(x in name for x in ["x86_64", "amd64", "x64"]):
        return "x86_64"
    if any(x in name for x in ["x86", "win32"]):
        return "x86"
    if "universal" in name or "all" in name:
        return "universal"
    return None

def is_valid_asset(name):
    low = name.lower()
    if "source code" in low:
        return False
    return any(low.endswith(ext) for ext in [".apk", ".exe", ".msi", ".zip"])

def format_size(size_bytes):
    if size_bytes < 1024 * 1024:
        return f"{size_bytes // 1024}KB"
    else:
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
