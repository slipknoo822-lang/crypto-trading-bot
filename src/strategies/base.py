"""Base strategy interface."""
from abc import ABC, abstractmethod
import pandas as pd


class BaseStrategy(ABC):
    """All strategies return a signal: 'BUY', 'SELL', or 'HOLD'."""

    @abstractmethod
    def analyze(self, df: pd.DataFrame) -> str:
        ...

    @abstractmethod
    def name(self) -> str:
        ...
