"""Risk Manager — stop-loss, take-profit, position sizing."""
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class Position:
    symbol: str
    side: str  # "LONG" or "SHORT"
    entry_price: float
    quantity: float
    stop_loss: float
    take_profit: float


class RiskManager:
    def __init__(self, stop_loss_pct: float, take_profit_pct: float, max_position_usd: float):
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_position_usd = max_position_usd
        self.positions: list[Position] = []

    def can_open(self, price: float, quantity: float) -> bool:
        cost = price * quantity
        if cost > self.max_position_usd:
            logger.warning(f"Position ${cost:.2f} exceeds max ${self.max_position_usd}")
            return False
        return True

    def open_position(self, symbol: str, price: float, quantity: float) -> Position:
        sl = price * (1 - self.stop_loss_pct / 100)
        tp = price * (1 + self.take_profit_pct / 100)
        pos = Position(symbol=symbol, side="LONG", entry_price=price,
                       quantity=quantity, stop_loss=sl, take_profit=tp)
        self.positions.append(pos)
        logger.info(f"Opened LONG {symbol} @ {price:.2f} | SL={sl:.2f} TP={tp:.2f}")
        return pos

    def check_exit(self, pos: Position, current_price: float) -> str | None:
        """Returns 'STOP_LOSS', 'TAKE_PROFIT', or None."""
        if current_price <= pos.stop_loss:
            return "STOP_LOSS"
        if current_price >= pos.take_profit:
            return "TAKE_PROFIT"
        return None

    def close_position(self, pos: Position, reason: str):
        if pos in self.positions:
            self.positions.remove(pos)
        logger.info(f"Closed {pos.symbol} ({reason})")

    @property
    def has_open_position(self) -> bool:
        return len(self.positions) > 0
