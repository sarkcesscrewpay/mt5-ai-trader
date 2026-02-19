# AI-Powered MetaTrader 5 Trading System Architecture

## System Overview

This is a modular, production-ready trading automation system that connects to MetaTrader 5 using AI/ML for signal prediction with strict risk management and capital preservation focus.

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           TRADING SYSTEM ARCHITECTURE                                │
└─────────────────────────────────────────────────────────────────────────────────────┘

                                    ┌──────────────────┐
                                    │   USER INTERFACE │
                                    │  (CLI/Web/Admin) │
                                    └────────┬─────────┘
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                   CORE LAYER                                         │
│  ┌────────────────────────────────────────────────────────────────────────────────┐ │
│  │                        TRADING ORCHESTRATOR                                    │ │
│  │  • Coordinates all modules    • Manages execution flow    • State management │ │
│  └────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                             │
           ┌─────────────────────────────────┼─────────────────────────────────────┐
           │                                 │                                     │
           ▼                                 ▼                                     ▼
┌─────────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐
│   DATA LAYER       │      │   AI/ML LAYER      │      │   EXECUTION LAYER  │
│                     │      │                     │      │                     │
│ ┌─────────────────┐ │      │ ┌─────────────────┐ │      │ ┌─────────────────┐ │
│ │ Data Collection │ │      │ │ Feature Engine │ │      │ │ MT5 Execution   │ │
│ │ Module          │ │      │ │                 │ │      │ │ Bridge          │ │
│ │                 │ │      │ │ • RSI           │ │      │ │                 │ │
│ │ • MT5 Data API  │ │      │ │ • MACD          │ │      │ │ • Order Mgmt    │ │
│ │ • Historical    │ │      │ │ • EMA           │ │      │ │ • Position Mgmt │ │
│ │ • Real-time     │ │      │ │ • ATR           │ │      │ │ • Error Handle  │ │
│ │ • Symbol sync   │ │      │ │ • Price patterns│ │      │ │ • Slippage prot │ │
│ └────────┬────────┘ │      │ │ • Volume stats  │ │      │ └────────┬────────┘ │
│          │          │      │ └────────┬────────┘ │      │          │          │
│          ▼          │      │          │          │      │          ▼          │
│ ┌─────────────────┐ │      │          ▼          │      │ ┌─────────────────┐ │
│ │ Feature Eng.   │ │      │ ┌─────────────────┐ │      │ │ Risk Management │ │
│ │ Module          │ │      │ │ AI Model Module│ │      │ │ Engine          │ │
│ │                 │ │      │ │                │ │      │ │                 │ │
│ │ • Data cleaning │ │      │ │ • XGBoost/LSTM │ │      │ │ • Position sizing│ │
│ │ • Normalization │ │      │ │ • Signal pred.  │ │      │ │ • Stop-loss     │ │
│ │ • Label gen.   │ │      │ │ • Confidence    │ │      │ │ • Drawdown ctrl │ │
│ │ • Train/test    │ │      │ │ • Retraining    │ │      │ │ • Max trades    │ │
│ └─────────────────┘ │      │ └─────────────────┘ │      │ └─────────────────┘ │
└─────────────────────┘      └─────────────────────┘      └─────────────────────┘
           │                         │                              │
           │                         │                              │
           ▼                         ▼                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                SAFETY LAYER                                          │
│                                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Kill Switch  │  │ Capital Prot │  │ News Filter │  │ Time Filter │              │
│  │              │  │ Mode         │  │             │  │             │              │
│  │ • Emergency  │  │ • Max DD     │  │ • Volatility│  │ • Market    │              │
│  │   shutdown   │  │ • Auto-close │  │ • Sentiment │  │   hours     │              │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              PERSISTENCE & MONITORING                                │
│                                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐                  │
│  │ Logging Module   │  │ Performance      │  │ Backtesting     │                  │
│  │                  │  │ Tracking         │  │ Engine           │                  │
│  │ • Trade logs     │  │ • Sharpe ratio   │  │ • Historical     │                  │
│  │ • Signal logs    │  │ • Max drawdown   │  │   simulation     │                  │
│  │ • Error logs     │  │ • Win rate       │  │ • Strategy test  │                  │
│  │ • Audit trail    │  │ • Equity curve   │  │ • Walk-forward   │                  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘                  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Module Descriptions

### 1. Data Collection Module
**Purpose**: Fetch and manage market data from MT5

**Responsibilities**:
- Connect to MT5 terminal via MetaTrader5 Python package
- Fetch historical OHLC data (candles)
- Fetch real-time tick data
- Maintain data cache for efficiency
- Handle data gaps and reconnections

**Key Functions**:
- `get_historical_data(symbol, timeframe, count)`
- `get_real_time_data(symbol)`
- `sync_symbols()`
- `validate_data_quality()`

### 2. Feature Engineering Module
**Purpose**: Transform raw data into ML-ready features

**Responsibilities**:
- Calculate technical indicators (RSI, MACD, EMA, ATR)
- Generate price patterns and features
- Normalize/scale features
- Create target labels for ML training
- Handle missing data

**Indicators**:
- RSI (Relative Strength Index) - 14 periods
- MACD (12, 26, 9) - Signal line crossovers
- EMA (9, 21, 50) - Trend direction
- ATR - Volatility measurement
- Additional: Bollinger Bands, Stochastic, Volume

### 3. AI Model Module
**Purpose**: Generate trading signals using ML

**Responsibilities**:
- Train ML models on historical data
- Generate probability predictions
- Calculate confidence scores
- Support model retraining
- Ensemble multiple models

**Model Options**:
- XGBoost - Fast, interpretable, good for tabular data
- LightGBM - Efficient, handles large datasets
- LSTM - Captures temporal patterns
- Ensemble - Combine multiple models

**Output Format**:
```python
Signal {
    direction: BUY | SELL | HOLD
    probability: float  # 0.0 - 1.0
    confidence: float  # confidence score
    model_name: str
    features: dict
}
```

### 4. Strategy Logic Module
**Purpose**: Convert AI signals into actionable trade ideas

**Responsibilities**:
- Apply filter conditions to signals
- Manage trade entry/exit logic
- Handle multiple timeframe analysis
- Coordinate with risk engine

**Strategy Rules**:
- Minimum confidence threshold (e.g., 0.65)
- Direction alignment across timeframes
- Volatility filters
- News/time-based filters

### 5. Risk Management Engine
**Purpose**: Protect capital through strict controls

**Responsibilities**:
- Calculate position sizes
- Set stop-loss and take-profit levels
- Monitor daily drawdown
- Control maximum open trades
- Emergency shutdown triggers

**Risk Rules**:
- Max 1-2% risk per trade
- Fixed fractional position sizing
- ATR-based stop distances
- Max 5-10 open positions
- Daily max drawdown: 5%

### 6. MT5 Execution Bridge
**Purpose**: Execute trades through MT5 terminal

**Responsibilities**:
- Place market/limit orders
- Manage positions
- Handle order modifications
- Error handling and retries
- Slippage protection

**Order Types**:
- Market execution
- Limit orders with expiration
- Stop orders

### 7. Logging & Performance Tracking
**Purpose**: Comprehensive system monitoring

**Responsibilities**:
- Log all trades and signals
- Track performance metrics
- Generate equity curves
- Alert on anomalies

**Metrics**:
- Sharpe ratio
- Maximum drawdown
- Win rate
- Profit factor
- Average trade duration

### 8. Backtesting Engine
**Purpose**: Validate strategies on historical data

**Responsibilities**:
- Simulate historical trading
- Calculate performance metrics
- Avoid overfitting
- Walk-forward analysis

**Output**:
- Equity curve
- Drawdown chart
- Trade log
- Performance summary

### 9. Safety Features
**Purpose**: Prevent catastrophic losses

**Kill Switch**:
- Manual emergency stop
- Automatic triggers:
  - Daily drawdown exceeded
  - Consecutive losses limit
  - Connection lost

**Capital Protection Mode**:
- Reduce position sizes by 50% when in drawdown
- Stop trading after 5% daily loss

**News Volatility Filter**:
- Skip trading during high-impact news
- Increase stop distances during volatility

**Trading Hours Filter**:
- Avoid major market open/close
- Skip low-liquidity sessions

---

## Data Flow

```
1. COLLECTION          2. FEATURES           3. AI MODEL          4. STRATEGY
   ──────────            ────────             ─────────            ─────────
   MT5 API ──────►   Clean & Validate ─►   Predict ─────────►   Apply Filters
   Raw candles         Indicators            Probability         Confidence
   Tick data           Normalize              Direction           Risk Check
                       Features                                     Approval

5. RISK ENGINE        6. EXECUTION          7. MONITORING        8. FEEDBACK
   ───────────         ──────────            ───────────          ─────────
   Position Sizing     MT5 Order ─────►      Log Trade ──────►   Record Result
   Stop/TP Levels     Confirmation          Update Metrics        Retrain Model
   Drawdown Check     Position Open         Alert if Needed      Update Portfolio
```

---

## Configuration

```yaml
# trading_config.yaml

system:
  mode: paper_trading  # or live
  symbols: [EURUSD, GBPUSD, USDJPY]
  max_concurrent_trades: 5

data:
  timeframes: [M5, M15, H1]
  lookback_periods: 1000
  update_interval: 60  # seconds

ai_model:
  model_type: xgboost
  min_confidence: 0.65
  retrain_frequency: weekly
  features:
    - rsi
    - macd
    - ema
    - atr
    - volume

risk:
  max_risk_per_trade: 0.02  # 2%
  max_daily_drawdown: 0.05  # 5%
  max_open_positions: 5
  atr_multiplier_sl: 2.0
  atr_multiplier_tp: 4.0
  min_risk_reward: 1.5

execution:
  slippage_protection: true
  max_slippage_pips: 2
  order_retry_count: 3
  order_retry_delay: 2  # seconds

safety:
  kill_switch_enabled: true
  capital_protection_mode: true
  news_filter_enabled: true
  trading_hours_filter: true
  allowed_sessions: [London, NewYork]
```

---

## Important Disclaimers

⚠️ **CAPITAL PRESERVATION PRIORITY**: This system is designed to minimize drawdown and protect capital. It does NOT guarantee profits.

⚠️ **BACKTESTED RESULTS**: Past performance does not guarantee future results. Backtest results often overestimate real-world performance due to overfitting and slippage assumptions.

⚠️ **LIVE TRADING RISKS**: Always use paper trading first. Start with small capital. Monitor system behavior closely.

⚠️ **NO ZERO-RISK GUARANTEE**: Trading financial markets carries inherent risks. Only trade with money you can afford to lose.
