import os
import threading
import logging
import re
import time
import unicodedata
import asyncio
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer

import pandas as pd
from telegram import Update, ReplyKeyboardRemove
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
CONTEXT_SECONDS = 1800

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

cached_df = None
last_load_time = 0

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


def looks_like_sentence(user_text: str, df: pd.DataFrame) -> bool:
    """Recognize common requests without rejecting real multi-word names."""
    query = normalize_text(user_text).replace("’", "'")
    if not query:
        return False

    # Names such as "I Want Choo" and "Stronger With You" are valid.
    # Check each name field separately, not combined notes or descriptions.
    for column in ("perfume_name", "inspiration"):
        if column in df.columns:
            for value in df[column]:
                known_name = normalize_text(value).replace("’", "'")
                if known_name and query in known_name:
                    return False

    patterns = [
        r"^(?:please|hi|hello|hey)\b",
        r"^(?:can|could|would|will)\s+you\b",
        r"^(?:do|did|does)\s+(?:you|this|it)\b",
        r"^(?:i|we)\s+(?:want|need|would|am|are|like|have|love|prefer)\b",
        r"^(?:i'm|we're|i'd|we'd)\b",
        r"^(?:show|give|tell|find|recommend|suggest|send)\s+(?:me|us)\b",
        r"^(?:what|which|where|how|why|who|is there|are there)\b",
        r"^(?:looking|searching)\s+for\b",
        r"\b(?:please|do you have|can you|could you)\b",
        r"^(?:اريد|ابي|ابغى|ممكن|هل|عندكم|عندك|اعطني|بدي)(?:\s|$)",
    ]
    return any(re.search(pattern, query) for pattern in patterns)


async def send_name_only_instruction(message):
    await message.reply_text(
        "Please type <b>only our perfume name</b> or "
        "<b>the inspiration perfume name</b>, without a full sentence.\n\n"
        "Examples: <b>Palm Chill</b> or <b>Dior Sauvage</b>.",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove(),
    )


async def send_usage(message):
    await message.reply_text(
        "<b>Welcome to Mamlakat Product Bot ✦</b>\n"
        "Volaré / Mamlakat / Ard Al Khaleej / Sublime\n\n"
        "🔎 Type <b>Dior Sauvage</b>, for example, to find "
        "<b>our perfumes inspired by it</b>.\n\n"
        "🌸 Type <b>our perfume name</b>, such as "
        "<b>Palm Chill</b>, to view its details.\n\n"
        "Results include photos, fragrance notes, inspiration, "
        "gender, size and scent family.\n\n"
        "<b>Enter the perfume name only, without a full sentence.</b>",
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=ReplyKeyboardRemove(),
    )


def faq_text(value):
    """Normalize punctuation and accents for rule-based FAQ matching."""
    return re.sub(r"[^\w\s]", " ", normalize_text(value)).strip()


def tidy_phrase(value):
    value = re.sub(r"\s+", " ", faq_text(value))
    value = re.sub(r"\s+(?:please|from your collection|in your collection)$", "", value)
    return value.strip()


def faq_intent(text):
    q = tidy_phrase(text)
    if re.search(r"\b(?:payment|payments|pay|bank transfer|credit card|debit card|cards?|cash)\b", q):
        return "payment"
    if re.search(r"\b(?:in stock|stock|restock|available|availability|sold out|do you have (?:it|this|that))\b", q):
        return "stock"
    if re.search(r"\b(?:store|stores|showroom|showrooms|shop location|shops|try|test|sample in person|where are you located|where is your shop|where can i smell)\b", q):
        return "stores"
    if re.search(r"\b(?:order|ordering|buy|purchase|checkout|shop online|websites?|place an order)\b", q):
        return "order"
    if re.search(r"\b(?:scent famil(?:y|ies)|fragrance famil(?:y|ies)|olfactive famil(?:y|ies))\b", q):
        if re.search(r"\b(?:mean|means|meaning|explain|definition)\b", q):
            return "family_definition"
        if re.search(r"\b(?:of|for|this|that|its|it s)\b", q):
            return "family"
        return "family_definition"
    if (re.search(r"\b(?:gender|unisex|male|female|men or women|women or men|for men|for women|for a man|for a woman|for males|for females|for ladies|for gentlemen|for him or her)\b", q)
            or (re.search(r"\b(?:men|women|man|woman|ladies|gentlemen)\b", q)
                and re.search(r"\b(?:is|are|can|wear|suitable)\b", q))) and not re.search(r"\b(?:inspiration|inspired|similar|alternative|dupe)\b", q):
        return "gender"
    if re.search(r"\b(?:inspired by|inspired from|similar to|smells like|smell like|something like|anything like|perfume like|fragrance like|alternative to|dupe of|dupes of|equivalent to|version of)\s+(.+)", q):
        target = extract_inspiration_target(q)
        if target and not re.match(r"^(?:what|which|whom)\b", target):
            return "inspired_products"
    if re.search(r"\b(?:inspiration|inspo|inspired|based on|copy of)\b", q):
        if re.search(r"\b(?:do you have|show me|find|looking for)\b", q) and "inspiration behind" not in q:
            return "inspired_products"
        return "inspiration"
    return None


def extract_inspiration_target(text):
    q = tidy_phrase(text)
    match = re.search(r"\b(?:inspired by|inspired from|similar to|smells like|smell like|something like|anything like|perfume like|fragrance like|alternative to|dupe of|dupes of|equivalent to|version of)\s+(.+)$", q)
    if match:
        return tidy_phrase(match.group(1))
    match = re.search(r"\b(?:inspiration|inspired)\s+(?:perfumes?|fragrances?)\s+(?:for|of)\s+(.+)$", q)
    return tidy_phrase(match.group(1)) if match else ""


def unique_products(rows):
    seen, result = set(), []
    for row in rows:
        key = product_key(row)
        if key not in seen and safe_str(row.get("perfume_name", "")):
            seen.add(key)
            result.append(row)
    return result


def product_key(row):
    return tuple(normalize_text(row.get(c, "")) for c in ("brand", "perfume_name", "ml"))


def name_matches(phrase, value):
    query, name = tidy_phrase(phrase), tidy_phrase(value)
    if not query or not name:
        return False
    return f" {query} " in f" {name} "


def named_products(text, df):
    q = f" {tidy_phrase(text)} "
    candidates = []
    for _, row in df.iterrows():
        name = tidy_phrase(row.get("perfume_name", ""))
        if name and f" {name} " in q:
            candidates.append((len(name), row))
    if not candidates:
        return []
    longest = max(length for length, _ in candidates)
    rows = unique_products([row for length, row in candidates if length == longest])
    # A brand mentioned in the question can disambiguate duplicate names.
    branded = [row for row in rows if f" {tidy_phrase(row.get('brand', ''))} " in q]
    rows = branded or rows
    sized = [row for row in rows if safe_str(row.get("ml", "")) and
             name_matches(row.get("ml", ""), text)]
    return sized or rows


def exact_name_input(text, df):
    q = tidy_phrase(text)
    return any(
        q == tidy_phrase(row.get(column, ""))
        for _, row in df.iterrows()
        for column in ("perfume_name", "inspiration")
        if safe_str(row.get(column, ""))
    )


def session_state(update, context):
    # Keep each group participant's context separate, and expire old selections.
    user_id = update.effective_user.id if update.effective_user else 0
    sessions = context.chat_data.setdefault("product_sessions", {})
    now = time.time()
    for key in list(sessions):
        if now - sessions[key].get("updated_at", 0) > CONTEXT_SECONDS:
            del sessions[key]
    state = sessions.setdefault(user_id, {})
    state["updated_at"] = now
    return state


def remember_products(state, rows):
    state["last_products"] = [product_key(row) for row in unique_products(rows)]
    state.pop("pending_faq", None)


def previous_products(state, df):
    keys = set(state.get("last_products", []))
    return unique_products([row for _, row in df.iterrows() if product_key(row) in keys])


def is_followup(text):
    q = tidy_phrase(text)
    if re.search(r"\b(?:this|that|it|its|these|those|above|last|previous)\b", q):
        return True
    return q in {
        "gender", "gender please", "men or women", "male or female", "unisex",
        "is this unisex", "what is the inspiration", "what s the inspiration",
        "inspiration", "inspo", "scent family", "fragrance family",
    }


async def reply_faq(message, text):
    await message.reply_text(text, parse_mode="HTML", disable_web_page_preview=True,
                             reply_markup=ReplyKeyboardRemove())


async def static_faq(message, intent):
    answers = {
        "family_definition": (
            'A <b>scent family</b> describes a perfume’s overall smell, such as '
            '<b>floral, woody, citrus or gourmand</b>. '
            'Gourmand means sweet, dessert-like scents.'
        ),
        "stock": 'Please contact our sales team at <b>+971 56 508 7612</b> to confirm availability.',
        "order": (
            'You can order through our websites:\n\n'
            '<b>Volaré:</b> <a href="https://www.volareperfumes.com">www.volareperfumes.com</a>\n'
            '<b>Mamlakat, Ard Al Khaleej &amp; Sublime:</b> '
            '<a href="https://www.mamlakat.com">www.mamlakat.com</a>'
        ),
        "payment": 'We accept advance payment by <b>bank transfer or card</b>.',
        "stores": 'Find a store near you: <a href="https://www.mamlakat.com/pages/stores">View our stores</a>.',
    }
    if intent not in answers:
        return False
    await reply_faq(message, answers[intent])
    return True


async def answer_product_faq(message, intent, rows, state):
    rows = unique_products(rows)
    # Different sizes can share a single factual answer, if their data agree.
    column = {"inspiration": "inspiration", "gender": "gender", "family": "scent_family"}.get(intent)
    if len(rows) > 1 and column:
        identities = {(normalize_text(r.get("brand", "")), normalize_text(r.get("perfume_name", ""))) for r in rows}
        answers = {normalize_text(r.get(column, "")) for r in rows}
        if len(identities) == 1 and len(answers) == 1:
            rows = rows[:1]
    # Never guess which product "this perfume" means after several results.
    if len(rows) != 1:
        state["pending_faq"] = intent
        names = list(dict.fromkeys(safe_str(r.get("perfume_name", "")) for r in rows))
        text = 'Which perfume do you mean? Please type its <b>name</b>'
        if len(rows) > 1:
            text += ', <b>brand</b> and <b>size</b>'
        text += '.'
        if names:
            text += '\n\n' + '\n'.join(escape(n) for n in names[:MAX_RESULTS])
        await reply_faq(message, text)
        return
    row = rows[0]
    name = escape(safe_str(row.get("perfume_name", "")))
    if intent == "inspiration":
        value = safe_str(row.get("inspiration", ""))
        text = (f'<b>{name}</b> is inspired by <b>{escape(value)}</b>.' if value else
                f'The inspiration for <b>{name}</b> is not listed. Please contact <b>+971 56 508 7612</b>.')
    elif intent == "gender":
        value = safe_str(row.get("gender", ""))
        gender = normalize_text(value)
        descriptions = {
            "men": "for men", "man": "for men", "male": "for men",
            "women": "for women", "woman": "for women", "female": "for women",
            "unisex": "unisex — suitable for everyone",
        }
        description = descriptions.get(gender, value)
        text = (f'<b>{name}</b> is <b>{escape(description)}</b>.' if description else
                f'The gender category for <b>{name}</b> is not listed. Please contact <b>+971 56 508 7612</b>.')
    else:
        value = safe_str(row.get("scent_family", ""))
        text = (f'<b>{name}</b> belongs to the <b>{escape(value)}</b> scent family.' if value else
                f'The scent family for <b>{name}</b> is not listed.')
    await reply_faq(message, text)
    remember_products(state, rows)


async def send_product_results(message, rows, state):
    remember_products(state, rows)
    for row in rows:
        blocks = build_detail_blocks(row)
        caption = "\n".join(blocks)
        short_caption = len(caption) <= 1000
        sent_photo = False
        for photo_url in split_photo_urls(row.get("photo_url", ""))[:3]:
            try:
                await message.reply_photo(
                    photo=photo_url,
                    caption=caption if short_caption and not sent_photo else "",
                    parse_mode="HTML",
                )
                sent_photo = True
            except Exception:
                logger.warning("Could not send a product photo.", exc_info=True)
        if not sent_photo or not short_caption:
            await send_detail_text(message, blocks)


async def dynamic_faq(update, text, intent, df, state):
    message = update.message
    if intent == "inspired_products":
        target = extract_inspiration_target(text)
        if not target:
            state["pending_faq"] = intent
            await reply_faq(message, 'Please type the <b>inspiration perfume name</b>, such as <b>Dior Sauvage</b>.')
            return
        rows = unique_products([row for _, row in df.iterrows()
                                if name_matches(target, row.get("inspiration", ""))])[:MAX_RESULTS]
        if not rows:
            state.pop("pending_faq", None)
            await reply_faq(message, 'No matching inspired perfumes were found. Please check the inspiration name and try again.')
            return
        await reply_faq(message, f'Our perfumes inspired by <b>{escape(target)}</b>:')
        await send_product_results(message, rows, state)
        return
    rows = named_products(text, df)
    if not rows and is_followup(text):
        rows = previous_products(state, df)
    await answer_product_faq(message, intent, rows, state)

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.message:
        state = session_state(update, context)
        state.clear()
        state["updated_at"] = time.time()
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
    text = update.message.text.strip()
    state = session_state(update, context)
    intent = faq_intent(text)
    try:
        # General FAQs do not depend on the product sheet being online.
        if intent in {"family_definition", "stock", "order", "payment", "stores"}:
            if cached_df is None or not exact_name_input(text, cached_df):
                state.pop("pending_faq", None)
                await static_faq(update.message, intent)
                return

        df = await asyncio.to_thread(get_data)
        if exact_name_input(text, df):
            intent = None

        if intent in {"inspired_products", "inspiration", "gender", "family"}:
            await dynamic_faq(update, text, intent, df, state)
            return

        pending = state.get("pending_faq")
        if pending and not looks_like_sentence(text, df):
            if pending == "inspired_products":
                await dynamic_faq(update, "inspired by " + text, pending, df, state)
            else:
                rows = named_products(text, df)
                if not rows:
                    rows = unique_products([row for _, row in df.iterrows()
                                            if name_matches(text, row.get("perfume_name", ""))])
                await answer_product_faq(update.message, pending, rows, state)
            return

        if looks_like_sentence(text, df):
            await send_name_only_instruction(update.message)
            return

        rows = search_perfumes(text, df)
        if not rows:
            await reply_faq(
                update.message,
                '<b>No matches found.</b>\n\nPlease type only our perfume name or '
                'the inspiration perfume name. Examples: <b>Palm Chill</b> or <b>Dior Sauvage</b>.',
            )
            return
        await send_product_results(update.message, rows, state)
    except Exception:
        logger.exception("Error while handling product search or FAQ.")
        await update.message.reply_text(
            "There was an error loading or sending product details. Please try again.",
            reply_markup=ReplyKeyboardRemove(),
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
