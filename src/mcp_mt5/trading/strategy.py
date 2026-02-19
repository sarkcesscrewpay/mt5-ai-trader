"""
Strategy Module for MT5 Trading System

This module handles trading strategy logic, signal filtering,
and coordination between AI models and execution.

Features:
- Signal filtering based on multiple conditions
- Multi-timeframe analysis
- Trade management rules

Author: AI Trading System
Version: 1.0.0
"""

import logging
from dataclasses import dataclass
from datetime import datetime, time
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Trading signal types."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class StrategyConfig:
    """
    Strategy configuration parameters.

    Attributes:
        min_confidence: Minimum AI confidence to consider signal
        min_rsi: Minimum RSI threshold
        max_rsi: Maximum RSI threshold (avoid overbought/oversold)
        trend_alignment_required: Require same direction on higher timeframe
        allow_contrarian: Allow opposite direction trades
    """
    min_confidence: float = 0.65
    min_rsi: float = 30.0
    max_rsi: float = 70.0
    trend_alignment_required: bool = True
    allow_contrarian: bool = False
    min_atr_filter: float = 0.0001  # Minimum ATR for volatility


@dataclass
class StrategySignal:
    """
    Strategy-level trading signal with all filters applied.

    Attributes:
        signal_type: BUY, SELL, or HOLD
        confidence: Overall confidence score
        ai_signal: Raw AI signal
        filters_passed: List of passed filter names
        filters_failed: List of failed filter names
        timestamp: Signal generation time
    """
    signal_type: SignalType
    confidence: float
    ai_signal: any
    filters_passed: list[str]
    filters_failed: list[str]
    timestamp: datetime


class TradingStrategy:
    """
    Trading strategy with multi-filter signal generation.

    Responsibilities:
    - Apply technical filters to AI signals
    - Check multiple timeframes
    - Validate market conditions
    - Generate actionable trade signals
    """

    def __init__(self, config: Optional[StrategyConfig] = None):
        self.config = config or StrategyConfig()

    def generate_signal(
        self,
        ai_signal: any,
        features: pd.DataFrame,
        higher_timeframe_features: Optional[pd.DataFrame] = None
    ) -> StrategySignal:
        """
        Generate trading signal with filters.

        Args:
            ai_signal: Signal from AI model
            features: Current timeframe features
            higher_timeframe_features: Higher timeframe features for trend

        Returns:
            StrategySignal with filter results
        """
        filters_passed = []
        filters_failed = []

        # Start with HOLD
        signal_type = SignalType.HOLD
        confidence = 0.0

        # Filter 1: AI Confidence
        if ai_signal and ai_signal.confidence >= self.config.min_confidence:
            filters_passed.append("confidence")
            confidence = ai_signal.confidence
            signal_type = SignalType.BUY if ai_signal.direction.name == "BUY" else SignalType.SELL
        else:
            filters_failed.append("confidence")
            return StrategySignal(
                signal_type=SignalType.HOLD,
                confidence=0.0,
                ai_signal=ai_signal,
                filters_passed=[],
                filters_failed=["confidence"],
                timestamp=datetime.now()
            )

        # Filter 2: RSI filter
        if len(features) > 0:
            rsi = features.get('rsi', pd.Series([50])).iloc[-1]

            if signal_type == SignalType.BUY:
                if rsi > self.config.min_rsi:
                    filters_passed.append("rsi_buy")
                else:
                    filters_failed.append("rsi_buy")
                    signal_type = SignalType.HOLD
            elif signal_type == SignalType.SELL:
                if rsi < self.config.max_rsi:
                    filters_passed.append("rsi_sell")
                else:
                    filters_failed.append("rsi_sell")
                    signal_type = SignalType.HOLD

        # Filter 3: ATR filter (volatility)
        if len(features) > 0:
            atr = features.get('atr', pd.Series([0])).iloc[-1]
            if atr > self.config.min_atr_filter:
                filters_passed.append("atr")
            else:
                filters_failed.append("atr")
                signal_type = SignalType.HOLD

        # Filter 4: Trend alignment
        if higher_timeframe_features is not None and len(higher_timeframe_features) > 0:
            em = highera_50_timeframe_features.get('ema_50', pd.Series([0])).iloc[-1]
            price = higher_timeframe_features.get('close', pd.Series([0])).iloc[-1]

            if self.config.trend_alignment_required:
                if signal_type == SignalType.BUY and price > ema_50:
                    filters_passed.append("trend_aligned")
                elif signal_type == SignalType.SELL and price < ema_50:
                    filters_passed.append("trend_aligned")
                else:
                    filters_failed.append("trend_aligned")
                    signal_type = SignalType.HOLD
            else:
                filters_passed.append("trend_check")

        # Filter 5: MACD confirmation
        if len(features) > 0:
            macd = features.get('macd', pd.Series([0])).iloc[-1]
            macd_signal = features.get('macd_signal', pd.Series([0])).iloc[-1]

            if signal_type == SignalType.BUY and macd > macd_signal:
                filters_passed.append("macd")
            elif signal_type == SignalType.SELL and macd < macd_signal:
                filters_passed.append("macd")
            else:
                filters_failed.append("macd")

        # If HOLD, reduce confidence
        if signal_type == SignalType.HOLD:
            confidence = 0.0

        return StrategySignal(
            signal_type=signal_type,
            confidence=confidence,
            ai_signal=ai_signal,
            filters_passed=filters_passed,
            filters_failed=filters_failed,
            timestamp=datetime.now()
        )

    def should_close_position(
        self,
        position: any,
        current_features: pd.DataFrame
    ) -> tuple[bool, str]:
        """
        Determine if position should be closed.

        Args:
            position: Open position
            current_features: Current market features

        Returns:
            Tuple of (should_close, reason)
        """
        if len(current_features) == 0:
            return False, "No features"

        # Check trailing stop (if enabled)
        # Check RSI exit conditions
        rsi = current_features.get('rsi', pd.Series([50])).iloc[-1]

        # Close long if RSI overbought
        if position.direction == "buy" and rsi > 75:
            return True, "RSI overbought"

        # Close short if RSI oversold
        if position.direction == "sell" and rsi < 25:
            return True, "RSI oversold"

        # Check MACD reversal
        macd = current_features.get('macd', pd.Series([0])).iloc[-1]
        macd_signal = current_features.get('macd_signal', pd.Series([0])).iloc[-1]

        if position.direction == "buy" and macd < macd_signal:
            return True, "MACD bearish crossover"

        if position.direction == "sell" and macd > macd_signal:
            return True, "MACD bullish crossover"

        return False, ""


class TimeFilter:
    """
    Filter trades based on trading hours and sessions.
    """

    # Major market sessions (UTC)
    SESSIONS = {
        'sydney': (time(22, 0), time(7, 0)),
        'tokyo': (time(0, 0), time(9, 0)),
        'london': (time(7, 0), time(16, 0)),
        'newyork': (time(13, 0), time(22, 0)),
    }

    def __init__(
        self,
        allowed_sessions: list[str] = None,
        avoid_market_open: bool = True,
        avoid_market_close: bool = True
    ):
        self.allowed_sessions = allowed_sessions or ['london', 'newyork']
        self.avoid_market_open = avoid_market_open
        self.avoid_market_close = avoid_market_close

    def is_trading_allowed(self, current_time: datetime) -> tuple[bool, str]:
        """
        Check if trading is allowed at current time.

        Args:
            current_time: Current datetime

        Returns:
            Tuple of (is_allowed, reason)
        """
        # Check session
        session = self._get_current_session(current_time)
        if self.allowed_sessions and session not in self.allowed_sessions:
            return False, f"Outside allowed sessions: {self.allowed_sessions}"

        # Avoid market open (first 30 minutes)
        if self.avoid_market_open:
            for start, end in [('07:00', '07:30'), ('13:00', '13:30')]:
                open_time = time(int(start.split(':')[0]), int(start.split(':')[1]))
                close_time = time(int(end.split(':')[0]), int(end.split(':')[1]))
                if open_time <= current_time.time() < close_time:
                    return False, "Avoiding market open"

        # Avoid market close (last 30 minutes)
        if self.avoid_market_close:
            for start, end in [('15:30', '16:00'), ('21:30', '22:00')]:
                open_time = time(int(start.split(':')[0]), int(start.split(':')[1]))
                close_time = time(int(end.split(':')[0]), int(end.split(':')[1]))
                if open_time <= current_time.time() < close_time:
                    return False, "Avoiding market close"

        # Weekend check
        if current_time.weekday() >= 5:
            return False, "Weekend"

        return True, "Trading allowed"

    def _get_current_session(self, current_time: datetime) -> Optional[str]:
        """Determine current market session."""
        t = current_time.time()

        if time(22, 0) <= t or t < time(7, 0):
            return 'sydney'
        elif time(0, 0) <= t < time(9, 0):
            return 'tokyo'
        elif time(7, 0) <= t < time(16, 0):
            return 'london'
        elif time(13, 0) <= t < time(22, 0):
            return 'newyork'

        return None


class NewsFilter:
    """
    Filter trades based on news events and volatility.
    """

    def __init__(
        self,
        high_impact_news: bool = True,
        volatility_threshold: float = 2.0
    ):
        self.high_impact_news = high_impact_news
        self.volatility_threshold = volatility_threshold

    def is_trading_allowed(
        self,
        current_time: datetime,
        recent_volatility: float = None,
        news_events: list = None
    ) -> tuple[bool, str]:
        """
        Check if trading is allowed given news/volatility.

        Args:
            current_time: Current time
            recent_volatility: Recent ATR ratio
            news_events: List of upcoming news events

        Returns:
            Tuple of (is_allowed, reason)
        """
        # Check high volatility
        if recent_volatility and recent_volatility > self.volatility_threshold:
            return False, f"High volatility: {recent_volatility:.2f}x"

        # Check news events (simplified - would integrate with news API)
        if news_events:
            for event in news_events:
                time_diff = abs((event['time'] - current_time).total_seconds() / 3600)
                if time_diff < 1 and event['impact'] == 'high':
                    return False, f"High impact news: {event['title']}"

        return True, "Trading allowed"


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("Strategy Module Test")
    print("=" * 60)

    # Create strategy
    config = StrategyConfig(
        min_confidence=0.65,
        min_rsi=30,
        max_rsi=70,
        trend_alignment_required=True
    )
    strategy = TradingStrategy(config)

    # Create sample features
    features = pd.DataFrame({
        'rsi': [45.0, 50.0, 35.0],
        'macd': [0.001, 0.002, 0.0015],
        'macd_signal': [0.001, 0.0015, 0.0015],
        'atr': [0.0015, 0.0016, 0.0017],
        'ema_50': [1.1000, 1.1010, 1.1020],
        'close': [1.1020, 1.1030, 1.1040]
    })

    print(f"Test features shape: {features.shape}")
    print("✓ Strategy module initialized")

    # Test time filter
    time_filter = TimeFilter(allowed_sessions=['london', 'newyork'])
    now = datetime.now()
    allowed, reason = time_filter.is_trading_allowed(now)
    print(f"\nTime filter: {allowed}, {reason}")

    print("\n" + "=" * 60)
    print("Strategy Module - Complete")
    print("=" * 60)
