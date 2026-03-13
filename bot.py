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

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
SHEET_URL = os.environ.get("SHEET_URL", "").strip()

LOCAL_CSV_FILE = "products.csv"
MAX_RESULTS = 10
CACHE_SECONDS = 60

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

cached_df = None
last_load_time = 0


def load_data_from_source() -> pd.DataFrame:
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


def get_data() -> pd.DataFrame:
    global cached_df, last_load_time

    now = time.time()

    if cached_df is None or (now - last_load_time) > CACHE_SECONDS:
        try:
            cached_df = load_data_from_source()
            last_load_time = now
            logger.info("Data cache refreshed.")
        except Exception as e:
            logger.exception("Failed to refresh data: %s", e)
            if cached_df is None:
                raise

    return cached_df


def safe_str(value) -> str:
    return str(value).strip() if value is not None else ""


def normalize_text(text: str) -> str:
    return safe_str(text).lower()


def convert_google_drive_url(url: str) -> str:
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
        parts.append(f"Size: {ml}")
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


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to Mamlakat Product Bot.\n"
        "Type any perfume name to search.\n\n"
        "Example:\n"
        "Palm Chill\n"
        "or\n"
        "Amber Sands Prestige"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_text = update.message.text.strip()
    logger.info("Received message: %s", user_text)

    try:
        df = get_data()
        results = search_perfumes(user_text, df)
        logger.info("Found %s results", len(results))

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


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

    def log_message(self, format, *args):
        return


def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    logger.info("Health server running on port %s", port)
    server.serve_forever()


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is missing. Add it in Render environment variables.")

    get_data()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    main()
