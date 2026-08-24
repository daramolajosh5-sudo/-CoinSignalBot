import asyncio
import os
import requests
from telegram import Bot

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_HANDLE = os.getenv("CHANNEL_HANDLE", "@CoinSignal")

# Fallback default interval (in seconds): 1800s = 30 minutes
DEFAULT_INTERVAL = 1800

def get_fetch_interval() -> int:
    """Reads FETCH_INTERVAL from environment variables. 
    Defaults to 1800 seconds if unset or invalid."""
    raw_val = os.getenv("FETCH_INTERVAL")
    if not raw_val:
        return DEFAULT_INTERVAL
    try:
        val = int(raw_val)
        return val if val > 0 else DEFAULT_INTERVAL
    except ValueError:
        print(f"Warning: Invalid FETCH_INTERVAL '{raw_val}'. Using default ({DEFAULT_INTERVAL}s).")
        return DEFAULT_INTERVAL

FETCH_INTERVAL = get_fetch_interval()
