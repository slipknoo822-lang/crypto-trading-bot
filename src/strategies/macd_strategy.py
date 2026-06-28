"""MACD Strategy — crossover signals."""
import ta
import pandas as pd
from .base import BaseStrategy


class MACDStrategy(BaseStrategy):
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        self.fast = fast
        self.slow = slow
        self.signal_period = signal

    def name(self) -> str:
        return "MACD"

    def analyze(self, df: pd.DataFrame) -> str:
        macd_ind = ta.trend.MACD(
            df["close"], window_fast=self.fast,
            window_slow=self.slow, window_sign=self.signal_period
        )
        macd_line = macd_ind.macd().iloc[-1]
        signal_line = macd_ind.macd_signal().iloc[-1]
        prev_macd = macd_ind.macd().iloc[-2]
        prev_signal = macd_ind.macd_signal().iloc[-2]

        # Bullish crossover
        if prev_macd <= prev_signal and macd_line > signal_line:
            return "BUY"
        # Bearish crossover
        if prev_macd >= prev_signal and macd_line < signal_line:
            return "SELL"
        return "HOLD"
