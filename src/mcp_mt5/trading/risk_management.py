"""
Risk Management Engine for MT5 Trading System

This module handles position sizing, risk controls, and capital protection.
Prioritizes capital preservation over aggressive growth.

Risk Controls:
- Fixed fractional position sizing (1-2% per trade)
- ATR-based stop loss and take profit
- Daily drawdown limits
- Maximum open positions
- Volatility-based adjustments

Author: AI Trading System
Version: 1.0.0
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class TradeDirection(Enum):
    """Trade direction types."""
    BUY = "buy"
    SELL = "sell"


@dataclass
class RiskConfig:
    """
    Risk management configuration.

    Attributes:
        max_risk_per_trade: Maximum risk per trade as fraction (0.01-0.02 = 1-2%)
        max_daily_drawdown: Maximum daily drawdown allowed (0.05 = 5%)
        max_open_positions: Maximum number of concurrent positions
        atr_multiplier_sl: ATR multiplier for stop loss
        atr_multiplier_tp: ATR multiplier for take profit
        min_risk_reward: Minimum risk-reward ratio required
        max_correlation: Maximum correlation between open positions
        trailing_stop_enabled: Enable trailing stop
        trailing_stop_atr_mult: ATR multiplier for trailing stop
    """
    max_risk_per_trade: float = 0.02  # 2% max risk
    max_daily_drawdown: float = 0.05  # 5% max daily drawdown
    max_open_positions: int = 5
    atr_multiplier_sl: float = 2.0
    atr_multiplier_tp: float = 4.0
    min_risk_reward: float = 1.5
    max_correlation: float = 0.7
    trailing_stop_enabled: bool = True
    trailing_stop_atr_mult: float = 1.5


@dataclass
class Position:
    """
    Trading position information.

    Attributes:
        symbol: Trading symbol
        direction: Trade direction
        volume: Position size in lots
        entry_price: Entry price
        current_price: Current market price
        stop_loss: Stop loss price
        take_profit: Take profit price
        profit: Current profit/loss
        open_time: Position open time
    """
    symbol: str
    direction: TradeDirection
    volume: float
    entry_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    profit: float = 0.0
    open_time: datetime = field(default_factory=datetime.now)


@dataclass
class TradeSignal:
    """
    Trade signal with risk-adjusted parameters.

    Attributes:
        symbol: Trading symbol
        direction: Trade direction
        entry_price: Suggested entry price
        stop_loss: Stop loss price
        take_profit: Take profit price
        volume: Position size in lots
        confidence: Signal confidence (0-1)
        atr: Current ATR value
        risk_amount: Risk amount in account currency
    """
    symbol: str
    direction: TradeDirection
    entry_price: float
    stop_loss: float
    take_profit: float
    volume: float
    confidence: float
    atr: float
    risk_amount: float


@dataclass
class AccountState:
    """
    Current account state.

    Attributes:
        balance: Account balance
        equity: Account equity
        margin: Used margin
        free_margin: Available margin
        open_positions: List of open positions
        daily_pnl: Today's profit/loss
        daily_drawdown: Current daily drawdown
    """
    balance: float
    equity: float
    margin: float = 0.0
    free_margin: float = 0.0
    open_positions: list[Position] = field(default_factory=list)
    daily_pnl: float = 0.0
    daily_drawdown: float = 0.0


class RiskEngine:
    """
    Risk management engine for trading.

    Responsibilities:
    - Calculate position sizes based on risk rules
    - Determine stop loss and take profit levels
    - Monitor daily drawdown
    - Control maximum positions
    - Apply volatility-based adjustments
    """

    def __init__(self, config: Optional[RiskConfig] = None):
        self.config = config or RiskConfig()
        self._daily_start_balance: Optional[float] = None
        self._positions_today: int = 0
        self._trades_today: list[datetime] = []

    def calculate_position_size(
        self,
        account: AccountState,
        symbol: str,
        stop_loss_pips: float,
        pip_value: float = 10.0,
        atr: Optional[float] = None
    ) -> float:
        """
        Calculate position size based on risk rules.

        Uses fixed fractional position sizing:
        position_size = (account_balance * risk_percent) / (stop_loss_pips * pip_value)

        Args:
            account: Current account state
            symbol: Trading symbol
            stop_loss_pips: Stop loss in pips
            pip_value: Value of one pip per lot
            atr: Current ATR (used for ATR-based sizing)

        Returns:
            Position size in lots
        """
        # Use equity for position sizing when in profit
        account_balance = account.equity if account.equity > 0 else account.balance

        # Calculate risk amount
        risk_amount = account_balance * self.config.max_risk_per_trade

        # If ATR provided, use ATR-based stop for more dynamic sizing
        if atr is not None and atr > 0:
            # Convert ATR to pips (depends on symbol)
            # For EURUSD, ATR of 0.001 = 10 pips
            atr_pips = atr * 100  # Simplified conversion
            stop_loss_pips = max(stop_loss_pips, atr_pips)

        # Calculate position size
        if stop_loss_pips <= 0 or pip_value <= 0:
            logger.warning("Invalid stop loss or pip value, using minimum size")
            return 0.01

        position_size = risk_amount / (stop_loss_pips * pip_value)

        # Round to valid lot size (usually 0.01)
        position_size = round(position_size, 2)

        # Enforce minimum and maximum
        position_size = max(0.01, min(position_size, 100.0))

        logger.debug(
            f"Position size: {position_size} lots "
            f"(risk: ${risk_amount:.2f}, SL: {stop_loss_pips:.1f} pips)"
        )

        return position_size

    def calculate_stop_loss(
        self,
        entry_price: float,
        direction: TradeDirection,
        atr: float,
        use_atr: bool = True
    ) -> float:
        """
        Calculate stop loss price using ATR.

        Args:
            entry_price: Entry price
            direction: Trade direction
            atr: Current ATR value
            use_atr: Use ATR multiplier or fixed pips

        Returns:
            Stop loss price
        """
        if use_atr:
            sl_distance = atr * self.config.atr_multiplier_sl
        else:
            # Default 20 pips
            sl_distance = 0.0020  # 20 pips for EURUSD

        if direction == TradeDirection.BUY:
            return entry_price - sl_distance
        else:
            return entry_price + sl_distance

    def calculate_take_profit(
        self,
        entry_price: float,
        direction: TradeDirection,
        stop_loss: float,
        atr: float = None
    ) -> float:
        """
        Calculate take profit based on risk-reward ratio.

        Args:
            entry_price: Entry price
            direction: Trade direction
            stop_loss: Stop loss price
            atr: ATR value (optional)

        Returns:
            Take profit price
        """
        # Calculate risk
        risk = abs(entry_price - stop_loss)

        # Apply minimum risk-reward ratio
        reward = risk * self.config.min_risk_reward

        # Optionally use ATR-based TP
        if atr is not None:
            atr_tp = atr * self.config.atr_multiplier_tp
            reward = max(reward, atr_tp)

        if direction == TradeDirection.BUY:
            return entry_price + reward
        else:
            return entry_price - reward

    def validate_trade(
        self,
        account: AccountState,
        trade_signal: TradeSignal
    ) -> tuple[bool, str]:
        """
        Validate if trade passes risk checks.

        Args:
            account: Current account state
            trade_signal: Proposed trade

        Returns:
            Tuple of (is_valid, reason)
        """
        # Check maximum positions
        if len(account.open_positions) >= self.config.max_open_positions:
            return False, f"Maximum positions reached ({self.config.max_open_positions})"

        # Check daily drawdown
        if account.daily_drawdown >= self.config.max_daily_drawdown:
            return False, f"Daily drawdown limit reached ({self.config.max_daily_drawdown*100}%)"

        # Check sufficient margin
        required_margin = self._estimate_margin(trade_signal.volume, trade_signal.symbol)
        if required_margin > account.free_margin:
            return False, f"Insufficient margin (required: {required_margin}, available: {account.free_margin})"

        # Check risk amount
        risk_amount = abs(trade_signal.entry_price - trade_signal.stop_loss) * trade_signal.volume
        if risk_amount > account.balance * self.config.max_risk_per_trade:
            return False, f"Risk amount exceeds limit"

        # Check risk-reward ratio
        reward = abs(trade_signal.take_profit - trade_signal.entry_price)
        risk = abs(trade_signal.entry_price - trade_signal.stop_loss)
        if reward / risk < self.config.min_risk_reward:
            return False, f"Risk-reward ratio below minimum ({self.config.min_risk_reward})"

        return True, "Trade validated"

    def check_drawdown(self, account: AccountState) -> bool:
        """
        Check if account is within drawdown limits.

        Args:
            account: Current account state

        Returns:
            True if within limits
        """
        if self._daily_start_balance is None:
            self._daily_start_balance = account.balance

        # Calculate daily drawdown
        daily_dd = (self._daily_start_balance - account.equity) / self._daily_start_balance

        if daily_dd >= self.config.max_daily_drawdown:
            logger.warning(
                f"Daily drawdown limit reached: {daily_dd*100:.2f}% "
                f"(max: {self.config.max_daily_drawdown*100}%)"
            )
            return False

        return True

    def calculate_correlation_risk(
        self,
        new_direction: TradeDirection,
        open_positions: list[Position]
    ) -> float:
        """
        Calculate correlation risk for new position.

        Args:
            new_direction: Direction of new trade
            open_positions: Currently open positions

        Returns:
            Correlation risk score (0-1)
        """
        if not open_positions:
            return 0.0

        # Simplified: if same direction on correlated pairs
        # In production, would use actual correlation matrix
        same_direction = sum(
            1 for p in open_positions
            if p.direction == new_direction
        )

        return same_direction / len(open_positions)

    def apply_capital_protection(
        self,
        account: AccountState,
        base_risk: float
    ) -> float:
        """
        Apply capital protection mode reducing risk when in drawdown.

        Args:
            account: Current account state
            base_risk: Base risk percentage

        Returns:
            Adjusted risk percentage
        """
        if account.daily_drawdown > 0.02:  # >2% drawdown
            reduction_factor = 0.5  # Reduce risk by 50%
            logger.info(f"Capital protection: reducing risk by {reduction_factor*100}%")
            return base_risk * reduction_factor

        return base_risk

    def _estimate_margin(self, volume: float, symbol: str) -> float:
        """
        Estimate margin required for position.

        Simplified calculation - in production would use actual margin info.
        """
        # Rough estimate: 100k units per lot, 1:100 leverage = 1000 per lot
        return volume * 1000

    def reset_daily(self):
        """Reset daily counters for new trading day."""
        self._positions_today = 0
        self._trades_today = []
        logger.info("Daily counters reset")


# Pseudocode for risk engine logic
"""
RISK ENGINE PSEUDOCODE:

1. POSITION SIZING:
   function calculate_position_size(balance, risk_percent, stop_loss_pips):
       risk_amount = balance * risk_percent
       position_size = risk_amount / (stop_loss_pips * pip_value)
       return clamp(position_size, MIN_LOT, MAX_LOT)

2. STOP LOSS CALCULATION:
   function calculate_stop_loss(entry_price, direction, atr):
       sl_distance = atr * atr_multiplier_sl
       if direction == BUY:
           return entry_price - sl_distance
       else:
           return entry_price + sl_distance

3. TAKE PROFIT CALCULATION:
   function calculate_take_profit(entry_price, direction, stop_loss):
       risk = abs(entry_price - stop_loss)
       reward = risk * min_risk_reward
       if direction == BUY:
           return entry_price + reward
       else:
           return entry_price - reward

4. DRAWDOWN CHECK:
   function check_drawdown(current_balance, start_balance, max_drawdown):
       drawdown = (start_balance - current_balance) / start_balance
       return drawdown < max_drawdown

5. TRADE VALIDATION:
   function validate_trade(account, signal):
       if positions >= max_positions: return REJECT
       if drawdown >= max_drawdown: return REJECT
       if margin < required: return REJECT
       if risk_reward < min_ratio: return REJECT
       return ACCEPT
"""


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("Risk Management Engine Test")
    print("=" * 60)

    # Create risk config
    config = RiskConfig(
        max_risk_per_trade=0.02,
        max_daily_drawdown=0.05,
        max_open_positions=5,
        atr_multiplier_sl=2.0,
        atr_multiplier_tp=4.0,
        min_risk_reward=1.5
    )

    # Create risk engine
    engine = RiskEngine(config)

    # Simulate account state
    account = AccountState(
        balance=10000.0,
        equity=10000.0,
        margin=1000.0,
        free_margin=9000.0,
        open_positions=[],
        daily_pnl=0.0,
        daily_drawdown=0.0
    )

    # Test position sizing
    print("\n1. Position Sizing Test")
    position_size = engine.calculate_position_size(
        account=account,
        symbol="EURUSD",
        stop_loss_pips=20,
        pip_value=10.0,
        atr=0.0015
    )
    print(f"   Position size: {position_size} lots")

    # Test stop loss calculation
    print("\n2. Stop Loss Calculation Test")
    entry_price = 1.1000
    atr = 0.0015  # 15 pips

    sl_buy = engine.calculate_stop_loss(entry_price, TradeDirection.BUY, atr)
    sl_sell = engine.calculate_stop_loss(entry_price, TradeDirection.SELL, atr)
    print(f"   Entry: {entry_price}, ATR: {atr}")
    print(f"   Buy SL: {sl_buy:.5f} ({abs(entry_price-sl_buy)*10000:.1f} pips)")
    print(f"   Sell SL: {sl_sell:.5f} ({abs(entry_price-sl_sell)*10000:.1f} pips)")

    # Test take profit calculation
    print("\n3. Take Profit Calculation Test")
    tp_buy = engine.calculate_take_profit(entry_price, TradeDirection.BUY, sl_buy, atr)
    tp_sell = engine.calculate_take_profit(entry_price, TradeDirection.SELL, sl_sell, atr)
    print(f"   Buy TP: {tp_buy:.5f} (RR: {abs(tp_buy-entry_price)/abs(entry_price-sl_buy):.1f})")
    print(f"   Sell TP: {tp_sell:.5f} (RR: {abs(tp_sell-entry_price)/abs(entry_price-sl_sell):.1f})")

    # Test trade validation
    print("\n4. Trade Validation Test")
    trade_signal = TradeSignal(
        symbol="EURUSD",
        direction=TradeDirection.BUY,
        entry_price=1.1000,
        stop_loss=sl_buy,
        take_profit=tp_buy,
        volume=0.1,
        confidence=0.75,
        atr=atr,
        risk_amount=20.0
    )

    is_valid, reason = engine.validate_trade(account, trade_signal)
    print(f"   Trade valid: {is_valid}, Reason: {reason}")

    # Test drawdown check
    print("\n5. Drawdown Check Test")
    account.equity = 9500.0  # 5% down
    engine._daily_start_balance = 10000.0

    in_drawdown = engine.check_drawdown(account)
    print(f"   Within drawdown limits: {in_drawdown}")

    print("\n" + "=" * 60)
    print("Risk Management Engine - Complete")
    print("=" * 60)
