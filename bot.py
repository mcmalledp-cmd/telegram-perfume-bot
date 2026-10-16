import os
import threading
import logging
import re
import time
import unicodedata
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer

import pandas as pd
from telegram import Update, ReplyKeyboardMarkup
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

HELP_BUTTON = "❓ How to use"


def search_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["Dior Sauvage", "Palm Chill"],
            ["Floral", "Woody", "Gourmand"],
            [HELP_BUTTON],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Type a perfume, note or scent family",
    )


def safe_str(value) -> str:
    return str(value).strip() if value is not None else ""


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", safe_str(text))

    text = "".join(
        character
        for character in text
        if not unicodedata.combining(character)
    )

    return re.sub(r"\s+", " ", text).strip().lower()


def load_data_from_source() -> pd.DataFrame:
    source = SHEET_URL if SHEET_URL else LOCAL_CSV_FILE

    df = pd.read_csv(source, dtype=str)
    df = df.fillna("")

    df.columns = [
        re.sub(r"\s+", "_", str(column).strip().lower())
        for column in df.columns
    ]

    for column in ["brand", "perfume_name"]:
        if column not in df.columns:
            raise ValueError(
                f"Missing required column: {column}"
            )

    logger.info("Loaded %s product rows.", len(df))

    return df


def get_data() -> pd.DataFrame:
    global cached_df, last_load_time

    now = time.time()

    if cached_df is None or now - last_load_time > CACHE_SECONDS:
        try:
            cached_df = load_data_from_source()
            last_load_time = now
            logger.info("Product cache refreshed.")

        except Exception:
            logger.exception("Failed to refresh product data.")

            if cached_df is None:
                raise

    return cached_df


def brand_links(brand: str):
    brand = normalize_text(brand)

    if "volare" in brand:
        return {
            "website_url": "https://www.volareperfumes.com",
            "website_label": "www.volareperfumes.com",
            "instagram_url": "https://www.instagram.com/volare.perfumes",
            "instagram_label": "@volare.perfumes",
        }

    if any(
        name in brand
        for name in (
            "mamlakat",
            "ard al khaleej",
            "sublime",
        )
    ):
        return {
            "website_url": "https://www.mamlakat.com",
            "website_label": "www.mamlakat.com",
            "instagram_url": "https://www.instagram.com/mamlakatofficial/",
            "instagram_label": "@mamlakatofficial",
        }

    return None


def convert_google_drive_url(url: str) -> str:
    url = safe_str(url)

    patterns = [
        r"drive\.google\.com/file/d/([^/]+)/",
        r"drive\.google\.com/.*[?&]id=([^&]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)

        if match:
            file_id = match.group(1)

            return (
                "https://drive.google.com/uc"
                f"?export=view&id={file_id}"
            )

    return url


def split_photo_urls(photo_value: str):
    raw = safe_str(photo_value)

    if not raw:
        return []

    for separator in ["|", ";"]:
        raw = raw.replace(separator, ",")

    return [
        convert_google_drive_url(url.strip())
        for url in raw.split(",")
        if url.strip()
    ]


def build_detail_blocks(row):
    fields = [
        ("Brand", "brand"),
        ("Perfume", "perfume_name"),
        ("Inspiration", "inspiration"),
        ("Gender", "gender"),
        ("Size", "ml"),
        ("Top", "top"),
        ("Middle", "middle"),
        ("Base", "base"),
        ("Scent Family", "scent_family"),
    ]

    blocks = []

    for label, column in fields:
        value = safe_str(row.get(column, "")) or "Not provided"

        for offset in range(0, len(value), 500):
            heading = (
                label
                if offset == 0
                else f"{label} (continued)"
            )

            text = escape(value[offset:offset + 500])

            blocks.append(f"<b>{heading}:</b> {text}")

    links = brand_links(row.get("brand", ""))

    if links:
        blocks.append(
            f'<b>Website:</b> '
            f'<a href="{links["website_url"]}">'
            f'{links["website_label"]}</a>'
        )

        blocks.append(
            f'📸 <b>Instagram:</b> '
            f'<a href="{links["instagram_url"]}">'
            f'{links["instagram_label"]}</a>'
        )

    return blocks


def build_caption(row) -> str:
    return "\n".join(build_detail_blocks(row))


async def send_detail_text(message, blocks):
    chunk = ""

    for block in blocks:
        candidate = f"{chunk}\n{block}" if chunk else block

        if len(candidate) > 3900 and chunk:
            await message.reply_text(
                chunk,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            chunk = block
        else:
            chunk = candidate

    if chunk:
        await message.reply_text(
            chunk,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )


def search_perfumes(user_text: str, df: pd.DataFrame):
    query = normalize_text(user_text)

    if not query:
        return []

    exact_matches = []
    partial_matches = []

    searchable_columns = [
        "perfume_name",
        "brand",
        "inspiration",
        "top",
        "middle",
        "base",
        "gender",
        "ml",
        "scent_family",
    ]

    for _, row in df.iterrows():
        perfume_name = normalize_text(
            row.get("perfume_name", "")
        )

        if not perfume_name:
            continue

        searchable_text = " ".join(
            normalize_text(row.get(column, ""))
            for column in searchable_columns
        )

        if query == perfume_name:
            exact_matches.append(row)
        elif query in searchable_text:
            partial_matches.append(row)

    if exact_matches:
        return exact_matches[:MAX_RESULTS]

    seen = set()
    unique_rows = []

    for row in partial_matches:
        key = (
            normalize_text(row.get("brand", "")),
            normalize_text(row.get("perfume_name", "")),
            normalize_text(row.get("ml", "")),
        )

        if key not in seen:
            seen.add(key)
            unique_rows.append(row)

    return unique_rows[:MAX_RESULTS]


async def send_usage(message):
    await message.reply_text(
        "<b>Welcome to Mamlakat Product Bot ✦</b>\n"
        "Volaré / Mamlakat / Ard Al Khaleej / Sublime\n\n"

        "🔎 <b>Search an inspiration perfume</b>\n"
        "Type <b>Dior Sauvage</b>, for example, "
        "to find our perfumes inspired by it.\n\n"

        "🌸 <b>Search our perfume</b>\n"
        "Type <b>Palm Chill</b>, for example, "
        "to see its photo, gender, size (ml), inspiration, "
        "fragrance notes and scent family.\n\n"

        "✨ <b>Explore scents</b>\n"
        "Try <b>Floral</b>, <b>Woody</b> or "
        "<b>Gourmand</b> (sweet, dessert-like scents). "
        "You can also search a note such as <b>vanilla</b>.\n\n"

        "<b>Type a name or tap an example below to start.</b>\n"
        "Use short search terms, such as "
        "<b>Dior Sauvage</b>, rather than a full sentence.\n\n"

        "Up to 10 matching products per search.\n"
        "Send /help whenever you need this guide.",

        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=search_keyboard(),
    )


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.message:
        await send_usage(update.message)


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.message:
        await send_usage(update.message)


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message or not update.message.text:
        return

    user_text = update.message.text.strip()

    if user_text == HELP_BUTTON:
        await send_usage(update.message)
        return

    try:
        df = get_data()
        results = search_perfumes(user_text, df)

        if not results:
            await update.message.reply_text(
                "<b>No matches found.</b>\n\n"
                "Try a shorter perfume name, an inspiration name, "
                "a note such as <b>vanilla</b>, or a scent family "
                "such as <b>Floral</b>.\n\n"
                "You can also tap an example below or send /help.",

                parse_mode="HTML",
                reply_markup=search_keyboard(),
            )
            return

        for row in results:
            blocks = build_detail_blocks(row)
            caption = "\n".join(blocks)

            photo_urls = split_photo_urls(
                row.get("photo_url", "")
            )

            short_caption = len(caption) <= 1000
            sent_photo = False

            for photo_url in photo_urls[:3]:
                try:
                    await update.message.reply_photo(
                        photo=photo_url,
                        caption=(
                            caption
                            if short_caption and not sent_photo
                            else ""
                        ),
                        parse_mode="HTML",
                    )
                    sent_photo = True

                except Exception:
                    logger.warning(
                        "Could not send a product photo.",
                        exc_info=True,
                    )

            if not sent_photo or not short_caption:
                await send_detail_text(
                    update.message,
                    blocks,
                )

    except Exception:
        logger.exception("Error while handling product search.")

        await update.message.reply_text(
            "There was an error loading or sending product details. "
            "Please try again.",
            reply_markup=search_keyboard(),
        )


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

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthHandler,
    )

    logger.info("Health server running on port %s", port)
    server.serve_forever()


def main():
    if not BOT_TOKEN:
        raise ValueError(
            "BOT_TOKEN is missing. "
            "Add it in Render environment variables."
        )

    get_data()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message,
        )
    )

    logger.info("Bot is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    threading.Thread(
        target=run_web_server,
        daemon=True,
    ).start()

    main()
