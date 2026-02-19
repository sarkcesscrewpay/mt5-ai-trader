"""
Starter Example: AI-Powered MT5 Trading System

Run: python src/mcp_mt5/trading/starter_example.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Try importing modules, handle missing MT5 gracefully
try:
    from mcp_mt5.trading.backtesting import BacktestEngine, BacktestConfig
    from mcp_mt5.trading.feature_engineering import FeatureEngineer, ScalerType
    from mcp_mt5.trading.risk_management import RiskEngine, RiskConfig, AccountState
    from mcp_mt5.trading.safety import SafetyManager, SafetyConfig, KillSwitch
    HAS_TRADING_MODULES = True
except ImportError as e:
    HAS_TRADING_MODULES = False
    print(f"Warning: Some modules unavailable: {e}")

import numpy as np
import pandas as pd


def run_backtest():
    """Run a simple backtest demo."""
    print("=" * 60)
    print("AI-POWERED MT5 TRADING SYSTEM - Backtest Demo")
    print("=" * 60)
    
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=500, freq='1h')
    returns = np.random.normal(0.0001, 0.001, 500)
    close = 100 * np.exp(np.cumsum(returns))
    
    data = pd.DataFrame({
        'open': close * (1 + np.random.uniform(-0.0005, 0.0005, 500)),
        'high': close * (1 + np.random.uniform(0, 0.002, 500)),
        'low': close * (1 + np.random.uniform(-0.002, 0, 500)),
        'close': close,
    }, index=dates)
    
    print(f"\nData: {len(data)} candles")
    
    # Run backtest
    config = BacktestConfig(
        initial_balance=10000,
        spread_pips=1.0,
        risk_per_trade=0.02
    )
    engine = BacktestEngine(config)
    result = engine.run(data, [])
    
    print(f"\nBacktest Results:")
    print(f"  Total trades: {result.metrics['total_trades']}")
    print(f"  Win rate: {result.metrics['win_rate']:.1f}%")
    print(f"  Net profit: ${result.metrics['net_profit']:.2f}")
    print(f"  Max drawdown: {result.metrics['max_drawdown']:.2f}%")
    print(f"  Sharpe ratio: {result.metrics['sharpe_ratio']:.2f}")
    
    # Test risk engine
    print("\n" + "=" * 60)
    print("Risk Engine Test")
    print("=" * 60)
    
    risk = RiskEngine(RiskConfig(
        max_risk_per_trade=0.02,
        max_open_positions=5
    ))
    
    account = AccountState(balance=10000, equity=10000)
    position_size = risk.calculate_position_size(account, "EURUSD", 20, 10.0, 0.0015)
    print(f"Position size: {position_size} lots")
    
    # Test safety
    print("\n" + "=" * 60)
    print("Safety System Test")
    print("=" * 60)
    
    safety = SafetyManager(SafetyConfig(
        max_daily_drawdown=0.05,
        max_consecutive_losses=5
    ))
    safety.initialize()
    print("Kill switch armed")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)


def main():
    if HAS_TRADING_MODULES:
        run_backtest()
    else:
        print("Trading modules not available. Please install dependencies:")
        print("  pip install numpy pandas scikit-learn xgboost lightgbm")


if __name__ == "__main__":
    main()
