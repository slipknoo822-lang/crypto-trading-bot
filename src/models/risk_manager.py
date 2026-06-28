"""Risk Manager — stop-loss, take-profit, dynamic drawdown limits, and portfolio safety."""
from dataclasses import dataclass
from loguru import logger
import numpy as np


@dataclass
class Position:
    symbol: str
    side: str  # "LONG" or "SHORT"
    entry_price: float
    quantity: float
    stop_loss: float
    take_profit: float
    entry_time: float


class RiskManager:
    def __init__(self, stop_loss_pct: float, take_profit_pct: float, max_position_usd: float, max_drawdown_pct: float = 10.0):
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_position_usd = max_position_usd
        self.max_drawdown_pct = max_drawdown_pct
        self.positions: list[Position] = []
        self.peak_balance = 0.0
        self.equity_curve = []

    def can_open(self, price: float, quantity: float, current_balance: float) -> bool:
        cost = price * quantity
        if cost > self.max_position_usd:
            logger.warning(f"[RISK] Position size ${cost:.2f} exceeds max ${self.max_position_usd}")
            return False
        
        # Check current drawdown
        if self.peak_balance > 0:
            current_drawdown = ((self.peak_balance - current_balance) / self.peak_balance) * 100
            if current_drawdown > self.max_drawdown_pct:
                logger.error(f"[RISK] Maximum drawdown limit breached: {current_drawdown:.2f}% > {self.max_drawdown_pct}%")
                return False
                
        return True

    def open_position(self, symbol: str, price: float, quantity: float, entry_time: float) -> Position:
        sl = price * (1 - self.stop_loss_pct / 100)
        tp = price * (1 + self.take_profit_pct / 100)
        pos = Position(symbol=symbol, side="LONG", entry_price=price,
                       quantity=quantity, stop_loss=sl, take_profit=tp, entry_time=entry_time)
        self.positions.append(pos)
        logger.info(f"[RISK] OPEN LONG {symbol} @ {price:.2f} | SL={sl:.2f} TP={tp:.2f}")
        return pos

    def update_metrics(self, current_balance: float):
        self.equity_curve.append(current_balance)
        if current_balance > self.peak_balance:
            self.peak_balance = current_balance

    def calculate_sharpe(self) -> float:
        """Returns proxy Sharpe Ratio from equity curve returns."""
        if len(self.equity_curve) < 5:
            return 0.0
        returns = np.diff(self.equity_curve) / self.equity_curve[:-1]
        std = np.std(returns)
        if std == 0:
            return 0.0
        return float((np.mean(returns) / std) * np.sqrt(252)) # Annualized proxy

    def check_exit(self, pos: Position, current_price: float) -> str | None:
        if current_price <= pos.stop_loss:
            return "STOP_LOSS"
        if current_price >= pos.take_profit:
            return "TAKE_PROFIT"
        return None

    def close_position(self, pos: Position, reason: str):
        if pos in self.positions:
            self.positions.remove(pos)
        logger.info(f"[RISK] CLOSED {pos.symbol} ({reason})")

    @property
    def has_open_position(self) -> bool:
        return len(self.positions) > 0
