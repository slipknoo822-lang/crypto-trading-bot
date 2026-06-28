import sqlite3
from datetime import datetime

class AuditDatabase:
    def __init__(self, db_path="trading_audit.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    symbol TEXT,
                    side TEXT,
                    quantity REAL,
                    price REAL,
                    cost REAL,
                    status TEXT,
                    slippage REAL,
                    latency_ms INTEGER
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    balance REAL,
                    pnl REAL,
                    drawdown REAL
                )
            """)
            conn.commit()

    def log_order(self, symbol: str, side: str, qty: float, price: float, cost: float, status: str, slippage: float, latency: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO orders (timestamp, symbol, side, quantity, price, cost, status, slippage, latency_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (datetime.utcnow().isoformat(), symbol, side, qty, price, cost, status, slippage, latency))
            conn.commit()

    def log_portfolio(self, balance: float, pnl: float, drawdown: float):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO portfolio_logs (timestamp, balance, pnl, drawdown)
                VALUES (?, ?, ?, ?)
            """, (datetime.utcnow().isoformat(), balance, pnl, drawdown))
            conn.commit()
