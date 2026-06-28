"""Bollinger Bands Strategy — breakout signals."""
import ta
import pandas as pd
from .base import BaseStrategy


class BollingerStrategy(BaseStrategy):
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        self.period = period
        self.std_dev = std_dev

    def name(self) -> str:
        return "Bollinger"

    def analyze(self, df: pd.DataFrame) -> str:
        bb = ta.volatility.BollingerBands(
            df["close"], window=self.period, window_dev=self.std_dev
        )
        close = df["close"].iloc[-1]
        upper = bb.bollinger_hband().iloc[-1]
        lower = bb.bollinger_lband().iloc[-1]

        if close <= lower:
            return "BUY"
        elif close >= upper:
            return "SELL"
        return "HOLD"
