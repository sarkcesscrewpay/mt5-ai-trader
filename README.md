# 🤖 AI-Powered MT5 Trading System

An automated trading system with AI/ML signal prediction, connected to MetaTrader 5.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## ⚠️ Risk Warning

**Trading financial instruments carries HIGH RISK and may result in complete loss of capital.**
This software is for EDUCATIONAL purposes. Past performance does NOT guarantee future results.
Never trade with money you cannot afford to lose.

## Features

- 📊 **AI Signal Prediction** - Machine learning models predict price direction
- 📈 **Technical Indicators** - RSI, MACD, EMA, ATR
- 🛡️ **Risk Management** - Max 2% risk per trade, daily drawdown limits
- 🔒 **Safety Features** - Kill switch, news filter, trading hours filter
- 📉 **Backtesting** - Test strategies on historical data
- 🎯 **MT5 Integration** - Connect to MetaTrader 5

## Dashboard

Run the web dashboard:

```bash
pip install streamlit
streamlit run src/mcp_mt5/trading/dashboard.py
```

Then open: http://localhost:8501

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Demo (No MT5 Required)

```bash
python src/mcp_mt5/trading/starter_example.py
```

### 3. Run Dashboard

```bash
streamlit run src/mcp_mt5/trading/dashboard.py
```

### 4. Run Backtest

```bash
python src/mcp_mt5/trading/backtesting.py
```

### 5. Go Live (Requires MT5)

```bash
pip install MetaTrader5
python src/mcp_mt5/trading/live_trading.py
```

## Project Structure

```
mcp-metatrader5-server/
├── src/mcp_mt5/trading/
│   ├── data_collection.py      # MT5 data fetching
│   ├── feature_engineering.py  # Technical indicators
│   ├── ai_model.py            # ML models
│   ├── strategy.py            # Trading logic
│   ├── risk_management.py      # Risk controls
│   ├── execution.py           # Order execution
│   ├── safety.py              # Kill switch, filters
│   ├── backtesting.py         # Historical testing
│   ├── dashboard.py           # Web UI
│   └── live_trading.py        # Live execution
├── config/
│   └── trading_config.yaml    # Configuration
├── docs/
│   ├── trading_tutorial.md    # Beginner's guide
│   └── trading_system_architecture.md
└── requirements.txt
```

## Configuration

Edit `config/trading_config.yaml`:

```yaml
trading:
  mode: paper  # or 'live'
  symbols:
    - EURUSD
    - GBPUSD
  risk:
    max_risk_per_trade: 2.0
    max_positions: 5
    max_daily_drawdown: 5.0

ai:
  model_type: xgboost
  min_confidence: 0.6
```

## Risk Management

| Setting | Default | Description |
|---------|---------|-------------|
| Max Risk/Trade | 2% | Maximum loss per trade |
| Max Positions | 5 | Simultaneous open trades |
| Daily Drawdown | 5% | Stop trading if exceeded |
| ATR Multiplier SL | 2.0 | Stop loss based on volatility |
| Min Risk:Reward | 1.5 | Minimum profit vs loss ratio |

## Documentation

- [Trading Tutorial](docs/trading_tutorial.md) - Beginner's guide
- [System Architecture](docs/trading_system_architecture.md) - Technical details
- [Deployment Guide](docs/deployment_guide.md) - VPS & Docker setup

## Deployment

### Streamlit Cloud

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Set:
   - Main file: `src/mcp_mt5/trading/dashboard.py`
   - Requirements: `requirements.txt`

### Docker

```bash
docker build -t mt5-ai-trader .
docker run -p 8501:8501 mt5-ai-trader
```

## Tech Stack

- **Language**: Python 3.10+
- **ML**: XGBoost, LightGBM, scikit-learn
- **Trading**: MetaTrader5
- **Dashboard**: Streamlit
- **Data**: Pandas, NumPy

## Disclaimer

This software is provided "AS IS" without warranty of any kind.
Use at your own risk. The authors are not responsible for any financial losses.
Always test thoroughly with paper trading before using real money.

## License

MIT License - See LICENSE file for details
