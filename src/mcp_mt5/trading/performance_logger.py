"""
Performance Logger and Tracking Module

This module handles comprehensive logging, performance metrics,
and analytics for the trading system.

Features:
- Trade logging
- Performance metrics calculation
- Equity curve tracking
- Alert generation

Author: AI Trading System
Version: 1.0.0
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# Use a different logger name to avoid conflicts
logger = __import__("logging").getLogger(__name__)


@dataclass
class TradeRecord:
    """
.

    Attributes:
        ticket: Order/ticket number
        symbol: Trading symbol
        direction: BUY or SELL
        volume: Position size
        entry_price: Entry price
        exit_price: Exit price
        stop_loss: Stop loss price
        take_profit: Take profit price
        entry_time: Entry datetime
        exit_time: Exit datetime
        profit: Profit/loss in account currency
        pips: Profit/loss in pips
        status: OPEN or CLOSED
    """
    ticket: Optional[int]
    symbol: str
    direction: str
    volume: float
    entry_price: float
    exit_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    entry_time: datetime
    exit_time: Optional[datetime]
    profit: float = 0.0
    pips: float = 0.0
    status: str = "OPEN"
    comment: str = ""


@dataclass
class PerformanceMetrics:
    """
    Performance metrics summary.
    """
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_profit: float = 0.0
    total_loss: float = 0.0
    net_profit: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    profit_factor: float = 0.0
    average_win: float = 0.0
    average_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    average_holding_time: float = 0.0


class TradingLogger:
    """
    Comprehensive trading logger and performance tracker.
    """

    def __init__(
        self,
        log_dir: str = "./logs",
        account_balance: float = 10000.0
    ):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.account_balance = account_balance
        self.initial_balance = account_balance
        self.trades: list[TradeRecord] = []
        self.equity_curve: list[dict] = []

    def log_trade_open(
        self,
        symbol: str,
        direction: str,
        volume: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        ticket: Optional[int] = None,
        comment: str = ""
    ) -> TradeRecord:
        """Log a new trade opening."""
        trade = TradeRecord(
            ticket=ticket,
            symbol=symbol,
            direction=direction,
            volume=volume,
            entry_price=entry_price,
            exit_price=None,
            stop_loss=stop_loss,
            take_profit=take_profit,
            entry_time=datetime.now(),
            exit_time=None,
            status="OPEN",
            comment=comment
        )

        self.trades.append(trade)
        logger.info(
            f"TRADE OPEN: {direction} {volume} {symbol} @ {entry_price}, "
            f"SL: {stop_loss}, TP: {take_profit}, Ticket: {ticket}"
        )
        return trade

    def log_trade_close(
        self,
        ticket: int,
        exit_price: float,
        profit: float,
        pips: float
    ) -> Optional[TradeRecord]:
        """Log a trade closing."""
        for trade in self.trades:
            if trade.ticket == ticket and trade.status == "OPEN":
                trade.exit_price = exit_price
                trade.exit_time = datetime.now()
                trade.profit = profit
                trade.pips = pips
                trade.status = "CLOSED"
                logger.info(
                    f"TRADE CLOSE: {trade.symbol} @ {exit_price}, "
                    f"Profit: {profit:.2f}, Pips: {pips:.1f}"
                )
                return trade
        logger.warning(f"Trade not found for ticket: {ticket}")
        return None

    def log_signal(
        self,
        symbol: str,
        signal_type: str,
        confidence: float,
        reason: str = ""
    ):
        """Log trading signal."""
        logger.info(
            f"SIGNAL: {symbol} {signal_type} (confidence: {confidence:.2f}) {reason}"
        )

    def log_error(self, error: str, details: str = ""):
        """Log error message."""
        logger.error(f"ERROR: {error} - {details}")

    def log_alert(self, alert_type: str, message: str):
        """Log alert."""
        logger.warning(f"ALERT [{alert_type}]: {message}")

    def calculate_metrics(self) -> PerformanceMetrics:
        """Calculate performance metrics from closed trades."""
        closed_trades = [t for t in self.trades if t.status == "CLOSED"]

        if not closed_trades:
            return PerformanceMetrics()

        total_trades = len(closed_trades)
        winning_trades_list = [t for t in closed_trades if t.profit > 0]
        losing_trades_list = [t for t in closed_trades if t.profit <= 0]

        win_rate = len(winning_trades_list) / total_trades if total_trades > 0 else 0

        total_profit_val = sum(t.profit for t in winning_trades_list)
        total_loss_val = abs(sum(t.profit for t in losing_trades_list))
        net_profit = total_profit_val - total_loss_val

        average_win = total_profit_val / len(winning_trades_list) if winning_trades_list else 0
        average_loss = total_loss_val / len(losing_trades_list) if losing_trades_list else 0

        largest_win = max(t.profit for t in winning_trades_list) if winning_trades_list else 0
        largest_loss = min(t.profit for t in losing_trades_list) if losing_trades_list else 0

        profit_factor = total_profit_val / total_loss_val if total_loss_val > 0 else 0
        max_drawdown = self._calculate_max_drawdown()
        sharpe_ratio = self._calculate_sharpe_ratio()

        holding_times = [
            (t.exit_time - t.entry_time).total_seconds() / 3600
            for t in closed_trades
            if t.exit_time and t.entry_time
        ]
        avg_holding = sum(holding_times) / len(holding_times) if holding_times else 0

        return PerformanceMetrics(
            total_trades=total_trades,
            winning_trades=len(winning_trades_list),
            losing_trades=len(losing_trades_list),
            win_rate=win_rate * 100,
            total_profit=total_profit_val,
            total_loss=total_loss_val,
            net_profit=net_profit,
            max_drawdown=max_drawdown * 100,
            sharpe_ratio=sharpe_ratio,
            profit_factor=profit_factor,
            average_win=average_win,
            average_loss=average_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            average_holding_time=avg_holding
        )

    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown from equity curve."""
        if not self.equity_curve:
            return 0.0

        equity = [e['equity'] for e in self.equity_curve]
        peak = equity[0]
        max_dd = 0.0

        for value in equity:
            if value > peak:
                peak = value
            dd = (peak - value) / peak
            if dd > max_dd:
                max_dd = dd

        return max_dd

    def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio from closed trades."""
        closed_trades = [t for t in self.trades if t.status == "CLOSED"]
        if len(closed_trades) < 2:
            return 0.0

        returns = [t.profit / self.account_balance for t in closed_trades]
        if not returns:
            return 0.0

        avg_return = np.mean(returns)
        std_return = np.std(returns)

        if std_return == 0:
            return 0.0

        return (avg_return - risk_free_rate / 252) / std_return * np.sqrt(252)

    def update_equity(self, equity: float):
        """Update equity curve."""
        self.equity_curve.append({
            'timestamp': datetime.now(),
            'equity': equity,
            'balance': self.account_balance
        })

    def get_equity_curve_df(self) -> pd.DataFrame:
        """Get equity curve as DataFrame."""
        if not self.equity_curve:
            return pd.DataFrame()

        return pd.DataFrame(self.equity_curve)

    def save_trades(self, filename: str = "trades.json"):
        """Save trades to JSON file."""
        filepath = self.log_dir / filename

        trades_data = []
        for trade in self.trades:
            trades_data.append({
                'ticket': trade.ticket,
                'symbol': trade.symbol,
                'direction': trade.direction,
                'volume': trade.volume,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'stop_loss': trade.stop_loss,
                'take_profit': trade.take_profit,
                'entry_time': trade.entry_time.isoformat(),
                'exit_time': trade.exit_time.isoformat() if trade.exit_time else None,
                'profit': trade.profit,
                'pips': trade.pips,
                'status': trade.status,
                'comment': trade.comment
            })

        with open(filepath, 'w') as f:
            json.dump(trades_data, f, indent=2)

        logger.info(f"Trades saved to {filepath}")

    def get_summary(self) -> str:
        """Get performance summary string."""
        metrics = self.calculate_metrics()

        summary = f"""
╔══════════════════════════════════════════════════════════════╗
║                   TRADING PERFORMANCE SUMMARY                 ║
╠══════════════════════════════════════════════════════════════╣
║  Total Trades:        {metrics.total_trades:>6}                               ║
║  Winning Trades:     {metrics.winning_trades:>6}  ({metrics.win_rate:>5.1f}%)              ║
║  Losing Trades:      {metrics.losing_trades:>6}                               ║
╠══════════════════════════════════════════════════════════════╣
║  Net Profit:         ${metrics.net_profit:>10.2f}                            ║
║  Total Profit:       ${metrics.total_profit:>10.2f}                            ║
║  Total Loss:         ${metrics.total_loss:>10.2f}                            ║
║  Profit Factor:      {metrics.profit_factor:>10.2f}                            ║
╠══════════════════════════════════════════════════════════════╣
║  Max Drawdown:       {metrics.max_drawdown:>10.2f}%                           ║
║  Sharpe Ratio:       {metrics.sharpe_ratio:>10.2f}                            ║
╠══════════════════════════════════════════════════════════════╣
║  Average Win:        ${metrics.average_win:>10.2f}                            ║
║  Average Loss:       ${metrics.average_loss:>10.2f}                            ║
║  Largest Win:        ${metrics.largest_win:>10.2f}                            ║
║  Largest Loss:       ${metrics.largest_loss:>10.2f}                            ║
║  Avg Holding Time:   {metrics.average_holding_time:>10.1f} hours                    ║
╚══════════════════════════════════════════════════════════════╝
"""
        return summary


if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("Trading Logger Test")
    print("=" * 60)

    logger_obj = TradingLogger(log_dir="./temp_logs", account_balance=10000)

    logger_obj.log_trade_open(
        symbol="EURUSD",
        direction="BUY",
        volume=0.1,
        entry_price=1.1000,
        stop_loss=1.0950,
        take_profit=1.1100,
        ticket=12345
    )

    logger_obj.log_trade_close(
        ticket=12345,
        exit_price=1.1050,
        profit=50.0,
        pips=50.0
    )

    metrics = logger_obj.calculate_metrics()
    print(logger_obj.get_summary())

    import shutil
    if os.path.exists("./temp_logs"):
        shutil.rmtree("./temp_logs")
