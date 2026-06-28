#!/usr/bin/env python3
"""
Crypto Trading Bot — Main entry point.
Fetches candles, runs strategy, executes trades (paper or live).
"""
import sys
import time
from loguru import logger

from src.config import Config
from src.exchange import BinanceClient
from src.strategies import STRATEGIES
from src.models import RiskManager
from src.utils import PaperTrader


def setup_logging():
    logger.remove()
    logger.add(sys.stderr, level=Config.LOG_LEVEL,
               format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | {message}")
    logger.add("bot.log", rotation="10 MB", level="DEBUG")


def main():
    setup_logging()
    logger.info("=" * 50)
    logger.info(f"Crypto Trading Bot starting")
    logger.info(f"Symbol: {Config.SYMBOL} | Interval: {Config.INTERVAL}")
    logger.info(f"Strategy: {Config.STRATEGY} | Mode: {Config.MODE}")
    logger.info("=" * 50)

    # Init strategy
    strategy_cls = STRATEGIES.get(Config.STRATEGY)
    if not strategy_cls:
        logger.error(f"Unknown strategy: {Config.STRATEGY}")
        logger.info(f"Available: {list(STRATEGIES.keys())}")
        sys.exit(1)
    strategy = strategy_cls()

    # Init risk manager
    risk = RiskManager(
        stop_loss_pct=Config.STOP_LOSS_PCT,
        take_profit_pct=Config.TAKE_PROFIT_PCT,
        max_position_usd=Config.MAX_POSITION_SIZE,
    )

    # Init exchange / paper trader
    paper = PaperTrader() if Config.MODE == "paper" else None
    exchange = BinanceClient(
        api_key=Config.API_KEY,
        api_secret=Config.API_SECRET,
        testnet=(Config.MODE != "live"),
    )

    logger.info(f"Strategy: {strategy.name()} | Risk: SL={Config.STOP_LOSS_PCT}% TP={Config.TAKE_PROFIT_PCT}%")

    # Main loop
    cycle = 0
    while True:
        cycle += 1
        try:
            logger.info(f"--- Cycle {cycle} ---")

            # 1. Fetch candles
            df = exchange.get_klines(Config.SYMBOL, Config.INTERVAL)
            price = df["close"].iloc[-1]
            logger.info(f"Current price: ${price:,.2f}")

            # 2. Check open positions for exit
            for pos in list(risk.positions):
                exit_reason = risk.check_exit(pos, price)
                if exit_reason:
                    if paper:
                        paper.sell(pos.symbol, pos.quantity, price)
                    else:
                        exchange.market_sell(pos.symbol, pos.quantity)
                    risk.close_position(pos, exit_reason)

            # 3. Run strategy
            signal = strategy.analyze(df)
            logger.info(f"Signal: {signal}")

            # 4. Execute
            if signal == "BUY" and not risk.has_open_position:
                if risk.can_open(price, Config.QUANTITY):
                    if paper:
                        result = paper.buy(Config.SYMBOL, Config.QUANTITY, price)
                    else:
                        result = exchange.market_buy(Config.SYMBOL, Config.QUANTITY)
                    if result.get("status") == "FILLED" or "orderId" in result:
                        risk.open_position(Config.SYMBOL, price, Config.QUANTITY)

            elif signal == "SELL" and risk.has_open_position:
                for pos in list(risk.positions):
                    if paper:
                        paper.sell(pos.symbol, pos.quantity, price)
                    else:
                        exchange.market_sell(pos.symbol, pos.quantity)
                    risk.close_position(pos, "STRATEGY_SELL")

            # 5. Status
            if paper:
                logger.info(f"Paper: {paper.summary()}")

            # Sleep based on interval
            sleep_map = {"1m": 60, "5m": 300, "15m": 900,
                         "30m": 1800, "1h": 3600, "4h": 14400, "1d": 86400}
            sleep_sec = sleep_map.get(Config.INTERVAL, 3600)
            logger.info(f"Sleeping {sleep_sec}s until next cycle...")
            time.sleep(sleep_sec)

        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
            if paper:
                logger.info(f"Final: {paper.summary()}")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            time.sleep(30)


if __name__ == "__main__":
    main()
