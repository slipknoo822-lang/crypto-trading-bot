"""Paper trading engine — simulates orders with audit logs and latency emulation."""
import time
import random
from loguru import logger


class PaperTrader:
    def __init__(self, initial_balance: float = 10000.0):
        self.balance = initial_balance
        self.holdings: dict[str, float] = {}
        self.trades: list[dict] = []
        self.initial_balance = initial_balance

    def buy(self, symbol: str, quantity: float, price: float) -> dict:
        cost = quantity * price
        if cost > self.balance:
            logger.warning(f"Insufficient paper balance: ${self.balance:.2f} < ${cost:.2f}")
            return {"status": "REJECTED", "reason": "insufficient_balance"}

        # Simulate network latency and slippage (0.01% - 0.05%)
        latency = random.randint(10, 50)
        slippage = price * random.uniform(0.0001, 0.0005)
        execution_price = price + slippage
        cost = quantity * execution_price

        self.balance -= cost
        self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity
        trade = {
            "side": "BUY",
            "symbol": symbol,
            "qty": quantity,
            "price": execution_price,
            "cost": cost,
            "slippage": slippage,
            "latency_ms": latency,
            "status": "FILLED"
        }
        self.trades.append(trade)
        logger.info(f"[PAPER] BUY {quantity} {symbol} @ ${execution_price:.2f} (Slip: ${slippage:.4f}, Latency: {latency}ms)")
        return trade

    def sell(self, symbol: str, quantity: float, price: float) -> dict:
        held = self.holdings.get(symbol, 0)
        if held < quantity:
            logger.warning(f"Insufficient holdings: {held} < {quantity}")
            return {"status": "REJECTED", "reason": "insufficient_holdings"}

        # Simulate network latency and slippage
        latency = random.randint(10, 50)
        slippage = price * random.uniform(0.0001, 0.0005)
        execution_price = price - slippage
        revenue = quantity * execution_price

        self.balance += revenue
        self.holdings[symbol] -= quantity
        if self.holdings[symbol] <= 0:
            del self.holdings[symbol]
        trade = {
            "side": "SELL",
            "symbol": symbol,
            "qty": quantity,
            "price": execution_price,
            "revenue": revenue,
            "slippage": slippage,
            "latency_ms": latency,
            "status": "FILLED"
        }
        self.trades.append(trade)
        logger.info(f"[PAPER] SELL {quantity} {symbol} @ ${execution_price:.2f} (Slip: ${slippage:.4f}, Latency: {latency}ms)")
        return trade

    @property
    def pnl(self) -> float:
        return self.balance - self.initial_balance

    def summary(self) -> str:
        return (f"Balance: ${self.balance:.2f} | PnL: ${self.pnl:+.2f} | "
                f"Trades: {len(self.trades)} | Holdings: {self.holdings}")
