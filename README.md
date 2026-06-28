# 🤖 Crypto Trading Bot

AI-powered cryptocurrency trading bot untuk Binance dengan multi-strategy support.

## Features

- **Multi-Strategy**: RSI, MACD, Bollinger Bands, dan Combined (voting)
- **Risk Management**: Stop-loss, take-profit, position sizing
- **Paper Trading**: Mode simulasi tanpa uang asli
- **Live Trading**: Eksekusi langsung di Binance
- **Structured Codebase**: Modular, clean, extensible

## Project Structure

```
crypto-trading-bot/
├── main.py                    # Entry point
├── requirements.txt           # Dependencies
├── .env.example               # Config template
├── src/
│   ├── config.py              # Config loader (.env)
│   ├── exchange/
│   │   └── binance_client.py  # Binance API wrapper
│   ├── strategies/
│   │   ├── base.py            # Strategy interface
│   │   ├── rsi_strategy.py    # RSI (oversold/overbought)
│   │   ├── macd_strategy.py   # MACD (crossover)
│   │   ├── bollinger_strategy.py  # Bollinger Bands (breakout)
│   │   └── combined_strategy.py   # Majority vote (2/3)
│   ├── models/
│   │   └── risk_manager.py    # SL/TP, position tracking
│   └── utils/
│       └── paper_trader.py    # Paper trading simulator
└── tests/
```

## Quick Start

```bash
# 1. Clone
git clone https://github.com/slipknoo822-lang/crypto-trading-bot.git
cd crypto-trading-bot

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup config
cp .env.example .env
# Edit .env — masukkan API key Binance kamu

# 4. Run (paper mode by default)
python main.py
```

## Configuration (.env)

| Variable | Default | Description |
|----------|---------|-------------|
| `BINANCE_API_KEY` | - | API key dari Binance |
| `BINANCE_API_SECRET` | - | API secret |
| `TRADING_SYMBOL` | BTCUSDT | Trading pair |
| `TRADING_INTERVAL` | 1h | Candle interval |
| `TRADING_QUANTITY` | 0.001 | Order size |
| `TRADING_MODE` | paper | `paper` atau `live` |
| `STRATEGY` | combined | `rsi`, `macd`, `bollinger`, `combined` |
| `STOP_LOSS_PCT` | 2.0 | Stop loss percentage |
| `TAKE_PROFIT_PCT` | 4.0 | Take profit percentage |

## Strategies

### RSI (Relative Strength Index)
- BUY ketika RSI ≤ 30 (oversold)
- SELL ketika RSI ≥ 70 (overbought)

### MACD (Moving Average Convergence Divergence)
- BUY pada bullish crossover (MACD cross atas signal)
- SELL pada bearish crossover

### Bollinger Bands
- BUY ketika harga menyentuh lower band
- SELL ketika harga menyentuh upper band

### Combined (Default)
- Menjalankan ketiga strategy di atas
- Signal BUY/SELL jika 2 dari 3 strategy setuju (majority vote)

## ⚠️ Disclaimer

Bot ini untuk tujuan edukasi. Trading crypto memiliki risiko tinggi.
Selalu gunakan paper mode terlebih dahulu sebelum live trading.
Tidak ada jaminan profit.

## License

MIT
