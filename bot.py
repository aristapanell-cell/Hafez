import os
import sqlite3
import random
import requests
import re
import time
from datetime import datetime, timezone, timedelta


# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

DB = "faals.db"

DATA_URL = (
    "https://raw.githubusercontent.com/Matinsojoudi/"
    "faal-hafez/refs/heads/main/create_db.py"
)

# Iran timezone
IRAN_OFFSET = timedelta(hours=3, minutes=30)

MAX_RETRY = 5


# =========================================================
# JALALI / PERSIAN DATE
# =========================================================

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


WEEKDAYS = {
    0: "دوشنبه",
    1: "سه‌شنبه",
    2: "چهارشنبه",
    3: "پنجشنبه",
    4: "جمعه",
    5: "شنبه",
    6: "یکشنبه",
}


PERSIAN_DIGITS = str.maketrans(
    "0123456789",
    "۰۱۲۳۴۵۶۷۸۹"
)


def to_persian_digits(value):
    """
    Convert English digits to Persian digits.
    """
    return str(value).translate(PERSIAN_DIGITS)


def gregorian_to_jalali(gy, gm, gd):
    """
    Convert Gregorian date to Jalali date.

    Returns:
        (jy, jm, jd)
    """

    g_days_in_month = [
        31, 28, 31, 30, 31, 30,
        31, 31, 30, 31, 30, 31
    ]

    j_days_in_month = [
        31, 31, 31, 31, 31, 31,
        30, 30, 30, 30, 30, 29
    ]

    gy -= 1600
    gm -= 1
    gd -= 1

    g_day_no = (
        365 * gy
        + (gy + 3) // 4
        - (gy + 99) // 100
        + (gy + 399) // 400
    )

    for i in range(gm):
        g_day_no += g_days_in_month[i]

    if gm > 1 and (
        gy % 4 == 0
        and (gy % 100 != 0 or gy % 400 == 0)
    ):
        g_day_no += 1

    g_day_no += gd

    j_day_no = g_day_no - 79

    j_np = j_day_no // 12053
    j_day_no %= 12053

    jy = 979 + 33 * j_np + 4 * (j_day_no // 1461)

    j_day_no %= 1461

    if j_day_no >= 366:
        jy += (j_day_no - 1) // 365
        j_day_no = (j_day_no - 1) % 365

    jm = 0

    while (
        jm < 11
        and j_day_no >= j_days_in_month[jm]
    ):
        j_day_no -= j_days_in_month[jm]
        jm += 1

    jd = j_day_no + 1

    return jy, jm + 1, jd


def get_iran_now():
    """
    Current datetime in Iran timezone.
    """

    return datetime.now(timezone.utc) + IRAN_OFFSET


def get_today_jalali():
    """
    Return today's Jalali information according to Iran time.

    Returns:
        weekday_name,
        jalali_year,
        jalali_month,
        jalali_day
    """

    now = get_iran_now()

    jy, jm, jd = gregorian_to_jalali(
        now.year,
        now.month,
        now.day
    )

    weekday = WEEKDAYS[now.weekday()]

    return weekday, jy, jm, jd


def get_today_key():
    """
    Unique daily key based on Iran date.
    """

    now = get_iran_now()

    return str(now.date())


# =========================================================
# DATABASE
# =========================================================

def get_connection():
    """
    Create SQLite connection.
    """

    conn = sqlite3.connect(
        DB,
        timeout=30
    )

    return conn


def init_db():
    conn = get_connection()
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

    cur.execute("""
        CREATE TABLE IF NOT EXISTS queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT,
            status TEXT DEFAULT 'pending',
            attempts INTEGER DEFAULT 0,
            last_error TEXT,
            locked INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS state (
            id INTEGER PRIMARY KEY,
            last_run TEXT
        )
    """)

    cur.execute("""
        INSERT OR IGNORE INTO state (id, last_run)
        VALUES (1, '')
    """)

    # اگر اجرای قبلی به هر دلیل وسط کار متوقف شده باشد،
    # آیتم‌های قفل‌شده دوباره قابل پردازش شوند.
    cur.execute("""
        UPDATE queue
        SET locked = 0
        WHERE status = 'pending'
    """)

    conn.commit()
    conn.close()


# =========================================================
# TELEGRAM
# =========================================================

def send_to_telegram(text):
    """
    Send message to Telegram with retry.
    """

    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/sendMessage"
    )

    last_error = None

    for attempt in range(MAX_RETRY):
        try:
            response = requests.post(
                url,
                json={
                    "chat_id": CHANNEL_ID,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True
                },
                timeout=20
            )

            try:
                data = response.json()
            except Exception:
                data = {}

            if (
                response.status_code == 200
                and data.get("ok") is True
            ):
                return True, None

            last_error = (
                data.get("description")
                or response.text[:500]
                or f"HTTP {response.status_code}"
            )

        except Exception as e:
            last_error = str(e)

        if attempt < MAX_RETRY - 1:
            time.sleep(2 ** attempt)

    return False, last_error


# =========================================================
# QUEUE
# =========================================================

def enqueue(message):
    """
    Add message to sending queue.
    """

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO queue (message)
        VALUES (?)
        """,
        (message,)
    )

    conn.commit()
    conn.close()


def process_queue():
    """
    Process pending Telegram messages.
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, message, attempts
        FROM queue
        WHERE status = 'pending'
          AND locked = 0
        ORDER BY id ASC
    """)

    rows = cur.fetchall()

    for qid, msg, attempts in rows:

        # Lock message
        cur.execute(
            """
            UPDATE queue
            SET locked = 1
            WHERE id = ?
            """,
            (qid,)
        )

        conn.commit()

        success, error = send_to_telegram(msg)

        if success:

            cur.execute(
                """
                UPDATE queue
                SET status = 'sent',
                    locked = 0,
                    last_error = NULL
                WHERE id = ?
                """,
                (qid,)
            )

        else:

            new_attempts = attempts + 1

            status = (
                "pending"
                if new_attempts < MAX_RETRY
                else "failed"
            )

            cur.execute(
                """
                UPDATE queue
                SET attempts = ?,
                    last_error = ?,
                    status = ?,
                    locked = 0
                WHERE id = ?
                """,
                (
                    new_attempts,
                    error,
                    status,
                    qid
                )
            )

        conn.commit()

        # فاصله بین ارسال‌ها
        time.sleep(1)

    conn.close()


# =========================================================
# LOAD HAFEZ DATA
# =========================================================

def load_faals():
    """
    Download Hafez data if database is empty.
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM faals"
    )

    count = cur.fetchone()[0]

    if count > 0:
        conn.close()
        return

    conn.close()

    try:
        response = requests.get(
            DATA_URL,
            timeout=60
        )

        response.raise_for_status()

        text = response.text

    except Exception as e:
        raise RuntimeError(
            f"خطا در دریافت دیتای فال حافظ: {e}"
        )

    # ساختار دیتای فعلی create_db.py
    pattern = (
        r"\(\s*(\d+)\s*,\s*"
        r"'([\s\S]*?)'\s*,\s*"
        r"'([\s\S]*?)'\s*\)"
    )

    rows = re.findall(
        pattern,
        text
    )

    if not rows:
        raise RuntimeError(
            "هیچ فال معتبری از فایل create_db.py استخراج نشد."
        )

    clean_rows = []

    for row in rows:

        fid = int(row[0])

        poem = (
            row[1]
            .replace("\\r\\n", "\n")
            .replace("\\n", "\n")
            .replace("\\r", "\n")
        )

        interp = (
            row[2]
            .replace("\\r\\n", "\n")
            .replace("\\n", "\n")
            .replace("\\r", "\n")
        )

        clean_rows.append(
            (
                fid,
                poem.strip(),
                interp.strip()
            )
        )

    conn = get_connection()

    conn.executemany(
        """
        INSERT OR REPLACE INTO faals
        (id, Poem, Interpretation)
        VALUES (?, ?, ?)
        """,
        clean_rows
    )

    conn.commit()
    conn.close()


# =========================================================
# FAL SELECTION
# =========================================================

def get_used(month, day):
    """
    Get Fal IDs already used for a specific month/date.
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT fal_id
        FROM sent
        WHERE month = ?
          AND day = ?
        """,
        (
            month,
            day
        )
    )

    used = [
        row[0]
        for row in cur.fetchall()
    ]

    conn.close()

    return used


def pick_fal(exclude):
    """
    Pick a random Fal while avoiding today's used Fals.
    """

    conn = get_connection()
    cur = conn.cursor()

    if exclude:

        placeholders = ",".join(
            "?" for _ in exclude
        )

        query = (
            "SELECT * FROM faals "
            f"WHERE id NOT IN ({placeholders})"
        )

        cur.execute(
            query,
            exclude
        )

    else:

        cur.execute(
            "SELECT * FROM faals"
        )

    rows = cur.fetchall()

    # اگر همه فال‌ها استفاده شده بودند،
    # دوباره از کل مجموعه انتخاب می‌کنیم.
    if not rows:

        cur.execute(
            "SELECT * FROM faals"
        )

        rows = cur.fetchall()

    conn.close()

    if not rows:
        raise RuntimeError(
            "هیچ فالی در دیتابیس وجود ندارد."
        )

    return random.choice(rows)


def save(month, fid, day):
    """
    Save today's selected Fal.
    """

    conn = get_connection()

    conn.execute(
        """
        INSERT OR IGNORE INTO sent
        (month, fal_id, day)
        VALUES (?, ?, ?)
        """,
        (
            month,
            fid,
            day
        )
    )

    conn.commit()
    conn.close()


# =========================================================
# POEM EXTRACTION
# =========================================================

def extract_bit(poem):
    """
    Pick a random couplet from the poem.

    Supports both \\n and \\r\\n.
    """

    if not poem:
        return ""

    # splitlines() هم \n و هم \r\n را پشتیبانی می‌کند.
    lines = [
        line.strip()
        for line in poem.splitlines()
        if line.strip()
    ]

    if not lines:
        return ""

    pairs = []

    for i in range(0, len(lines), 2):

        first = lines[i]

        second = (
            lines[i + 1]
            if i + 1 < len(lines)
            else ""
        )

        pairs.append(
            (
                first,
                second
            )
        )

    if not pairs:
        return ""

    first, second = random.choice(pairs)

    if second:
        return f"{first}\n{second}"

    return first


# =========================================================
# MESSAGE DESIGN
# =========================================================

def build(month, emoji, bit, interp):
    """
    Build beautiful Telegram message.
    """

    weekday, jy, jm, jd = get_today_jalali()

    date_day = to_persian_digits(jd)
    date_year = to_persian_digits(jy)

    jalali_month_name = MONTHS[jm][0]
    birth_month_name = MONTHS[month][0]

    date_text = (
        f"{weekday} "
        f"{date_day} "
        f"{jalali_month_name} "
        f"{date_year}"
    )

    return f"""📖 <b>فال حافظ امروز</b>

✨ <b>{date_text}</b>

━━━━━━━━━━━━━━━━━━

{emoji} <b>متولدین {birth_month_name}</b>

🌸🍃🌺🍃🌸🍃🌺

<blockquote>{bit}</blockquote>

💫 <b>تعبیر فال</b>

{interp}

🌺🍃🌸🍃🌺🍃🌸

━━━━━━━━━━━━━━━━━━

💖 <i>امیدوارم امروزت پر از اتفاق‌های خوب باشه...</i>

━━━━━━━━━━━━━━━━━━
<blockquote>@aristapanel</blockquote>

#فال_حافظ #فال_امروز #سرگرمی #آریستا
"""


# =========================================================
# DAILY LOCK
# =========================================================

def acquire_lock():
    """
    Ensure the bot runs only once per Iran calendar day.
    """

    conn = get_connection()
    cur = conn.cursor()

    today = get_today_key()

    cur.execute(
        """
        SELECT last_run
        FROM state
        WHERE id = 1
        """
    )

    row = cur.fetchone()

    last = row[0] if row else ""

    if last == today:
        conn.close()
        return False

    cur.execute(
        """
        UPDATE state
        SET last_run = ?
        WHERE id = 1
        """,
        (today,)
    )

    conn.commit()
    conn.close()

    return True


# =========================================================
# DAILY BATCH
# =========================================================

def enqueue_daily_batch():
    """
    Create 12 daily Fals.
    One Fal for each Persian month.
    """

    day = get_today_key()

    for month in range(1, 13):

        used = get_used(
            month,
            day
        )

        fid, poem, interp = pick_fal(
            used
        )

        bit = extract_bit(
            poem
        )

        text = build(
            month,
            MONTHS[month][1],
            bit,
            interp
        )

        enqueue(text)

        save(
            month,
            fid,
            day
        )


# =========================================================
# MAIN
# =========================================================

def run():

    print("🚀 Arista Hafez Bot started...")

    init_db()

    print("📚 Loading Hafez data...")

    load_faals()

    weekday, jy, jm, jd = get_today_jalali()

    print(
        "📅 Today:",
        weekday,
        jd,
        MONTHS[jm][0],
        jy
    )

    if not acquire_lock():

        print(
            "⏭️ Today's Fals have already been queued."
        )

        return

    print(
        "🌸 Creating 12 daily Fals..."
    )

    enqueue_daily_batch()

    print(
        "📤 Sending queued messages..."
    )

    process_queue()

    print(
        "✅ Done."
    )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    run()
