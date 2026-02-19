"""
Safety Features Module for MT5 Trading System

This module implements safety mechanisms including:
- Kill switch (emergency stop)
- Capital protection mode
- Trading hour filters
- News volatility filters

Author: AI Trading System
Version: 1.0.0
"""

import logging
import signal
import sys
import threading
from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum
from typing import Callable, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class SafetyStatus(Enum):
    """Safety system status."""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    DISABLED = "disabled"
    CAPITAL_PROTECTION = "capital_protection"


@dataclass
class SafetyConfig:
    """
    Safety configuration.

    Attributes:
        kill_switch_enabled: Enable kill switch
        max_daily_drawdown: Maximum daily drawdown (0.05 = 5%)
        max_consecutive_losses: Max consecutive losing trades
        capital_protection_enabled: Enable capital protection
        capital_protection_threshold: Drawdown threshold for protection
        position_reduction_factor: Factor to reduce positions by
    """
    kill_switch_enabled: bool = True
    max_daily_drawdown: float = 0.05
    max_consecutive_losses: int = 5
    capital_protection_enabled: bool = True
    capital_protection_threshold: float = 0.03
    position_reduction_factor: float = 0.5
    emergency_stop_enabled: bool = True


@dataclass
class SafetyState:
    """
    Current safety system state.

    Attributes:
        status: Current status
        triggered_at: When trigger was activated
        trigger_reason: Reason for trigger
        consecutive_losses: Current consecutive losses
    """
    status: SafetyStatus = SafetyStatus.ACTIVE
    triggered_at: Optional[datetime] = None
    trigger_reason: str = ""
    consecutive_losses: int = 0
    daily_loss: float = 0.0
    kill_switch_armed: bool = False


class KillSwitch:
    """
    Emergency kill switch for trading system.

    Responsibilities:
    - Manual emergency stop
    - Automatic triggers based on drawdown/losses
    - Graceful shutdown
    """

    def __init__(self, config: Optional[SafetyConfig] = None):
        self.config = config or SafetyConfig()
        self._state = SafetyState()
        self._lock = threading.Lock()
        self._callbacks: list[Callable] = []
        self._original_sigterm = None
        self._original_sigint = None

    def arm(self):
        """Arm the kill switch."""
        with self._lock:
            self._state.kill_switch_armed = True
            self._state.status = SafetyStatus.ACTIVE
            logger.info("Kill switch ARMED")

            # Setup signal handlers
            self._original_sigterm = signal.getsignal(signal.SIGTERM)
            self._original_sigint = signal.getsignal(signal.SIGINT)

            signal.signal(signal.SIGTERM, self._handle_shutdown)
            signal.signal(signal.SIGINT, self._handle_shutdown)

    def disarm(self):
        """Disarm the kill switch."""
        with self._lock:
            self._state.kill_switch_armed = False
            self._state.status = SafetyStatus.DISABLED
            logger.info("Kill switch DISARMED")

            # Restore signal handlers
            if self._original_sigterm:
                signal.signal(signal.SIGTERM, self._original_sigterm)
            if self._original_sigint:
                signal.signal(signal.SIGINT, self._original_int)

    def trigger(self, reason: str) -> bool:
        """
        Trigger the kill switch.

        Args:
            reason: Reason for trigger

        Returns:
            True if successfully triggered
        """
        with self._lock:
            if not self._state.kill_switch_armed:
                logger.warning("Kill switch not armed")
                return False

            self._state.status = SafetyStatus.TRIGGERED
            self._state.triggered_at = datetime.now()
            self._state.trigger_reason = reason

            logger.critical(f"KILL SWITCH TRIGGERED: {reason}")

            # Execute callbacks
            for callback in self._callbacks:
                try:
                    callback(reason)
                except Exception as e:
                    logger.error(f"Callback error: {e}")

            return True

    def check_conditions(
        self,
        account_balance: float,
        daily_pnl: float,
        consecutive_losses: int
    ) -> Optional[str]:
        """
        Check if any kill switch conditions are met.

        Args:
            account_balance: Current account balance
            daily_pnl: Today's profit/loss
            consecutive_losses: Current consecutive losses

        Returns:
            Reason string if triggered, None otherwise
        """
        with self._lock:
            # Check daily drawdown
            if daily_pnl < 0:
                daily_loss_pct = abs(daily_pnl) / account_balance
                self._state.daily_loss = daily_loss_pct

                if daily_loss_pct >= self.config.max_daily_drawdown:
                    return f"Daily drawdown limit: {daily_loss_pct*100:.1f}%"

            # Check consecutive losses
            self._state.consecutive_losses = consecutive_losses
            if consecutive_losses >= self.config.max_consecutive_losses:
                return f"Max consecutive losses: {consecutive_losses}"

            return None

    def register_callback(self, callback: Callable):
        """Register a callback to be called when kill switch triggers."""
        self._callbacks.append(callback)

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.trigger(f"Signal {signum} received")

    @property
    def is_active(self) -> bool:
        """Check if kill switch is active."""
        return self._state.status == SafetyStatus.ACTIVE

    @property
    def state(self) -> SafetyState:
        """Get current state."""
        return self._state


class CapitalProtection:
    """
    Capital protection mode - reduces risk when in drawdown.

    When activated:
    - Position sizes reduced by 50%
    - Only highest confidence trades allowed
    - Stricter stop loss requirements
    """

    def __init__(self, config: Optional[SafetyConfig] = None):
        self.config = config or SafetyConfig()
        self._active = False
        self._lock = threading.Lock()

    def activate(self, reason: str = ""):
        """Activate capital protection mode."""
        with self._lock:
            self._active = True
            logger.warning(f"CAPITAL PROTECTION ACTIVATED: {reason}")

    def deactivate(self):
        """Deactivate capital protection mode."""
        with self._lock:
            self._active = False
            logger.info("Capital protection deactivated")

    def check(
        self,
        account_balance: float,
        peak_balance: float
    ) -> bool:
        """
        Check if capital protection should be activated.

        Args:
            account_balance: Current balance
            peak_balance: Highest balance

        Returns:
            True if protection should be active
        """
        if not self.config.capital_protection_enabled:
            return False

        drawdown = (peak_balance - account_balance) / peak_balance

        if drawdown >= self.config.capital_protection_threshold:
            self.activate(f"Drawdown: {drawdown*100:.1f}%")
            return True

        if self._active and drawdown < self.config.capital_protection_threshold * 0.5:
            self.deactivate()

        return self._active

    def get_risk_multiplier(self) -> float:
        """Get risk reduction multiplier."""
        if self._active:
            return self.config.position_reduction_factor
        return 1.0

    @property
    def is_active(self) -> bool:
        return self._active


class TradingHoursFilter:
    """
    Filter trades based on trading hours and market sessions.
    """

    # Trading sessions (UTC)
    SESSIONS = {
        'sydney': (time(22, 0), time(7, 0)),
        'tokyo': (time(0, 0), time(9, 0)),
        'london': (time(7, 0), time(16, 0)),
        'newyork': (time(13, 0), time(22, 0)),
    }

    # Major pairs have best liquidity during these hours
    HIGH_LIQUIDITY = [
        (time(7, 0), time(16, 0)),  # London
        (time(13, 0), time(22, 0)),  # New York
    ]

    def __init__(
        self,
        allowed_sessions: list[str] = None,
        avoid_market_open_minutes: int = 30,
        avoid_market_close_minutes: int = 30
    ):
        self.allowed_sessions = allowed_sessions or ['london', 'newyork']
        self.avoid_open = avoid_market_open_minutes
        self.avoid_close = avoid_market_close_minutes

    def is_allowed(self, timestamp: datetime) -> tuple[bool, str]:
        """
        Check if trading is allowed at given time.

        Args:
            timestamp: Check datetime

        Returns:
            Tuple of (allowed, reason)
        """
        # Weekend check
        if timestamp.weekday() >= 5:
            return False, "Weekend"

        # Check session
        current_session = self._get_session(timestamp)
        if self.allowed_sessions and current_session not in self.allowed_sessions:
            return False, f"Session {current_session} not in allowed list"

        # Avoid market open
        for start, end in self.HIGH_LIQUIDITY:
            open_time = datetime.combine(timestamp.date(), start)
            close_time = datetime.combine(timestamp.date(), end)

            # Handle overnight sessions
            if start > end:
                open_time = datetime.combine(timestamp.date() - timedelta(days=1), start)

            avoid_open_start = open_time - timedelta(minutes=self.avoid_open)
            avoid_open_end = open_time + timedelta(minutes=self.avoid_open)

            if avoid_open_start <= timestamp <= avoid_open_end:
                return False, "Avoiding market open"

            # Avoid market close
            avoid_close_start = close_time - timedelta(minutes=self.avoid_close)
            avoid_close_end = close_time + timedelta(minutes=self.avoid_close)

            if avoid_close_start <= timestamp <= avoid_close_end:
                return False, "Avoiding market close"

        return True, "Trading allowed"

    def _get_session(self, timestamp: datetime) -> Optional[str]:
        """Get current trading session."""
        t = timestamp.time()

        if time(22, 0) <= t or t < time(7, 0):
            return 'sydney'
        elif time(0, 0) <= t < time(9, 0):
            return 'tokyo'
        elif time(7, 0) <= t < time(16, 0):
            return 'london'
        elif time(13, 0) <= t < time(22, 0):
            return 'newyork'

        return None


class NewsVolatilityFilter:
    """
    Filter trades based on news events and market volatility.
    """

    def __init__(
        self,
        high_volatility_multiplier: float = 2.0,
        news_lookahead_hours: int = 1
    ):
        self.high_volatility_mult = high_volatility_multiplier
        self.news_lookahead = news_lookahead_hours
        self._news_events = []

    def add_news_event(self, timestamp: datetime, title: str, impact: str):
        """Add news event."""
        self._news_events.append({
            'timestamp': timestamp,
            'title': title,
            'impact': impact
        })

    def is_allowed(
        self,
        current_time: datetime,
        current_atr: float,
        average_atr: float
    ) -> tuple[bool, str]:
        """
        Check if trading is allowed.

        Args:
            current_time: Current time
            current_atr: Current ATR value
            average_atr: Average ATR

        Returns:
            Tuple of (allowed, reason)
        """
        # Check volatility
        if average_atr > 0:
            volatility_ratio = current_atr / average_atr

            if volatility_ratio >= self.high_volatility_mult:
                return False, f"High volatility: {volatility_ratio:.1f}x average"

        # Check upcoming news
        for event in self._news_events:
            time_diff = (event['timestamp'] - current_time).total_seconds() / 3600

            if 0 <= time_diff <= self.news_lookahead and event['impact'] == 'high':
                return False, f"High impact news: {event['title']}"

        return True, "Trading allowed"


class SafetyManager:
    """
    Overall safety system manager.

    Coordinates all safety components:
    - Kill switch
    - Capital protection
    - Trading hours filter
    - News volatility filter
    """

    def __init__(self, config: Optional[SafetyConfig] = None):
        self.config = config or SafetyConfig()

        self.kill_switch = KillSwitch(config)
        self.capital_protection = CapitalProtection(config)
        self.trading_hours = TradingHoursFilter()
        self.news_filter = NewsVolatilityFilter()

    def initialize(self):
        """Initialize safety system."""
        self.kill_switch.arm()
        logger.info("Safety system initialized")

    def check_all(
        self,
        account_balance: float,
        peak_balance: float,
        daily_pnl: float,
        consecutive_losses: int,
        current_time: datetime,
        current_atr: float,
        average_atr: float
    ) -> tuple[bool, str]:
        """
        Run all safety checks.

        Returns:
            Tuple of (all_allowed, block_reason)
        """
        # Check kill switch conditions
        reason = self.kill_switch.check_conditions(
            account_balance, daily_pnl, consecutive_losses
        )
        if reason:
            return False, f"Kill switch: {reason}"

        # Check capital protection
        if self.capital_protection.check(account_balance, peak_balance):
            logger.warning("Capital protection active - reducing risk")

        # Check trading hours
        allowed, reason = self.trading_hours.is_allowed(current_time)
        if not allowed:
            return False, f"Trading hours: {reason}"

        # Check news/volatility
        allowed, reason = self.news_filter.is_allowed(current_time, current_atr, average_atr)
        if not allowed:
            return False, f"News/Volatility: {reason}"

        return True, "All checks passed"

    def get_risk_multiplier(self) -> float:
        """Get current risk multiplier from capital protection."""
        return self.capital_protection.get_risk_multiplier()


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("Safety Features Module Test")
    print("=" * 60)

    # Create safety config
    config = SafetyConfig(
        max_daily_drawdown=0.05,
        max_consecutive_losses=5,
        capital_protection_enabled=True,
        capital_protection_threshold=0.03
    )

    # Create safety manager
    safety = SafetyManager(config)
    safety.initialize()

    print("✓ Safety system initialized")

    # Test kill switch
    print("\n1. Kill Switch Test")
    triggered = safety.kill_switch.trigger("Manual test")
    print(f"   Triggered: {triggered}")
    print(f"   Status: {safety.kill_switch.state.status.value}")

    # Reset for further tests
    safety.kill_switch._state.status = SafetyStatus.ACTIVE

    # Test trading hours
    print("\n2. Trading Hours Filter Test")
    from datetime import datetime
    now = datetime.now()
    allowed, reason = safety.trading_hours.is_allowed(now)
    print(f"   Current time: {now}")
    print(f"   Allowed: {allowed}, Reason: {reason}")

    # Test capital protection
    print("\n3. Capital Protection Test")
    is_active = safety.capital_protection.check(9700, 10000)
    print(f"   Active: {is_active}")
    print(f"   Risk multiplier: {safety.capital_protection.get_risk_multiplier()}")

    print("\n" + "=" * 60)
    print("Safety Features Module - Complete")
    print("=" * 60)
