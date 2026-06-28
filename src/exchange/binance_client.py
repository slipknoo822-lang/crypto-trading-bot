"""Binance exchange client wrapper."""
import pandas as pd
from binance.client import Client
from loguru import logger


class BinanceClient:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.client = Client(api_key, api_secret, testnet=testnet)
        logger.info(f"Binance client initialized (testnet={testnet})")

    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> pd.DataFrame:
        """Fetch OHLCV candles → DataFrame."""
        raw = self.client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(raw, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_vol", "trades", "taker_buy_base",
            "taker_buy_quote", "ignore"
        ])
        for col in ("open", "high", "low", "close", "volume"):
            df[col] = df[col].astype(float)
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df[["timestamp", "open", "high", "low", "close", "volume"]]

    def get_price(self, symbol: str) -> float:
        return float(self.client.get_symbol_ticker(symbol=symbol)["price"])

    def market_buy(self, symbol: str, quantity: float) -> dict:
        logger.info(f"BUY {quantity} {symbol}")
        return self.client.order_market_buy(symbol=symbol, quantity=quantity)

    def market_sell(self, symbol: str, quantity: float) -> dict:
        logger.info(f"SELL {quantity} {symbol}")
        return self.client.order_market_sell(symbol=symbol, quantity=quantity)

    def get_balance(self, asset: str = "USDT") -> float:
        return float(self.client.get_asset_balance(asset=asset)["free"])
