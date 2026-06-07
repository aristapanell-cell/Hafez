import os
import sqlite3
import random
import requests
import importlib.util
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]
DB = "faals.db"
DATA_URL = "https://raw.githubusercontent.com/Matinsojoudi/faal-hafez/refs/heads/main/create_db.py"
DATA_FILE = "data/create_db.py"

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
    cur.execute("CREATE TABLE IF NOT EXISTS faals (id INTEGER PRIMARY KEY, Poem TEXT, Interpretation TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS sent (month INTEGER, fal_id INTEGER, day TEXT, UNIQUE(month, fal_id, day))")
    conn.commit()
    conn.close()

def load_faals():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM faals")
    count = cur.fetchone()[0]
    conn.close()

    if count > 0:
        return

    os.makedirs("data", exist_ok=True)

    if not os.path.exists(DATA_FILE):
        r = requests.get(DATA_URL, timeout=60)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            f.write(r.text)

    spec = importlib.util.spec_from_file_location("create_db", DATA_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.executemany("INSERT OR REPLACE INTO faals VALUES (?,?,?)", module.data)
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
        rows = cur.fetchall()
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
    conn.execute("INSERT OR IGNORE INTO sent VALUES (?,?,?)", (month, fid, day))
    conn.commit()
    conn.close()

def extract_bit(poem):
    lines = [x.strip() for x in poem.split("\r\n") if x.strip()]
    pairs = [(lines[i], lines[i+1] if i+1 < len(lines) else "") for i in range(0, len(lines), 2)]
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

def should_run(today):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM sent WHERE day=? LIMIT 1", (today,))
    ok = cur.fetchone()
    conn.close()
    return ok is None

def main():
    now = datetime.now(timezone.utc) + IRAN_OFFSET
    today = now.date().isoformat()

    init_db()
    load_faals()

    if not should_run(today):
        return

    for m in range(1, 13):
        name, emoji = MONTHS[m]
        used = get_used(m, today)
        fid, poem, interp = pick_fal(used)

        bit = extract_bit(poem)
        send(build(m, emoji, bit, interp))
        save(m, fid, today)

if __name__ == "__main__":
    main()
