  Using cached httpx-0.28.1-py3-none-any.whl.metadata (7.1 kB)
Collecting anyio (from httpx<0.29,>=0.27->python-telegram-bot==22.6->-r requirements.txt (line 1))
  Using cached anyio-4.12.1-py3-none-any.whl.metadata (4.3 kB)
Collecting certifi (from httpx<0.29,>=0.27->python-telegram-bot==22.6->-r requirements.txt (line 1))
  Using cached certifi-2026.2.25-py3-none-any.whl.metadata (2.5 kB)
Collecting httpcore==1.* (from httpx<0.29,>=0.27->python-telegram-bot==22.6->-r requirements.txt (line 1))
  Using cached httpcore-1.0.9-py3-none-any.whl.metadata (21 kB)
Collecting idna (from httpx<0.29,>=0.27->python-telegram-bot==22.6->-r requirements.txt (line 1))
  Using cached idna-3.11-py3-none-any.whl.metadata (8.4 kB)
Collecting h11>=0.16 (from httpcore==1.*->httpx<0.29,>=0.27->python-telegram-bot==22.6->-r requirements.txt (line 1))
  Using cached h11-0.16.0-py3-none-any.whl.metadata (8.3 kB)
Collecting python-dateutil>=2.8.2 (from pandas->-r requirements.txt (line 2))
  Using cached python_dateutil-2.9.0.post0-py2.py3-none-any.whl.metadata (8.4 kB)
Collecting six>=1.5 (from python-dateutil>=2.8.2->pandas->-r requirements.txt (line 2))
  Using cached six-1.17.0-py2.py3-none-any.whl.metadata (1.7 kB)
Using cached python_telegram_bot-22.6-py3-none-any.whl (737 kB)
Using cached httpx-0.28.1-py3-none-any.whl (73 kB)
Using cached httpcore-1.0.9-py3-none-any.whl (78 kB)
Using cached pandas-3.0.1-cp313-cp313-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl (10.9 MB)
Using cached numpy-2.4.3-cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl (16.6 MB)
Using cached h11-0.16.0-py3-none-any.whl (37 kB)
Using cached python_dateutil-2.9.0.post0-py2.py3-none-any.whl (229 kB)
Using cached six-1.17.0-py2.py3-none-any.whl (11 kB)
Using cached anyio-4.12.1-py3-none-any.whl (113 kB)
Using cached idna-3.11-py3-none-any.whl (71 kB)
Using cached certifi-2026.2.25-py3-none-any.whl (153 kB)
Installing collected packages: six, numpy, idna, h11, certifi, python-dateutil, httpcore, anyio, pandas, httpx, python-telegram-bot
Successfully installed anyio-4.12.1 certifi-2026.2.25 h11-0.16.0 httpcore-1.0.9 httpx-0.28.1 idna-3.11 numpy-2.4.3 pandas-3.0.1 python-dateutil-2.9.0.post0 python-telegram-bot-22.6 six-1.17.0
[notice] A new release of pip is available: 25.1.1 -> 26.0.1
[notice] To update, run: pip install --upgrade pip
==> Uploading build...
==> Uploaded in 12.8s. Compression took 5.5s
==> Build successful 🎉
==> Deploying...
==> Setting WEB_CONCURRENCY=1 by default, based on available CPUs in the instance
==> Running 'python bot.py'
2026-03-13 09:25:22,997 - __main__ - INFO - Health server running on port 10000
2026-03-13 09:25:24,093 - __main__ - INFO - Bot is running...
2026-03-13 09:25:24,796 - httpx - INFO - HTTP Request: POST https://api.telegram.org/bot8734784511:AAHuj0Ol2I-tHxYd1VmhyLeixHxj9G-q5Xk/getMe "HTTP/1.1 200 OK"
2026-03-13 09:25:24,962 - httpx - INFO - HTTP Request: POST https://api.telegram.org/bot8734784511:AAHuj0Ol2I-tHxYd1VmhyLeixHxj9G-q5Xk/deleteWebhook "HTTP/1.1 200 OK"
2026-03-13 09:25:24,963 - telegram.ext.Application - INFO - Application started
==> Your service is live 🎉
==> 
==> ///////////////////////////////////////////////////////////
==> 
==> Available at your primary URL https://telegram-perfume-bot-fegl.onrender.com
==> 
==> ///////////////////////////////////////////////////////////


is it working good

Yes — everything is working correctly ✅. Your logs show that the Telegram bot installed successfully, deployed, and started running.

Let me explain the key lines so you understand:
1️⃣ Packages installed successfully

Successfully installed ... python-telegram-bot ... pandas ...

This means your requirements.txt worked and all needed libraries were installed.
2️⃣ Your bot server started

Health server running on port 10000

This is Render’s health check server.
It means your bot container is alive and responding.
3️⃣ Telegram bot started correctly

Bot is running...
Application started

This confirms the Python bot code is running without errors.
4️⃣ Telegram connection succeeded

POST https://api.telegram.org/.../getMe "200 OK"

This means:

✔ Telegram recognized your bot token
✔ Your bot authenticated successfully
5️⃣ Render deployed successfully

Your service is live
https://telegram-perfume-bot-fegl.onrender.com

Your bot is now running 24/7 on Render.
🧪 Now Test It

Go to your Telegram group where the bot is added and type a perfume name.

Example:

bohemio

The bot should return:

    perfume photo

    smell notes

    gender

    product info

If you type something not in database:

abcd

Bot should reply:

Perfume not found

⚠️ One IMPORTANT security issue

Your bot token is visible in the logs:

bot8734784511:AAHuj0Ol2I...

Anyone could control your bot if they see this.

You should immediately regenerate it.

Steps:

    Open @BotFather in Telegram

    Type

/revoke

    Select your bot

    Generate new token

Then update it in your Render Environment Variables.
👍 Final status

Your Telegram perfume bot is:

✔ Installed
✔ Deployed
✔ Connected to Telegram
✔ Running 24/7

✅ Next, I can also help you upgrade it so your sales team can type:

bohemio

and it returns all Bohemio perfumes with photos automatically — much more powerful.

Just say “upgrade the bot” and I’ll give you the improved version.

import os
import threading
import logging
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

import pandas as pd
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

# =========================
# SETTINGS
# =========================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
SHEET_URL = os.environ.get("SHEET_URL", "").strip()

LOCAL_CSV_FILE = "products.csv"
MAX_RESULTS = 10

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# =========================
# LOAD DATA
# =========================
def load_data() -> pd.DataFrame:
    try:
        if SHEET_URL:
            df = pd.read_csv(SHEET_URL)
            logger.info("Loaded data from Google Sheet.")
        else:
            df = pd.read_csv(LOCAL_CSV_FILE)
            logger.info("Loaded data from local CSV.")

        df = df.fillna("")
        df.columns = [str(col).strip().lower() for col in df.columns]

        logger.info("CSV columns found: %s", list(df.columns))

        required_columns = ["brand", "perfume_name"]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")

        return df

    except Exception as e:
        logger.exception("Error loading data: %s", e)
        raise

# =========================
# HELPERS
# =========================
def safe_str(value) -> str:
    return str(value).strip() if value is not None else ""

def normalize_text(text: str) -> str:
    return safe_str(text).lower()

def convert_google_drive_url(url: str) -> str:
    """
    Convert Google Drive share/view links into direct-view links usable by Telegram.
    """
    url = safe_str(url)

    patterns = [
        r"drive\.google\.com/file/d/([^/]+)/",
        r"id=([^&]+)"
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            file_id = match.group(1)
            return f"https://drive.google.com/uc?export=view&id={file_id}"

    return url

def split_photo_urls(photo_value: str):
    raw = safe_str(photo_value)
    if not raw:
        return []

    for sep in ["|", ";"]:
        raw = raw.replace(sep, ",")

    urls = [x.strip() for x in raw.split(",") if x.strip()]
    return [convert_google_drive_url(x) for x in urls]

def build_caption(row) -> str:
    brand = safe_str(row.get("brand", ""))
    perfume_name = safe_str(row.get("perfume_name", ""))
    inspiration = safe_str(row.get("inspiration", ""))
    gender = safe_str(row.get("gender", ""))
    ml = safe_str(row.get("ml", ""))

    top = safe_str(row.get("top", ""))
    middle = safe_str(row.get("middle", ""))
    base = safe_str(row.get("base", ""))

    parts = []

    if brand:
        parts.append(f"Brand: {brand}")
    if perfume_name:
        parts.append(f"Perfume: {perfume_name}")
    if inspiration:
        parts.append(f"Inspiration: {inspiration}")
    if gender:
        parts.append(f"Gender: {gender}")
    if ml:
        parts.append(f"Size: {ml} ml")
    if top:
        parts.append(f"Top: {top}")
    if middle:
        parts.append(f"Middle: {middle}")
    if base:
        parts.append(f"Base: {base}")

    return "\n".join(parts)

def search_perfumes(user_text: str, df: pd.DataFrame):
    query = normalize_text(user_text)
    if not query:
        return []

    exact_matches = []
    partial_matches = []

    for _, row in df.iterrows():
        perfume_name = normalize_text(row.get("perfume_name", ""))
        brand = normalize_text(row.get("brand", ""))
        inspiration = normalize_text(row.get("inspiration", ""))
        top = normalize_text(row.get("top", ""))
        middle = normalize_text(row.get("middle", ""))
        base = normalize_text(row.get("base", ""))
        gender = normalize_text(row.get("gender", ""))
        ml = normalize_text(row.get("ml", ""))

        searchable_text = " ".join([
            perfume_name,
            brand,
            inspiration,
            top,
            middle,
            base,
            gender,
            ml
        ]).strip()

        if query == perfume_name:
            exact_matches.append(row)
            continue

        if query in searchable_text:
            partial_matches.append(row)

    if exact_matches:
        return exact_matches[:MAX_RESULTS]

    seen = set()
    unique_rows = []

    for row in partial_matches:
        perfume_name = normalize_text(row.get("perfume_name", ""))
        if perfume_name not in seen:
            seen.add(perfume_name)
            unique_rows.append(row)

    return unique_rows[:MAX_RESULTS]

# =========================
# TELEGRAM HANDLERS
# =========================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to Mamlakat Product Bot.\n"
        "Type any perfume name to search.\n\n"
        "Example:\n"
        "Bohemio\n"
        "or\n"
        "Bohemio Cherry Rosé Elixir"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_text = update.message.text.strip()
    logger.info("Received message: %s", user_text)

    try:
        df = load_data()
        results = search_perfumes(user_text, df)

        if not results:
            await update.message.reply_text("Product not found.")
            return

        for row in results:
            caption = build_caption(row)
            photo_urls = split_photo_urls(row.get("photo_url", ""))

            sent_photo = False
            for photo_url in photo_urls[:3]:
                try:
                    await update.message.reply_photo(
                        photo=photo_url,
                        caption=caption if not sent_photo else ""
                    )
                    sent_photo = True
                except Exception as e:
                    logger.warning("Failed to send photo %s: %s", photo_url, e)

            if not sent_photo:
                await update.message.reply_text(caption)

    except Exception as e:
        logger.exception("Error while handling message: %s", e)
        await update.message.reply_text("There was an error reading the product database.")

# =========================
# HEALTH CHECK SERVER
# =========================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running")

    def log_message(self, format, *args):
        return

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    logger.info("Health server running on port %s", port)
    server.serve_forever()

# =========================
# MAIN
# =========================
def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is missing. Add it in Render environment variables.")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    main()


is it ok

Yes — this is mostly good and should work. Your bot structure is clean, and it does the main things correctly:

    loads CSV / Google Sheet

    searches perfumes

    sends up to 3 photos

    sends caption

    has health check for Render

    runs polling correctly

But there are a few important improvements I strongly recommend before you rely on it.
What is good

Your code already has:

    proper async Telegram handlers

    fallback to local CSV if sheet URL is missing

    lowercase column cleanup

    exact match first, then partial match

    duplicate removal for partial results

    health server for Render

    logging

So overall: yes, it is okay.
Important issues to fix
1. load_data() runs on every single message

Right now, every time someone types anything, the bot re-reads the CSV / Google Sheet:

df = load_data()

inside handle_message.

That works, but it is slow and can become annoying if many people use it.
Better options:

    load once at startup, or

    cache it and refresh every few minutes

For now, the simplest improvement is to keep a global dataframe.
2. Search may match too many unrelated products

You search inside this full text:

searchable_text = " ".join([
    perfume_name, brand, inspiration, top, middle, base, gender, ml
])

So if someone types:

men

it may return many products just because gender = men.

If your goal is:

    typing bohemio → all bohemio products

    typing exact full name → only that product

then it is better to prioritize:

    exact perfume name

    perfume name contains query

    brand contains query

and only optionally search other fields later.
3. Caption repeats for every photo attempt

You do this:

await update.message.reply_photo(
    photo=photo_url,
    caption=caption if not sent_photo else ""
)

That part is actually fine.
But if the first photo fails and second succeeds, the caption still goes on second one, which is okay. No issue there.
4. Google Drive links may still fail

This function:

return f"https://drive.google.com/uc?export=view&id={file_id}"

works for some files, but Telegram may still fail if:

    file is not public

    too large

    Drive blocks direct serving

    permission is folder-only, not file-public

So if photos fail sometimes, the code is not necessarily wrong — the Drive sharing settings may be the real issue.

Each image should be:

    shared as Anyone with the link

    ideally a direct file link, not folder link

5. No handling for empty / bad sheet data

If SHEET_URL points to a normal Google Sheet page instead of a CSV export link, this will fail:

pd.read_csv(SHEET_URL)

So make sure SHEET_URL is a real CSV export URL, not the normal sheet URL.

Example format:

https://docs.google.com/spreadsheets/d/.../export?format=csv&gid=0

6. Token safety

Earlier, your bot token appeared in logs. That is dangerous.
If that token is still the same, regenerate it in BotFather and update Render.
Best improved version

Here is the cleaner version of the search logic I recommend conceptually:

    exact full perfume name → return only that

    partial match in perfume name → return matching perfumes

    partial match in brand → return matching perfumes

    otherwise not found

That will behave more like what you want for salespeople.

For example:

    bohemio → all Bohemio perfumes

    bohemio cherry rosé elixir → only that item

    random word from base note → not necessarily match everything

Small code improvements
Improve normalize_text

You can make it slightly better by removing extra spaces:

def normalize_text(text: str) -> str:
    return " ".join(safe_str(text).lower().split())

This helps if users type extra spaces.
Better search function

This version is better for your use case:

def search_perfumes(user_text: str, df: pd.DataFrame):
    query = normalize_text(user_text)
    if not query:
        return []

    exact_matches = []
    name_matches = []
    brand_matches = []

    for _, row in df.iterrows():
        perfume_name = normalize_text(row.get("perfume_name", ""))
        brand = normalize_text(row.get("brand", ""))

        if query == perfume_name:
            exact_matches.append(row)
            continue

        if query in perfume_name:
            name_matches.append(row)
            continue

        if query in brand:
            brand_matches.append(row)

    if exact_matches:
        return exact_matches[:MAX_RESULTS]

    combined = name_matches + brand_matches

    seen = set()
    unique_rows = []
    for row in combined:
        perfume_name = normalize_text(row.get("perfume_name", ""))
        if perfume_name not in seen:
            seen.add(perfume_name)
            unique_rows.append(row)

    return unique_rows[:MAX_RESULTS]

This is better aligned with your bot goal.
Cache dataframe once

At top level:

PRODUCTS_DF = None

Then in main():

global PRODUCTS_DF
PRODUCTS_DF = load_data()

Then in handler:

results = search_perfumes(user_text, PRODUCTS_DF)

That makes it faster.
Final judgment

So the answer is:

Yes, the code is okay and should run.
But for your real use case, I recommend 3 important upgrades:

    load the data once instead of every message

    search mainly by perfume name / brand

    make sure Google Drive image links are public direct links

Overall score:

8/10
Good working version, but not the best optimized version yet.

Paste your products.csv column names or one sample row, and I’ll rewrite the final best bot.py for your exact database.

give me full python to update

Paste this as your full updated bot.py:

import os
import threading
import logging
import re
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import pandas as pd
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

# =========================
# SETTINGS
# =========================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
SHEET_URL = os.environ.get("SHEET_URL", "").strip()

LOCAL_CSV_FILE = "products.csv"
MAX_RESULTS = 10
CACHE_TTL_SECONDS = 300  # reload data every 5 minutes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# =========================
# GLOBAL CACHE
# =========================
PRODUCTS_DF = None
LAST_LOAD_TIME = 0


# =========================
# HELPERS
# =========================
def safe_str(value) -> str:
    return str(value).strip() if value is not None else ""


def normalize_text(text: str) -> str:
    return " ".join(safe_str(text).lower().split())


def convert_google_drive_url(url: str) -> str:
    """
    Convert Google Drive links to direct image links usable by Telegram.
    Supports:
    - https://drive.google.com/file/d/FILE_ID/view?...
    - https://drive.google.com/open?id=FILE_ID
    - https://drive.google.com/uc?id=FILE_ID
    """
    url = safe_str(url)
    if not url:
        return ""

    patterns = [
        r"drive\.google\.com/file/d/([^/]+)",
        r"[?&]id=([^&]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            file_id = match.group(1)
            return f"https://drive.google.com/uc?export=view&id={file_id}"

    return url


def split_photo_urls(photo_value: str):
    raw = safe_str(photo_value)
    if not raw:
        return []

    for sep in ["|", ";", "\n"]:
        raw = raw.replace(sep, ",")

    urls = [x.strip() for x in raw.split(",") if x.strip()]
    cleaned_urls = []

    for url in urls:
        converted = convert_google_drive_url(url)
        if converted:
            cleaned_urls.append(converted)

    return cleaned_urls[:3]


def build_caption(row) -> str:
    brand = safe_str(row.get("brand", ""))
    perfume_name = safe_str(row.get("perfume_name", ""))
    inspiration = safe_str(row.get("inspiration", ""))
    gender = safe_str(row.get("gender", ""))
    ml = safe_str(row.get("ml", ""))

    top = safe_str(row.get("top", ""))
    middle = safe_str(row.get("middle", ""))
    base = safe_str(row.get("base", ""))

    parts = []

    if brand:
        parts.append(f"Brand: {brand}")
    if perfume_name:
        parts.append(f"Perfume: {perfume_name}")
    if inspiration:
        parts.append(f"Inspiration: {inspiration}")
    if gender:
        parts.append(f"Gender: {gender}")
    if ml:
        parts.append(f"Size: {ml} ml")
    if top:
        parts.append(f"Top: {top}")
    if middle:
        parts.append(f"Middle: {middle}")
    if base:
        parts.append(f"Base: {base}")

    return "\n".join(parts)


# =========================
# LOAD DATA
# =========================
def load_data() -> pd.DataFrame:
    try:
        if SHEET_URL:
            df = pd.read_csv(SHEET_URL)
            logger.info("Loaded data from Google Sheet.")
        else:
            df = pd.read_csv(LOCAL_CSV_FILE)
            logger.info("Loaded data from local CSV.")

        df = df.fillna("")
        df.columns = [str(col).strip().lower() for col in df.columns]

        logger.info("CSV columns found: %s", list(df.columns))

        required_columns = ["brand", "perfume_name"]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")

        return df

    except Exception as e:
        logger.exception("Error loading data: %s", e)
        raise


def get_data() -> pd.DataFrame:
    global PRODUCTS_DF, LAST_LOAD_TIME

    now = time.time()

    if PRODUCTS_DF is None or (now - LAST_LOAD_TIME > CACHE_TTL_SECONDS):
        PRODUCTS_DF = load_data()
        LAST_LOAD_TIME = now
        logger.info("Product data cache refreshed.")

    return PRODUCTS_DF


# =========================
# SEARCH
# =========================
def search_perfumes(user_text: str, df: pd.DataFrame):
    query = normalize_text(user_text)
    if not query:
        return []

    exact_matches = []
    name_startswith_matches = []
    name_contains_matches = []
    brand_matches = []

    for _, row in df.iterrows():
        perfume_name = normalize_text(row.get("perfume_name", ""))
        brand = normalize_text(row.get("brand", ""))

        if not perfume_name:
            continue

        # Exact full perfume name match -> highest priority
        if query == perfume_name:
            exact_matches.append(row)
            continue

        # If query is at start of perfume name
        if perfume_name.startswith(query):
            name_startswith_matches.append(row)
            continue

        # If query appears anywhere in perfume name
        if query in perfume_name:
            name_contains_matches.append(row)
            continue

        # If query appears in brand name
        if query in brand:
            brand_matches.append(row)

    if exact_matches:
        return exact_matches[:MAX_RESULTS]

    combined = name_startswith_matches + name_contains_matches + brand_matches

    seen = set()
    unique_rows = []

    for row in combined:
        perfume_name = normalize_text(row.get("perfume_name", ""))
        if perfume_name not in seen:
            seen.add(perfume_name)
            unique_rows.append(row)

    return unique_rows[:MAX_RESULTS]


# =========================
# TELEGRAM HANDLERS
# =========================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    await update.message.reply_text(
        "Welcome to Mamlakat Product Bot.\n"
        "Type any perfume name to search.\n\n"
        "Examples:\n"
        "Bohemio\n"
        "Bohemio Cherry Rosé Elixir"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_text = update.message.text.strip()
    logger.info("Received message: %s", user_text)

    try:
        df = get_data()
        results = search_perfumes(user_text, df)

        if not results:
            await update.message.reply_text("Product not found.")
            return

        for row in results:
            caption = build_caption(row)
            photo_urls = split_photo_urls(row.get("photo_url", ""))

            sent_photo = False

            for photo_url in photo_urls:
                try:
                    await update.message.reply_photo(
                        photo=photo_url,
                        caption=caption if not sent_photo else ""
                    )
                    sent_photo = True
                except Exception as e:
                    logger.warning("Failed to send photo %s: %s", photo_url, e)

            if not sent_photo:
                await update.message.reply_text(caption)

    except Exception as e:
        logger.exception("Error while handling message: %s", e)
        await update.message.reply_text("There was an error reading the product database.")


# =========================
# OPTIONAL COMMAND TO REFRESH DATA
# =========================
async def reload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global PRODUCTS_DF, LAST_LOAD_TIME

    try:
        PRODUCTS_DF = load_data()
        LAST_LOAD_TIME = time.time()

        if update.message:
            await update.message.reply_text("Product database reloaded successfully.")

    except Exception as e:
        logger.exception("Reload failed: %s", e)
        if update.message:
            await update.message.reply_text("Failed to reload product database.")


# =========================
# HEALTH CHECK SERVER
# =========================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running")

    def log_message(self, format, *args):
        return


def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    logger.info("Health server running on port %s", port)
    server.serve_forever()


# =========================
# MAIN
# =========================
def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is missing. Add it in Render environment variables.")

    # Load once at startup
    get_data()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("reload", reload_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    main()

What changed

This version is better because it:

    loads the CSV once and caches it

    refreshes automatically every 5 minutes

    prioritizes exact perfume name matches

    matches collection names like bohemio better

    keeps /reload command if you update the sheet manually

    supports up to 3 photos

    still works on Render

After pasting

Do this:

    Replace your old bot.py with this code

    Save

    Push / redeploy on Render

    Test in Telegram:

        bohemio

        full exact perfume name

        random wrong name

Important

Your products.csv should include at least these columns:

brand, perfume_name, photo_url, inspiration, gender, ml, top, middle, base

And your Google Drive image links must be public.

Paste your products.csv headers next and I’ll check if they exactly match this code.


