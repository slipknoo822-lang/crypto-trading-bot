"""Crypto Trading Bot - Config loader."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Binance
    API_KEY = os.getenv("BINANCE_API_KEY", "")
    API_SECRET = os.getenv("BINANCE_API_SECRET", "")

    # Trading
    SYMBOL = os.getenv("TRADING_SYMBOL", "BTCUSDT")
    INTERVAL = os.getenv("TRADING_INTERVAL", "1h")
    QUANTITY = float(os.getenv("TRADING_QUANTITY", "0.001"))

    # Mode
    MODE = os.getenv("TRADING_MODE", "paper")  # paper | live

    # Strategy
    STRATEGY = os.getenv("STRATEGY", "combined")  # rsi | macd | bollinger | combined

    # Risk
    STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "2.0"))
    TAKE_PROFIT_PCT = float(os.getenv("TAKE_PROFIT_PCT", "4.0"))
    MAX_POSITION_SIZE = float(os.getenv("MAX_POSITION_SIZE", "100.0"))

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
