"""Async WebSockets & Resilient Exchange Client."""
import asyncio
import time
import pandas as pd
from binance.client import Client
from binance import AsyncClient, BinanceSocketManager
from loguru import logger

class BinanceClient:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.sync_client = Client(api_key, api_secret, testnet=testnet)
        self.async_client = None
        self.bsm = None
        logger.info(f"Binance client initialized (testnet={testnet})")

    async def init_async(self):
        if not self.async_client:
            self.async_client = await AsyncClient.create(self.api_key, self.api_secret, testnet=self.testnet)
            self.bsm = BinanceSocketManager(self.async_client)
            logger.info("Async Binance client and WebSockets manager initialized")

    async def close_async(self):
        if self.async_client:
            await self.async_client.close_connection()

    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> pd.DataFrame:
        """Fetch OHLCV candles (Sync fallback)."""
        raw = self.sync_client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(raw, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_vol", "trades", "taker_buy_base",
            "taker_buy_quote", "ignore"
        ])
        for col in ("open", "high", "low", "close", "volume"):
            df[col] = df[col].astype(float)
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df[["timestamp", "open", "high", "low", "close", "volume"]]

    async def start_kline_socket(self, symbol: str, interval: str):
        """Yields real-time candle update feeds via WebSockets."""
        await self.init_async()
        socket = self.bsm.kline_socket(symbol=symbol, interval=interval)
        while True:
            try:
                async with socket as stream:
                    while True:
                        msg = await stream.recv()
                        # Yield if kline is closed or critical update
                        yield msg
            except Exception as e:
                logger.error(f"[WS ERROR] Connection lost: {e}. Reconnecting in 5s...")
                await asyncio.sleep(5)

    async def market_buy(self, symbol: str, quantity: float) -> dict:
        start_time = time.perf_counter()
        logger.info(f"[EXEC] Market BUY order triggered: {quantity} {symbol}")
        await self.init_async()
        try:
            res = await self.async_client.order_market_buy(symbol=symbol, quantity=quantity)
            latency = int((time.perf_counter() - start_time) * 1000)
            res["latency_ms"] = latency
            return res
        except Exception as e:
            logger.error(f"[EXEC ERROR] Market BUY failed: {e}")
            raise e

    async def market_sell(self, symbol: str, quantity: float) -> dict:
        start_time = time.perf_counter()
        logger.info(f"[EXEC] Market SELL order triggered: {quantity} {symbol}")
        await self.init_async()
        try:
            res = await self.async_client.order_market_sell(symbol=symbol, quantity=quantity)
            latency = int((time.perf_counter() - start_time) * 1000)
            res["latency_ms"] = latency
            return res
        except Exception as e:
            logger.error(f"[EXEC ERROR] Market SELL failed: {e}")
            raise e

    async def get_balance(self, asset: str = "USDT") -> float:
        await self.init_async()
        try:
            res = await self.async_client.get_asset_balance(asset=asset)
            return float(res["free"])
        except Exception:
            return 0.0
