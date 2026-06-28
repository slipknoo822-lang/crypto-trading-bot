"""Test strategies with synthetic data."""
import time
import pandas as pd
import numpy as np
from src.strategies import RSIStrategy, MACDStrategy, BollingerStrategy, CombinedStrategy
from src.utils import PaperTrader
from src.models import RiskManager


def make_df(prices: list[float]) -> pd.DataFrame:
    """Create minimal OHLCV dataframe from price list."""
    return pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=len(prices), freq="h"),
        "open": prices,
        "high": [p * 1.01 for p in prices],
        "low": [p * 0.99 for p in prices],
        "close": prices,
        "volume": [100.0] * len(prices),
    })


def test_strategies():
    # Generate 50 candles of trending-down data (should trigger BUY on RSI)
    np.random.seed(42)
    downtrend = [50000 - i * 100 + np.random.randn() * 50 for i in range(50)]
    df_down = make_df(downtrend)

    rsi = RSIStrategy()
    macd = MACDStrategy()
    bb = BollingerStrategy()
    combined = CombinedStrategy()

    for s in [rsi, macd, bb, combined]:
        signal = s.analyze(df_down)
        assert signal in ("BUY", "SELL", "HOLD"), f"{s.name()} returned invalid: {signal}"
        print(f"  {s.name():12s} → {signal}")

    print("  All strategies returned valid signals ✓")


def test_paper_trader():
    pt = PaperTrader(initial_balance=10000)
    # Buy and sell calls now accept execution prices which are subject to slippage inside
    result = pt.buy("BTCUSDT", 0.1, 50000)
    assert result["status"] == "FILLED"
    assert pt.balance < 10000.0  # Balance reduced by price + slippage cost

    result = pt.sell("BTCUSDT", 0.1, 55000)
    assert result["status"] == "FILLED"
    print(f"  PaperTrader: {pt.summary()} ✓")


def test_risk_manager():
    rm = RiskManager(stop_loss_pct=2.0, take_profit_pct=4.0, max_position_usd=100)
    assert rm.can_open(50000, 0.001, 10000.0)  # $50 < $100
    assert not rm.can_open(50000, 0.01, 10000.0)  # $500 > $100

    pos = rm.open_position("BTCUSDT", 50000, 0.001, entry_time=time.time())
    assert rm.has_open_position
    assert rm.check_exit(pos, 50000) is None  # no exit
    assert rm.check_exit(pos, 48000) == "STOP_LOSS"
    assert rm.check_exit(pos, 53000) == "TAKE_PROFIT"
    print(f"  RiskManager: SL/TP checks passed ✓")


if __name__ == "__main__":
    print("Testing strategies...")
    test_strategies()
    print("Testing paper trader...")
    test_paper_trader()
    print("Testing risk manager...")
    test_risk_manager()
    print("\nAll tests passed! ✅")
