import asyncio
import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_HANDLE = os.getenv("CHANNEL_HANDLE", "@CoinSignal")

DEFAULT_INTERVAL = 1800

def get_fetch_interval() -> int:
    raw_val = os.getenv("FETCH_INTERVAL")
    if not raw_val:
        return DEFAULT_INTERVAL
    try:
        val = int(raw_val)
        return val if val > 0 else DEFAULT_INTERVAL
    except ValueError:
        logging.warning(f"Invalid FETCH_INTERVAL '{raw_val}'. Falling back to {DEFAULT_INTERVAL}s.")
        return DEFAULT_INTERVAL

FETCH_INTERVAL = get_fetch_interval()

def format_number(val):
    if not val:
        return "N/A"
    if val >= 1_000_000_000:
        return f"${val / 1_000_000_000:.2f}B"
    elif val >= 1_000_000:
        return f"${val / 1_000_000:.2f}M"
    return f"${val:,.2f}"

def fetch_crypto_markets():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": "bitcoin,ethereum,solana",
        "order": "market_cap_desc",
        "per_page": 3,
        "page": 1,
        "sparkline": "false"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        logging.error(f"Error fetching market data: {e}")
        return None

def format_message(market_data):
    if not market_data or not isinstance(market_data, list):
        return None

    coins_summary = []
    
    for coin in market_data:
        symbol = coin.get("symbol", "").upper()
        name = coin.get("name", "")
        price = coin.get("current_price", 0)
        change_24h = coin.get("price_change_percentage_24h", 0)
        high_24h = coin.get("high_24h", 0)
        low_24h = coin.get("low_24h", 0)
        mcap = format_number(coin.get("market_cap", 0))
        vol = format_number(coin.get("total_volume", 0))

        emoji = "📈" if change_24h >= 0 else "📉"
        change_sign = "+" if change_24h >= 0 else ""

        block = (
            f"🔹 **{name} (${symbol})**\n"
            f"💵 **Price:** ${price:,.2f} ({emoji} {change_sign}{change_24h:.2f}%)\n"
            f"📊 **24h Range:** ${low_24h:,.2f} – ${high_24h:,.2f}\n"
            f"💰 **Market Cap:** {mcap} | **24h Vol:** {vol}\n"
        )
        coins_summary.append(block)

    return (
        "🚨 **CoinSignal | Full Market Report**\n\n"
        + "\n".join(coins_summary) +
        "\n⚡ *Automated signal feed*"
    )

# /start Command Handler with Image
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name = update.effective_user.first_name
    welcome_text = (
        f"👋 **Welcome to CoinSignal, {user_first_name}!**\n\n"
        "Your automated portal for real-time crypto markets, forex updates, and breaking financial news.\n\n"
        "📊 **What I Do:**\n"
        "• Post live price alerts to the channel\n"
        "• Track 24h market metrics, high/low ranges, and volume\n"
        "• Deliver breaking crypto & forex market insights\n\n"
        f"📢 **Join our official channel:** {CHANNEL_HANDLE}"
    )
    
    image_path = "welcome.png"

    if os.path.exists(image_path):
        with open(image_path, "rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=welcome_text,
                parse_mode="Markdown"
            )
    else:
        # Fallback if image isn't found
        await update.message.reply_text(
            text=welcome_text,
            parse_mode="Markdown"
        )

# Background loop for channel posting
async def post_to_channel_loop(app):
    await asyncio.sleep(5)  # Initial boot buffer
    while True:
        data = fetch_crypto_markets()
        message = format_message(data)
        if message:
            try:
                await app.bot.send_message(
                    chat_id=CHANNEL_HANDLE,
                    text=message,
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )
                logging.info(f"Posted update to {CHANNEL_HANDLE}")
            except Exception as e:
                logging.error(f"Failed channel post: {e}")

        await asyncio.sleep(FETCH_INTERVAL)

async def post_init(app):
    """Schedules the background posting task when app starts."""
    asyncio.create_task(post_to_channel_loop(app))

def main():
    if not TELEGRAM_BOT_TOKEN:
        logging.error("TELEGRAM_BOT_TOKEN is missing!")
        return

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    # Handlers
    app.add_handler(CommandHandler("start", start_command))

    logging.info("CoinSignal Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
