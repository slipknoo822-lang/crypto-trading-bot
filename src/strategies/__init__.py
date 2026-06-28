from .rsi_strategy import RSIStrategy
from .macd_strategy import MACDStrategy
from .bollinger_strategy import BollingerStrategy
from .combined_strategy import CombinedStrategy
from .base import BaseStrategy

STRATEGIES = {
    "rsi": RSIStrategy,
    "macd": MACDStrategy,
    "bollinger": BollingerStrategy,
    "combined": CombinedStrategy,
}

__all__ = ["RSIStrategy", "MACDStrategy", "BollingerStrategy",
           "CombinedStrategy", "BaseStrategy", "STRATEGIES"]
