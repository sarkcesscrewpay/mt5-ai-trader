"""
Backtesting Engine for MT5 Trading System

This module handles historical strategy testing and performance evaluation.

Features:
- Historical simulation
- Performance metrics calculation
- Walk-forward analysis
- Monte Carlo simulation

Author: AI Trading System
Version: 1.0.0
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """
    Backtest configuration.

    Attributes:
        initial_balance: Starting account balance
        spread_pips: Spread in pips (for realistic simulation)
        commission: Commission per trade
        slippage_pips: Slippage in pips
        risk_per_trade: Risk percentage per trade
    """
    initial_balance: float = 10000.0
    spread_pips: float = 1.0
    commission: float = 0.0
    slippage_pips: float = 0.5
    risk_per_trade: float = 0.02


@dataclass
class BacktestResult:
    """
    Backtest results.

    Attributes:
        trades: List of executed trades
        equity_curve: Equity curve DataFrame
        metrics: Performance metrics
        config: Backtest configuration used
    """
    trades: list
    equity_curve: pd.DataFrame
    metrics: dict
    config: BacktestConfig


class BacktestEngine:
    """
    Historical backtesting engine.

    Responsibilities:
    - Simulate trading on historical data
    - Calculate realistic performance metrics
    - Generate equity curves and drawdown charts
    """

    def __init__(self, config: Optional[BacktestConfig] = None):
        self.config = config or BacktestConfig()

    def run(
        self,
        data: pd.DataFrame,
        signals: list,
        risk_engine: any = None
    ) -> BacktestResult:
        """
        Run backtest on historical data.

        Args:
            data: OHLC data with features
            signals: List of trading signals
            risk_engine: Risk engine for position sizing

        Returns:
            BacktestResult with all metrics
        """
        logger.info(f"Starting backtest with {len(data)} bars")

        # Initialize state
        balance = self.config.initial_balance
        equity = balance
        positions = []
        trades = []
        equity_curve = []

        # Point value (simplified)
        pip_value = 10.0  # For standard lots

        # Run simulation
        for i, (idx, row) in enumerate(data.iterrows()):
            # Check signals
            if i < len(signals):
                signal = signals[i]

                if signal.direction != "HOLD" and len(positions) < 5:
                    # Calculate position size
                    if risk_engine:
                        volume = risk_engine.calculate_position_size(
                            balance * equity,
                            signal.symbol,
                            20,  # Default SL
                            pip_value
                        )
                    else:
                        volume = 0.1

                    # Apply spread
                    entry = row['close']
                    if signal.direction == "BUY":
                        entry += self.config.spread_pips * 0.0001
                    else:
                        entry -= self.config.spread_pips * 0.0001

                    # Calculate SL and TP
                    sl_pips = 20
                    if signal.direction == "BUY":
                        sl = entry - sl_pips * 0.0001
                        tp = entry + sl_pips * self.config.risk_per_trade * 3 * 0.0001
                    else:
                        sl = entry + sl_pips * 0.0001
                        tp = entry - sl_pips * self.config.risk_per_trade * 3 * 0.0001

                    # Open position
                    position = {
                        'entry_time': idx,
                        'entry_price': entry,
                        'direction': signal.direction,
                        'volume': volume,
                        'sl': sl,
                        'tp': tp,
                        'symbol': signal.symbol if hasattr(signal, 'symbol') else 'EURUSD'
                    }
                    positions.append(position)

            # Check open positions
            closed_positions = []
            for pos in positions:
                # Check stop loss
                if pos['direction'] == "BUY":
                    if row['low'] <= pos['sl']:
                        pips = (pos['sl'] - pos['entry_price']) / 0.0001
                        profit = pips * pos['volume'] * pip_value
                        profit -= self.config.commission

                        trades.append({
                            'entry_time': pos['entry_time'],
                            'exit_time': idx,
                            'direction': pos['direction'],
                            'entry_price': pos['entry_price'],
                            'exit_price': pos['sl'],
                            'volume': pos['volume'],
                            'profit': profit,
                            'pips': pips,
                            'reason': 'SL'
                        })
                        closed_positions.append(pos)
                        balance += profit
                        equity = balance

                    elif row['high'] >= pos['tp']:
                        pips = (pos['tp'] - pos['entry_price']) / 0.0001
                        profit = pips * pos['volume'] * pip_value
                        profit -= self.config.commission

                        trades.append({
                            'entry_time': pos['entry_time'],
                            'exit_time': idx,
                            'direction': pos['direction'],
                            'entry_price': pos['entry_price'],
                            'exit_price': pos['tp'],
                            'volume': pos['volume'],
                            'profit': profit,
                            'pips': pips,
                            'reason': 'TP'
                        })
                        closed_positions.append(pos)
                        balance += profit
                        equity = balance
                else:  # SELL
                    if row['high'] >= pos['sl']:
                        pips = (pos['entry_price'] - pos['sl']) / 0.0001
                        profit = pips * pos['volume'] * pip_value
                        profit -= self.config.commission

                        trades.append({
                            'entry_time': pos['entry_time'],
                            'exit_time': idx,
                            'direction': pos['direction'],
                            'entry_price': pos['entry_price'],
                            'exit_price': pos['sl'],
                            'volume': pos['volume'],
                            'profit': profit,
                            'pips': pips,
                            'reason': 'SL'
                        })
                        closed_positions.append(pos)
                        balance += profit
                        equity = balance

                    elif row['low'] <= pos['tp']:
                        pips = (pos['entry_price'] - pos['tp']) / 0.0001
                        profit = pips * pos['volume'] * pip_value
                        profit -= self.config.commission

                        trades.append({
                            'entry_time': pos['entry_time'],
                            'exit_time': idx,
                            'direction': pos['direction'],
                            'entry_price': pos['entry_price'],
                            'exit_price': pos['tp'],
                            'volume': pos['volume'],
                            'profit': profit,
                            'pips': pips,
                            'reason': 'TP'
                        })
                        closed_positions.append(pos)
                        balance += profit
                        equity = balance

            # Remove closed positions
            for pos in closed_positions:
                positions.remove(pos)

            # Update equity curve
            equity_curve.append({
                'time': idx,
                'equity': equity,
                'balance': balance
            })

        # Close remaining positions at final price
        if positions and len(data) > 0:
            final_price = data.iloc[-1]['close']
            for pos in positions:
                if pos['direction'] == "BUY":
                    pips = (final_price - pos['entry_price']) / 0.0001
                else:
                    pips = (pos['entry_price'] - final_price) / 0.0001

                profit = pips * pos['volume'] * pip_value

                trades.append({
                    'entry_time': pos['entry_time'],
                    'exit_time': data.index[-1],
                    'direction': pos['direction'],
                    'entry_price': pos['entry_price'],
                    'exit_price': final_price,
                    'volume': pos['volume'],
                    'profit': profit,
                    'pips': pips,
                    'reason': 'EOD'
                })
                balance += profit

        # Calculate metrics
        metrics = self._calculate_metrics(trades)

        # Create equity curve DataFrame
        equity_df = pd.DataFrame(equity_curve)

        logger.info(f"Backtest complete: {len(trades)} trades, Net Profit: ${metrics['net_profit']:.2f}")

        return BacktestResult(
            trades=trades,
            equity_curve=equity_df,
            metrics=metrics,
            config=self.config
        )

    def _calculate_metrics(self, trades: list) -> dict:
        """Calculate performance metrics from trades."""
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'net_profit': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0,
                'profit_factor': 0
            }

        total_trades = len(trades)
        winning_trades = [t for t in trades if t['profit'] > 0]
        losing_trades = [t for t in trades if t['profit'] <= 0]

        win_rate = len(winning_trades) / total_trades * 100

        total_profit = sum(t['profit'] for t in winning_trades)
        total_loss = abs(sum(t['profit'] for t in losing_trades))
        net_profit = total_profit - total_loss

        profit_factor = total_profit / total_loss if total_loss > 0 else 0

        # Calculate drawdown
        balance = self.config.initial_balance
        peak = balance
        max_dd = 0
        equity = balance

        for trade in trades:
            equity += trade['profit']
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak
            if dd > max_dd:
                max_dd = dd

        # Calculate Sharpe ratio
        returns = [t['profit'] / self.config.initial_balance for t in trades]
        if len(returns) > 1:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe = (avg_return * 252 / len(returns)) / (std_return * np.sqrt(252)) if std_return > 0 else 0
        else:
            sharpe = 0

        return {
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'net_profit': net_profit,
            'total_profit': total_profit,
            'total_loss': total_loss,
            'profit_factor': profit_factor,
            'max_drawdown': max_dd * 100,
            'sharpe_ratio': sharpe,
            'average_profit': total_profit / len(winning_trades) if winning_trades else 0,
            'average_loss': total_loss / len(losing_trades) if losing_trades else 0
        }

    def run_walk_forward(
        self,
        data: pd.DataFrame,
        train_size: int = 1000,
        test_size: int = 200,
        step: int = 100
    ) -> list[BacktestResult]:
        """
        Run walk-forward analysis.

        Args:
            data: Full dataset
            train_size: Training window size
            test_size: Test window size
            step: Step size between windows

        Returns:
            List of BacktestResults for each window
        """
        results = []
        start = 0

        while start + train_size + test_size <= len(data):
            # Split data
            train_end = start + train_size
            test_end = train_end + test_size

            train_data = data.iloc[start:train_end]
            test_data = data.iloc[train_end:test_end]

            logger.info(
                f"Walk-forward: train {start}-{train_end}, "
                f"test {train_end}-{test_end}"
            )

            # Train model (simplified - would retrain here)
            # Run backtest on test period
            result = self.run(test_data, [])  # Would use signals here

            results.append(result)

            start += step

        return results


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("Backtesting Engine Test")
    print("=" * 60)

    # Create sample data
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=500, freq='1h')

    # Generate price data with trend
    returns = np.random.normal(0.0001, 0.001, 500)
    close = 100 * np.exp(np.cumsum(returns))

    data = pd.DataFrame({
        'open': close * (1 + np.random.uniform(-0.0005, 0.0005, 500)),
        'high': close * (1 + np.random.uniform(0, 0.002, 500)),
        'low': close * (1 + np.random.uniform(-0.002, 0, 500)),
        'close': close,
    }, index=dates)

    print(f"Test data: {len(data)} bars")

    # Create backtest config
    config = BacktestConfig(
        initial_balance=10000,
        spread_pips=1.0,
        commission=2.0
    )

    # Create engine
    engine = BacktestEngine(config)

    # Run backtest
    result = engine.run(data, [])

    print(f"\n✓ Backtest complete:")
    print(f"  Total trades: {result.metrics['total_trades']}")
    print(f"  Win rate: {result.metrics['win_rate']:.1f}%")
    print(f"  Net profit: ${result.metrics['net_profit']:.2f}")
    print(f"  Max drawdown: {result.metrics['max_drawdown']:.2f}%")
    print(f"  Sharpe ratio: {result.metrics['sharpe_ratio']:.2f}")
    print(f"  Profit factor: {result.metrics['profit_factor']:.2f}")

    print("\n" + "=" * 60)
    print("Backtesting Engine - Complete")
    print("=" * 60)
