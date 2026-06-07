import os
import sqlite3
import random
import requests
import re
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

DB = "faals.db"
DATA_URL = "https://raw.githubusercontent.com/Matinsojoudi/faal-hafez/refs/heads/main/create_db.py"

IRAN_OFFSET = timedelta(hours=3, minutes=30)

MONTHS = {
    1: ("فروردین", "🐏"),
    2: ("اردیبهشت", "🐂"),
    3: ("خرداد", "🦋"),
    4: ("تیر", "🦀"),
    5: ("مرداد", "🦁"),
    6: ("شهریور", "🌾"),
    7: ("مهر", "⚖️"),
    8: ("آبان", "🦂"),
    9: ("آذر", "🏹"),
    10: ("دی", "🐐"),
    11: ("بهمن", "🏺"),
    12: ("اسفند", "🐟"),
}


def send(text):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML"},
        timeout=30
    )


def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS faals (
            id INTEGER PRIMARY KEY,
            Poem TEXT,
            Interpretation TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sent (
            month INTEGER,
            fal_id INTEGER,
            day TEXT,
            UNIQUE(month, fal_id, day)
        )
    """)

    conn.commit()
    conn.close()


# =========================
# PRODUCTION SAFE LOADER
# =========================
def load_faals():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM faals")
    if cur.fetchone()[0] > 0:
        conn.close()
        return

    text = requests.get(DATA_URL, timeout=60).text

    # استخراج tuple ها بدون exec
    pattern = r"\(\s*(\d+)\s*,\s*'([\s\S]*?)'\s*,\s*'([\s\S]*?)'\s*\)"
    rows = re.findall(pattern, text)

    clean_rows = []
    for r in rows:
        fid = int(r[0])
        poem = r[1].replace("\\r\\n", "\n").replace("\\n", "\n")
        interp = r[2].replace("\\r\\n", "\n").replace("\\n", "\n")
        clean_rows.append((fid, poem, interp))

    cur.executemany(
        "INSERT OR REPLACE INTO faals VALUES (?,?,?)",
        clean_rows
    )

    conn.commit()
    conn.close()


def get_used(month, day):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT fal_id FROM sent WHERE month=? AND day=?", (month, day))
    used = [i[0] for i in cur.fetchall()]
    conn.close()
    return used


def pick_fal(exclude):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    if exclude:
        q = f"SELECT * FROM faals WHERE id NOT IN ({','.join(['?']*len(exclude))})"
        cur.execute(q, exclude)
    else:
        cur.execute("SELECT * FROM faals")

    rows = cur.fetchall()
    conn.close()

    if not rows:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("SELECT * FROM faals")
        rows = cur.fetchall()
        conn.close()

    return random.choice(rows)


def save(month, fid, day):
    conn = sqlite3.connect(DB)
    conn.execute(
        "INSERT OR IGNORE INTO sent VALUES (?,?,?)",
        (month, fid, day)
    )
    conn.commit()
    conn.close()


def extract_bit(poem):
    lines = [x.strip() for x in poem.split("\r\n") if x.strip()]
    pairs = [(lines[i], lines[i+1] if i+1 < len(lines) else "")
             for i in range(0, len(lines), 2)]

    if not pairs:
        return ""

    a, b = random.choice(pairs)
    return (a + "\n" + b).strip()


def build(month, emoji, bit, interp):
    name = MONTHS[month][0]
    return f"""📖 <b>فال و سرگرمی</b>
{emoji} متولدین {name}

🌺🍂🍃🌺🍂🍃🌺🍂🍃

<b>{bit}</b>

{interp}

🌺
🍂
🍃
🌺🍂
🍂🍃🌺
🍃🌺🍂🍃
🌺🍂🍃🌺🍂🍃🌺🍂🍃

➖➖➖➖➖➖➖➖
<blockquote>@aristapanel</blockquote>
➖➖➖➖➖➖➖➖
#فال_حافظ #سرگرمی #آریستا"""
