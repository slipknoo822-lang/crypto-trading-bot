"""Paper trading engine — simulates orders without real money."""
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

        self.balance -= cost
        self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity
        trade = {"side": "BUY", "symbol": symbol, "qty": quantity,
                 "price": price, "cost": cost}
        self.trades.append(trade)
        logger.info(f"[PAPER] BUY {quantity} {symbol} @ ${price:.2f} = ${cost:.2f}")
        return {"status": "FILLED", **trade}

    def sell(self, symbol: str, quantity: float, price: float) -> dict:
        held = self.holdings.get(symbol, 0)
        if held < quantity:
            logger.warning(f"Insufficient holdings: {held} < {quantity}")
            return {"status": "REJECTED", "reason": "insufficient_holdings"}

        revenue = quantity * price
        self.balance += revenue
        self.holdings[symbol] -= quantity
        if self.holdings[symbol] <= 0:
            del self.holdings[symbol]
        trade = {"side": "SELL", "symbol": symbol, "qty": quantity,
                 "price": price, "revenue": revenue}
        self.trades.append(trade)
        logger.info(f"[PAPER] SELL {quantity} {symbol} @ ${price:.2f} = ${revenue:.2f}")
        return {"status": "FILLED", **trade}

    @property
    def pnl(self) -> float:
        return self.balance - self.initial_balance

    def summary(self) -> str:
        return (f"Balance: ${self.balance:.2f} | PnL: ${self.pnl:+.2f} | "
                f"Trades: {len(self.trades)} | Holdings: {self.holdings}")
