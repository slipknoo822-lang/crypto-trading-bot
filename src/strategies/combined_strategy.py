"""Combined strategy — majority vote from RSI + MACD + Bollinger."""
import pandas as pd
from .base import BaseStrategy
from .rsi_strategy import RSIStrategy
from .macd_strategy import MACDStrategy
from .bollinger_strategy import BollingerStrategy
from loguru import logger


class CombinedStrategy(BaseStrategy):
    def __init__(self):
        self.strategies = [RSIStrategy(), MACDStrategy(), BollingerStrategy()]

    def name(self) -> str:
        return "Combined"

    def analyze(self, df: pd.DataFrame) -> str:
        signals = {}
        for s in self.strategies:
            sig = s.analyze(df)
            signals[s.name()] = sig
            logger.debug(f"  {s.name()} → {sig}")

        votes = list(signals.values())
        buy_count = votes.count("BUY")
        sell_count = votes.count("SELL")

        # Need 2/3 majority
        if buy_count >= 2:
            logger.info(f"Combined signal: BUY (votes: {signals})")
            return "BUY"
        elif sell_count >= 2:
            logger.info(f"Combined signal: SELL (votes: {signals})")
            return "SELL"

        logger.info(f"Combined signal: HOLD (votes: {signals})")
        return "HOLD"
