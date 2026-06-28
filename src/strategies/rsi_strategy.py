"""RSI Strategy — oversold/overbought signals."""
import ta
import pandas as pd
from .base import BaseStrategy


class RSIStrategy(BaseStrategy):
    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def name(self) -> str:
        return "RSI"

    def analyze(self, df: pd.DataFrame) -> str:
        rsi = ta.momentum.RSIIndicator(df["close"], window=self.period).rsi()
        last = rsi.iloc[-1]

        if last <= self.oversold:
            return "BUY"
        elif last >= self.overbought:
            return "SELL"
        return "HOLD"
