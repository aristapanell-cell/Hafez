import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

SIZE_LIMIT = 50 * 1024 * 1024
MAX_CONCURRENT = 5

REPOS = [
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

REPO_NAMES = {
    "hiddify-app": "Hiddify",
    "FlClash": "FlClash",
    "v2rayN": "V2rayN",
    "clash-verge-rev": "Clash Verge",
    "ClashMetaForAndroid": "ClashMeta",
    "karing": "Karing",
    "happ-android": "Happ",
    "v2rayNG": "V2rayNG",
    "ExclaveNetwork/Exclave": "Exclave",
    "dyhkwong/Exclave": "Exclave-Alt",
    "sing-box": "SingBox",
    "husi": "Husi",
    "NekoBoxForAndroid": "NekoBox",
    "OnionHop": "OnionHop",
    "SlipNet": "SlipNet",
    "shirokhorshid-android": "Shirokhorshid",
    "MahsaNG": "MahsaNG"
}
