import csv
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters

TOKEN = "8734784511:AAGdQVoyjnu3WdqoQ2F5GbVIsRSPyuIOvEc"
CSV_FILE = "products.csv"


def load_products():
    products = []
    with open(CSV_FILE, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        print("CSV columns found:", reader.fieldnames)
        for row in reader:
            products.append(row)
    return products


PRODUCTS = load_products()


def clean(text):
    return str(text).strip().lower()


def build_caption(product):
    return (
        f"{product.get('perfume_name', '')}\n"
        f"Brand: {product.get('brand', '')}\n\n"
        f"{product.get('smell_note', '')}"
    )


def find_exact_match(query):
    query = clean(query)
    for product in PRODUCTS:
        if clean(product.get("perfume_name", "")) == query:
            return product
    return None


def find_partial_matches(query):
    query = clean(query)
    matches = []

    for product in PRODUCTS:
        perfume_name = clean(product.get("perfume_name", ""))
        keywords = clean(product.get("keywords", ""))

        if query in perfume_name or query in keywords:
            matches.append(product)

    return matches


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Type perfume name only.\n\n"
        "Example:\n"
        "bohemio\n"
        "or\n"
        "BOHEMIO CHERRY ROSÉ ELIXIR"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if not text:
        return

    # 1) exact full perfume name
    exact_product = find_exact_match(text)
    if exact_product:
        await update.message.reply_photo(
            photo=exact_product.get("photo_url", ""),
            caption=build_caption(exact_product)
        )
        return

    # 2) partial / collection search
    matches = find_partial_matches(text)

    if not matches:
        await update.message.reply_text("Not found")
        return

    # 3) one match only
    if len(matches) == 1:
        await update.message.reply_photo(
            photo=matches[0].get("photo_url", ""),
            caption=build_caption(matches[0])
        )
        return

    # 4) many matches -> send all
    for product in matches:
        await update.message.reply_photo(
            photo=product.get("photo_url", ""),
            caption=build_caption(product)
        )


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
