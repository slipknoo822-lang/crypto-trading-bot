#!/usr/bin/env python3
"""
Crypto Trading Bot — Institutional-Grade Main Entry Point.
Asynchronous execution engine driven by live WebSockets updates.
"""
import sys
import time
import asyncio
import pandas as pd
from loguru import logger

from src.config import Config
from src.exchange import BinanceClient
from src.strategies import STRATEGIES
from src.models import RiskManager
from src.utils import PaperTrader
from src.utils.database import AuditDatabase


def setup_logging():
    logger.remove()
    logger.add(sys.stderr, level=Config.LOG_LEVEL,
               format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | {message}")
    logger.add("bot.log", rotation="10 MB", level="DEBUG")


async def run_engine():
    setup_logging()
    logger.info("=" * 50)
    logger.info("Crypto Trading Bot Starting (Skala Institusi)")
    logger.info(f"Symbol: {Config.SYMBOL} | WS Interval: {Config.INTERVAL}")
    logger.info(f"Strategy: {Config.STRATEGY} | Mode: {Config.MODE}")
    logger.info("=" * 50)

    # Init database, strategy, risk, exchange, and paper engine
    db = AuditDatabase()
    strategy_cls = STRATEGIES.get(Config.STRATEGY)
    if not strategy_cls:
        logger.error(f"Unknown strategy: {Config.STRATEGY}")
        sys.exit(1)
    strategy = strategy_cls()

    risk = RiskManager(
        stop_loss_pct=Config.STOP_LOSS_PCT,
        take_profit_pct=Config.TAKE_PROFIT_PCT,
        max_position_usd=Config.MAX_POSITION_SIZE,
    )

    paper = PaperTrader() if Config.MODE == "paper" else None
    exchange = BinanceClient(
        api_key=Config.API_KEY,
        api_secret=Config.API_SECRET,
        testnet=(Config.MODE != "live"),
    )
    
    # Initialize connection
    await exchange.init_async()

    # Pre-populate historical data to warm up indicators
    logger.info("Warming up historical data buffer...")
    hist_df = exchange.get_klines(Config.SYMBOL, Config.INTERVAL, limit=100)
    
    # Track current metrics
    current_balance = paper.balance if paper else await exchange.get_balance()
    risk.update_metrics(current_balance)

    logger.info("Starting WebSockets live stream loop...")
    
    try:
        async for msg in exchange.start_kline_socket(Config.SYMBOL, Config.INTERVAL):
            kline = msg.get("k", {})
            is_closed = kline.get("x", False)
            price = float(kline.get("c", 0.0))
            
            # 1. Update live price updates for active position exit checks (low latency)
            for pos in list(risk.positions):
                exit_reason = risk.check_exit(pos, price)
                if exit_reason:
                    start_exec = time.perf_counter()
                    if paper:
                        res = paper.sell(pos.symbol, pos.quantity, price)
                    else:
                        res = await exchange.market_sell(pos.symbol, pos.quantity)
                    
                    latency = res.get("latency_ms", int((time.perf_counter() - start_exec) * 1000))
                    slippage = res.get("slippage", 0.0)
                    cost = res.get("cost", pos.quantity * price)
                    
                    # Log audit and close
                    db.log_order(pos.symbol, "SELL", pos.quantity, price, cost, "FILLED", slippage, latency)
                    risk.close_position(pos, exit_reason)
                    
                    # Update portfolio stats
                    current_balance = paper.balance if paper else await exchange.get_balance()
                    drawdown = ((risk.peak_balance - current_balance) / risk.peak_balance) * 100 if risk.peak_balance > 0 else 0.0
                    risk.update_metrics(current_balance)
                    db.log_portfolio(current_balance, current_balance - 10000.0 if paper else 0.0, drawdown)

            # 2. On candle close, append to DataFrame & check strategy signals
            if is_closed:
                logger.info(f"Candle closed. Price: ${price:,.2f}. Running strategy analysis...")
                
                # Dynamic update klines df
                new_row = {
                    "timestamp": pd.to_datetime(kline.get("t"), unit="ms"),
                    "open": float(kline.get("o")),
                    "high": float(kline.get("h")),
                    "low": float(kline.get("l")),
                    "close": price,
                    "volume": float(kline.get("v"))
                }
                hist_df = pd.concat([hist_df, pd.DataFrame([new_row])], ignore_index=True).iloc[1:]
                
                signal = strategy.analyze(hist_df)
                logger.info(f"Strategy signal: {signal} | Sharpe: {risk.calculate_sharpe():.2f}")

                # Execute order
                if signal == "BUY" and not risk.has_open_position:
                    current_balance = paper.balance if paper else await exchange.get_balance()
                    if risk.can_open(price, Config.QUANTITY, current_balance):
                        start_exec = time.perf_counter()
                        if paper:
                            res = paper.buy(Config.SYMBOL, Config.QUANTITY, price)
                        else:
                            res = await exchange.market_buy(Config.SYMBOL, Config.QUANTITY)
                        
                        if res.get("status") == "FILLED" or "orderId" in res:
                            latency = res.get("latency_ms", int((time.perf_counter() - start_exec) * 1000))
                            slippage = res.get("slippage", 0.0)
                            cost = res.get("cost", Config.QUANTITY * price)
                            
                            db.log_order(Config.SYMBOL, "BUY", Config.QUANTITY, price, cost, "FILLED", slippage, latency)
                            risk.open_position(Config.SYMBOL, price, Config.QUANTITY, entry_time=time.time())

                elif signal == "SELL" and risk.has_open_position:
                    for pos in list(risk.positions):
                        start_exec = time.perf_counter()
                        if paper:
                            res = paper.sell(pos.symbol, pos.quantity, price)
                        else:
                            res = await exchange.market_sell(pos.symbol, pos.quantity)
                        
                        latency = res.get("latency_ms", int((time.perf_counter() - start_exec) * 1000))
                        slippage = res.get("slippage", 0.0)
                        cost = res.get("cost", pos.quantity * price)
                        
                        db.log_order(pos.symbol, "SELL", pos.quantity, price, cost, "FILLED", slippage, latency)
                        risk.close_position(pos, "STRATEGY_SELL")

                # Regularly write portfolio metrics
                current_balance = paper.balance if paper else await exchange.get_balance()
                drawdown = ((risk.peak_balance - current_balance) / risk.peak_balance) * 100 if risk.peak_balance > 0 else 0.0
                risk.update_metrics(current_balance)
                db.log_portfolio(current_balance, current_balance - 10000.0 if paper else 0.0, drawdown)
                if paper:
                    logger.info(f"Summary: {paper.summary()}")

    except asyncio.CancelledError:
        logger.info("Engine task cancelled.")
    finally:
        await exchange.close_async()
        logger.info("Async exchange client connection closed.")


def main():
    try:
        asyncio.run(run_engine())
    except KeyboardInterrupt:
        logger.info("Bot execution terminated by user.")


if __name__ == "__main__":
    main()
