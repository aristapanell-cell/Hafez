import os
from typing import List

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")
if not CHAT_ID:
    raise ValueError("CHAT_ID environment variable is not set")

SIZE_LIMIT = 50 * 1024 * 1024
MAX_CONCURRENT = 5
REQUEST_TIMEOUT = 30
DOWNLOAD_TIMEOUT = 120

REPOS: List[str] = [
    "https://api.github.com/repos/hiddify/hiddify-app/releases",
    "https://api.github.com/repos/chen08209/FlClash/releases",
    "https://api.github.com/repos/2dust/v2rayN/releases",
    "https://api.github.com/repos/clash-verge-rev/clash-verge-rev/releases",
    "https://api.github.com/repos/MetaCubeX/ClashMetaForAndroid/releases",
    "https://api.github.com/repos/KaringX/karing/releases",
    "https://api.github.com/repos/Happ-proxy/happ-android/releases",
    "https://api.github.com/repos/2dust/v2rayNG/releases",
    "https://api.github.com/repos/ExclaveNetwork/Exclave/releases",
    "https://api.github.com/repos/openlibrecommunity/olcng/releases",
    "https://api.github.com/repos/dyhkwong/Exclave/releases",
    "https://api.github.com/repos/SagerNet/sing-box/releases",
    "https://api.github.com/repos/xchacha20-poly1305/husi/releases",
    "https://api.github.com/repos/MatsuriDayo/NekoBoxForAndroid/releases",
    "https://api.github.com/repos/center2055/OnionHop/releases",
    "https://api.github.com/repos/anonvector/SlipNet/releases",
    "https://api.github.com/repos/shirokhorshid/shirokhorshid-android/releases",
    "https://api.github.com/repos/GFW-knocker/MahsaNG/releases"
]

REPO_NAMES: dict = {
    "hiddify-app": "Hiddify",
    "FlClash": "FlClash",
    "v2rayN": "V2rayN",
    "clash-verge-rev": "Clash Verge",
    "ClashMetaForAndroid": "ClashMeta",
    "karing": "Karing",
    "happ-android": "Happ",
    "v2rayNG": "V2rayNG",
    "ExclaveNetwork/Exclave": "Exclave",
    "openlibrecommunity/olcng": "OLCNG",
    "sing-box": "SingBox",
    "husi": "Husi",
    "NekoBoxForAndroid": "NekoBox",
    "OnionHop": "OnionHop",
    "SlipNet": "SlipNet",
    "shirokhorshid-android": "Shirokhorshid",
    "MahsaNG": "MahsaNG"
}

REPO_PATTERNS: dict = {
    r"hiddify-app": "Hiddify",
    r"FlClash": "FlClash",
    r"v2rayN": "V2rayN",
    r"clash-verge-rev": "Clash Verge",
    r"ClashMetaForAndroid": "ClashMeta",
    r"karing": "Karing",
    r"happ-android": "Happ",
    r"v2rayNG": "V2rayNG",
    r"ExclaveNetwork/Exclave": "Exclave",
    r"openlibrecommunity/olcng": "OLCNG",
    r"sing-box": "SingBox",
    r"husi": "Husi",
    r"NekoBoxForAndroid": "NekoBox",
    r"OnionHop": "OnionHop",
    r"SlipNet": "SlipNet",
    r"shirokhorshid-android": "Shirokhorshid",
    r"MahsaNG": "MahsaNG"
}
