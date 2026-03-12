import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pandas as pd
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

# =========================
# SETTINGS
# =========================
BOT_TOKEN = os.environ.get("8734784511:AAGdQVoyjnu3WdqoQ2F5GbVIsRSPyuIOvEc", "").strip()

# Put your published Google Sheet CSV link in Render env variable:
# SHEET_URL = https://docs.google.com/spreadsheets/d/XXXXX/export?format=csv
SHEET_URL = os.environ.get("https://docs.google.com/spreadsheets/d/e/2PACX-1vRPB1vYtc3E1FXutjbrEt3IDDe_RjWrBHN7All7-DglF2YHsNmkWE2UDXV-oV6JW-y_gK-I3DaS30X1/pub?output=csv", "").strip()

# Optional fallback for local testing
LOCAL_CSV_FILE = "products.csv"

# Max number of matching products to send
MAX_RESULTS = 10


# =========================
# LOAD DATA
# =========================
def load_data() -> pd.DataFrame:
    """
    Load perfume data from Google Sheet CSV URL.
    Falls back to local CSV file if SHEET_URL is missing.
    """
    try:
        if SHEET_URL:
            df = pd.read_csv(SHEET_URL)
            print("Loaded data from Google Sheet.")
        else:
            df = pd.read_csv(LOCAL_CSV_FILE)
            print("Loaded data from local CSV.")

        df = df.fillna("")

        # Normalize column names
        df.columns = [str(col).strip().lower() for col in df.columns]

        print("CSV columns found:", list(df.columns))

        required_columns = ["brand", "perfume_name"]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")

        return df

    except Exception as e:
        print("Error loading data:", e)
        raise


df = load_data()


# =========================
# HELPERS
# =========================
def safe_str(value) -> str:
    return str(value).strip() if value is not None else ""


def normalize_text(text: str) -> str:
    return safe_str(text).lower()


def split_photo_urls(photo_value: str):
    """
    Supports one or multiple image URLs.
    You can separate multiple URLs in the sheet by:
    comma ,
    or pipe |
    or semicolon ;
    """
    raw = safe_str(photo_value)
    if not raw:
        return []

    for sep in ["|", ";"]:
        raw = raw.replace(sep, ",")

    urls = [x.strip() for x in raw.split(",") if x.strip()]
    return urls


def build_caption(row) -> str:
    brand = safe_str(row.get("brand", ""))
    perfume_name = safe_str(row.get("perfume_name", ""))
    gender = safe_str(row.get("gender", ""))
    smell_note = safe_str(row.get("smell_note", ""))
    keywords = safe_str(row.get("keywords", ""))

    parts = []

    if brand:
        parts.append(f"Brand: {brand}")
    if perfume_name:
        parts.append(f"Perfume: {perfume_name}")
    if gender:
        parts.append(f"Gender: {gender}")
    if smell_note:
        parts.append(f"Notes: {smell_note}")
    if keywords:
        parts.append(f"Keywords: {keywords}")

    return "\n".join(parts)


def row_exact_score(query: str, row) -> int:
    """
    Higher score = better match
    """
    perfume_name = normalize_text(row.get("perfume_name", ""))
    brand = normalize_text(row.get("brand", ""))
    keywords = normalize_text(row.get("keywords", ""))

    score = 0

    # Exact perfume name
    if query == perfume_name:
        score += 100

    # Exact brand
    if query == brand:
        score += 60

    # Exact keyword token
    keyword_list = [k.strip() for k in keywords.replace(";", ",").replace("|", ",").split(",")]
    if query in keyword_list:
        score += 50

    # Startswith
    if perfume_name.startswith(query):
        score += 35
    if brand.startswith(query):
        score += 20

    # Contains
    if query in perfume_name:
        score += 25
    if query in brand:
        score += 10
    if query in keywords:
        score += 15

    return score


def search_perfumes(user_text: str):
    query = normalize_text(user_text)
    if not query:
        return []

    matches = []

    for _, row in df.iterrows():
        perfume_name = normalize_text(row.get("perfume_name", ""))
        brand = normalize_text(row.get("brand", ""))
        keywords = normalize_text(row.get("keywords", ""))
        smell_note = normalize_text(row.get("smell_note", ""))
        gender = normalize_text(row.get("gender", ""))

        searchable_text = " ".join([perfume_name, brand, keywords, smell_note, gender]).strip()

        if query in searchable_text:
            score = row_exact_score(query, row)
            matches.append((score, row))

    # Sort best matches first
    matches.sort(key=lambda x: x[0], reverse=True)

    # Remove duplicates by perfume_name
    seen = set()
    unique_rows = []

    for score, row in matches:
        perfume_name = normalize_text(row.get("perfume_name", ""))
        if perfume_name not in seen:
            seen.add(perfume_name)
            unique_rows.append(row)

    return unique_rows[:MAX_RESULTS]


# =========================
# TELEGRAM HANDLER
# =========================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_text = update.message.text.strip()
    results = search_perfumes(user_text)

    if not results:
        await update.message.reply_text("Not found")
        return

    for row in results:
        caption = build_caption(row)
        photo_urls = split_photo_urls(row.get("photo_url", ""))

        # Send up to 3 photos if available
        sent_photo = False
        for photo_url in photo_urls[:3]:
            try:
                await update.message.reply_photo(photo=photo_url, caption=caption if not sent_photo else "")
                sent_photo = True
            except Exception as e:
                print(f"Failed to send photo {photo_url}: {e}")

        if not sent_photo:
            await update.message.reply_text(caption)


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
    print(f"Health server running on port {port}")
    server.serve_forever()


# =========================
# MAIN
# =========================
def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is missing. Add it in Render environment variables.")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    main()
