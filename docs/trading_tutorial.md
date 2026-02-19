# Complete Beginner's Guide to AI Trading

## Table of Contents
1. [What is Trading?](#what-is-trading)
2. [How the AI Trading System Works](#how-the-ai-trading-system-works)
3. [Prerequisites](#prerequisites)
4. [Getting Started](#getting-started)
5. [Understanding the Dashboard](#understanding-the-dashboard)
6. [Running Your First Backtest](#running-your-first-backtest)
7. [Going Live](#going-live)
8. [Important Warnings](#important-warnings)

---

## What is Trading?

### Basic Concept
Trading means buying and selling financial instruments (like currencies, stocks, or commodities) to make a profit. 

### Example: Currency Trading (Forex)
```
You have $1,000
- You "buy" EURUSD at 1.0850 (meaning you think Euro will go up vs Dollar)
- Price moves to 1.0900
- You sell and earn: $46.08 profit
- Your total: $1,046.08
```

### Key Terms
| Term | Meaning |
|------|---------|
| **BUY (Long)** | You expect price to go UP |
| **SELL (Short)** | You expect price to go DOWN |
| **Stop Loss (SL)** | Auto-sell if price goes AGAINST you (limits loss) |
| **Take Profit (TP)** | Auto-sell if price goes FOR you (locks profit) |
| **Lot/Volume** | How much you trade (0.01 = micro lot = ~$1,000) |
| **P/L** | Profit or Loss |

---

## How the AI Trading System Works

This is an **automated trading system** that:

```
┌─────────────────────────────────────────────────────────────────┐
│                     AI TRADING SYSTEM FLOW                       │
└─────────────────────────────────────────────────────────────────┘

   ┌──────────────┐
   │ 1. MT5 Data  │ ← Gets historical price data from MetaTrader
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │2. Indicators │ ← Calculates RSI, MACD, EMA, ATR
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ 3. AI Model  │ ← Machine learning predicts price direction
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │4. Risk Check │ ← Checks: Is risk too high? Drawdown limit?
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │5. Execute    │ ← Places order in MT5 (or simulates)
   └──────────────┘
```

### Modules Explanation:

| Module | What it Does |
|--------|--------------|
| **Data Collection** | Fetches price history from MT5 |
| **Feature Engineering** | Calculates technical indicators |
| **AI Model** | Predicts if price will go UP or DOWN |
| **Risk Management** | Calculates position size, checks limits |
| **Execution** | Places the actual trade |
| **Safety** | Kill switch, news filter, time filter |

---

## Prerequisites

### Required:
1. **Computer** - Windows 10/11 recommended
2. **Internet** - For connecting to broker
3. **MetaTrader 5 (MT5)** - Free trading platform

### For Live Trading:
1. **Trading Account** - Open with a broker (IC Markets, OANDA, etc.)
2. **MetaTrader5 Python package** - `pip install MetaTrader5`
3. **Capital** - Start with small amount ($100-1000)

---

## Getting Started

### Step 1: Install Dependencies
```bash
cd c:\Users\sarkc\Desktop\mcp-metatrader5-server-main
pip install -r requirements.txt
pip install streamlit
```

### Step 2: Run Demo Dashboard
```bash
python -m streamlit run src/mcp_mt5/trading/dashboard.py --server.headless true --browser.gatherUsageStats false
```
Then open: **http://localhost:8501**

### Step 3: Understand the Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  🤖 MT5 AI Trading Dashboard                                 │
├─────────────────────────────────────────────────────────────┤
│  [Dashboard] [Positions] [Risk Settings] [Logs] [Backtest]  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Balance: $10,000   Equity: $10,250   Positions: 2          │
│                                                              │
│  Trading Mode: [Paper Trading ▼]                            │
│  Symbols: [✓ EURUSD ✓ GBPUSD ✓ USDJPY]                     │
│  [▶️ Start Trading]                                         │
│                                                              │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  📊 Market Overview                                          │
│  ┌────────┬────────┬────────┬────────┬──────────────────┐  │
│  │Symbol  │Bid     │Ask     │Change  │Signal            │  │
│  │EURUSD  │1.0852  │1.0854  │+0.12%  │🟢 BUY            │  │
│  │GBPUSD  │1.2654  │1.2656  │-0.08%  │🔴 SELL           │  │
│  └────────┴────────┴────────┴────────┴──────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Understanding the Dashboard

### 1. Dashboard Tab
- **Balance**: Your account money
- **Equity**: Balance + open positions P/L
- **Trading Mode**: 
  - *Paper Trading* = Simulated (no real money)
  - *Live Trading* = Real money
- **Start/Stop Trading**: Activates the AI bot

### 2. Positions Tab
Shows your open trades:
```
Ticket | Symbol | Type | Volume | Entry | Current | P/L  | SL   | TP
12345  | EURUSD | BUY | 0.10   | 1.0825| 1.0852  |+$27  | 1.080| 1.090
```

### 3. Risk Settings Tab ⚠️ VERY IMPORTANT
Configure how safely the bot trades:

| Setting | Recommended | Meaning |
|---------|-------------|---------|
| Max Risk per Trade | 2% | Lose max $20 per $1000 |
| Max Positions | 5 | Don't open more than 5 trades |
| ATR Multiplier (SL) | 2.0 | Stop loss based on volatility |
| Max Drawdown | 5% | Stop trading if lose 5% in a day |
| Kill Switch | ON | Emergency stop button |
| Capital Protection | ON | Prevents large losses |

### 4. Backtest Tab
Test the AI on historical data to see how it would have performed.

---

## Running Your First Backtest

### Why Backtest?
- Test the AI without risking real money
- See if the strategy is profitable
- Understand risk/reward

### How to Backtest:
1. Go to **Backtest** tab
2. Select symbol: `EURUSD`
3. Select timeframe: `H1` (1 hour candles)
4. Set date range
5. Set Initial Balance: `$10,000`
6. Click **Run Backtest**

### Results to Look For:
| Metric | Good | Bad |
|--------|------|-----|
| Win Rate | >50% | <40% |
| Max Drawdown | <10% | >20% |
| Risk:Reward | >1.5 | <1.0 |
| Sharpe Ratio | >1.0 | <0.5 |

---

## Going Live (Real Money)

### ⚠️ WARNING: HIGH RISK
Trading with real money can result in **COMPLETE LOSS OF CAPITAL**.

### Steps to Go Live:

1. **Open MT5 Account**
   - Choose a regulated broker (IC Markets, OANDA, etc.)
   - Complete verification
   - Deposit money (start with $100-500)

2. **Install MT5**
   - Download from your broker
   - Login with your account

3. **Connect Python to MT5**
   ```bash
   pip install MetaTrader5
   ```

4. **Update Config**
   Edit `config/trading_config.yaml`:
   ```yaml
   trading:
     mode: live  # Changed from paper
     symbols:
       - EURUSD
   ```

5. **Start Trading**
   - Set Risk per Trade to **1%** (conservative)
   - Enable Kill Switch
   - Click Start Trading

---

## Important Warnings

### 🚨 RISK DISCLAIMER
```
Trading financial instruments carries HIGH RISK and may not 
be suitable for all investors. You can lose ALL your capital.

Past performance does NOT guarantee future results.
This software is for EDUCATIONAL purposes.
```

### Safety Features Built-In:
1. **Max 2% risk per trade** - Never lose more than 2% on one trade
2. **5% daily drawdown limit** - Stop trading if lose 5% in a day
3. **Kill Switch** - Emergency stop button
4. **Capital Protection** - Reduces position size when losing

### Recommended for Beginners:
1. **Start with Paper Trading** for 1-3 months
2. **Only use money you can afford to lose**
3. **Keep risk at 1-2% maximum**
4. **Never trade during news events**
5. **Learn about risk management first**

---

## Next Steps

1. **Explore the Dashboard** - Try each tab
2. **Run Backtests** - See how the AI performs
3. **Learn Trading Basics** - See recommended resources below
4. **Practice with Demo Account** - Use broker's demo account
5. **Start Small** - When going live, start with minimum position

### Recommended Learning Resources:
- BabyPips.com - Free Forex trading course
- Investopedia - Trading terminology
- TradingSim - Practice trading without risk

---

## Quick Reference Commands

```bash
# Run dashboard
python -m streamlit run src/mcp_mt5/trading/dashboard.py

# Run demo trading
python src/mcp_mt5/trading/starter_example.py

# Run live trading (requires MT5)
python src/mcp_mt5/trading/live_trading.py

# Run backtest
python src/mcp_mt5/trading/backtesting.py
```
