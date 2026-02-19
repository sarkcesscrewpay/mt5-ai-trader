"""
Data Collection Module for MT5 Trading System

This module handles fetching and managing market data from MetaTrader 5.
Supports historical data retrieval, real-time updates, and data validation.

Author: AI Trading System
Version: 1.0.0
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

import MetaTrader5 as mt5
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class TimeFrame(Enum):
    """Supported timeframes for data collection."""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"

    @property
    def mt5_constant(self) -> int:
        """Return MT5 timeframe constant."""
        mapping = {
            "1m": mt5.TIMEFRAME_M1,
            "5m": mt5.TIMEFRAME_M5,
            "15m": mt5.TIMEFRAME_M15,
            "30m": mt5.TIMEFRAME_M30,
            "1h": mt5.TIMEFRAME_H1,
            "4h": mt5.TIMEFRAME_H4,
            "1d": mt5.TIMEFRAME_D1,
            "1w": mt5.TIMEFRAME_W1,
        }
        return mapping[self.value]


class MT5Connection:
    """
    Manages connection to MetaTrader 5 terminal.

    Responsibilities:
    - Initialize MT5 connection
    - Handle reconnection
    - Validate connection status
    """

    def __init__(self):
        self._initialized = False
        self._login: Optional[int] = None
        self._server: Optional[str] = None

    def connect(self, login: Optional[int] = None, server: Optional[str] = None,
                password: Optional[str] = None, timeout: int = 60000) -> bool:
        """
        Establish connection to MT5 terminal.

        Args:
            login: Trading account login number
            server: Broker server name
            password: Account password
            timeout: Connection timeout in milliseconds

        Returns:
            True if connection successful
        """
        try:
            if not mt5.initialize(timeout=timeout):
                error = mt5.last_error()
                logger.error(f"MT5 initialization failed: {error}")
                return False

            # Login if credentials provided
            if login and password:
                authorized = mt5.login(
                    login=login,
                    password=password,
                    server=server
                )
                if not authorized:
                    logger.error(f"Login failed: {mt5.last_error()}")
                    return False
                self._login = login
                self._server = server

            self._initialized = True
            logger.info("MT5 connection established successfully")
            return True

        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from MT5 terminal."""
        mt5.shutdown()
        self._initialized = False
        logger.info("MT5 disconnected")

    def is_connected(self) -> bool:
        """Check if MT5 is connected and initialized."""
        return self._initialized and mt5.terminal_info() is not None

    def get_account_info(self) -> Optional[dict]:
        """Get current account information."""
        if not self.is_connected():
            return None
        account = mt5.account_info()
        if account is None:
            return None
        return {
            "login": account.login,
            "balance": account.balance,
            "equity": account.equity,
            "margin": account.margin,
            "free_margin": account.margin_free,
            "leverage": account.leverage,
            "profit": account.profit,
        }

    def get_symbols(self) -> list[str]:
        """Get list of available trading symbols."""
        if not self.is_connected():
            return []
        symbols = mt5.symbols_get()
        return [s.name for s in symbols if s.visible]


class DataCollector:
    """
    Collects OHLC and tick data from MT5.

    Responsibilities:
    - Fetch historical candle data
    - Get real-time prices
    - Validate data quality
    - Handle data gaps
    """

    def __init__(self, connection: MT5Connection):
        self._connection = connection
        self._cache: dict = {}

    def get_historical_candles(
        self,
        symbol: str,
        timeframe: TimeFrame,
        count: int = 1000,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical OHLC data from MT5.

        Args:
            symbol: Trading symbol (e.g., "EURUSD")
            timeframe: Candle timeframe
            count: Number of candles to fetch
            start: Start datetime (optional)
            end: End datetime (optional)

        Returns:
            DataFrame with OHLC data or None on error
        """
        try:
            if not self._connection.is_connected():
                logger.error("MT5 not connected")
                return None

            # Ensure symbol is visible
            if not mt5.symbol_select(symbol, True):
                logger.error(f"Cannot select symbol: {symbol}")
                return None

            # Get timezone from MT5
            timezone = mt5.timezone()

            if start and end:
                # Convert to MT5 timestamps
                start_time = int(start.timestamp())
                end_time = int(end.timestamp())
                rates = mt5.copy_rates_range(
                    symbol,
                    timeframe.mt5_constant,
                    start_time,
                    end_time
                )
            else:
                # Get last N candles
                rates = mt5.copy_rates_from_pos(
                    symbol,
                    timeframe.mt5_constant,
                    0,
                    count
                )

            if rates is None or len(rates) == 0:
                logger.warning(f"No data returned for {symbol}")
                return None

            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)

            # Standardize column names
            df.columns = ['open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume']

            logger.debug(f"Fetched {len(df)} candles for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None

    def get_current_price(self, symbol: str) -> Optional[dict]:
        """
        Get current bid/ask prices for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Dict with 'bid', 'ask', 'time' or None
        """
        try:
            if not self._connection.is_connected():
                return None

            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return None

            return {
                'bid': tick.bid,
                'ask': tick.ask,
                'time': datetime.fromtimestamp(tick.time),
                'last': tick.last
            }
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return None

    def get_symbol_info(self, symbol: str) -> Optional[dict]:
        """
        Get detailed symbol information including point size, digits, etc.

        Args:
            symbol: Trading symbol

        Returns:
            Dict with symbol details
        """
        try:
            if not self._connection.is_connected():
                return None

            info = mt5.symbol_info(symbol)
            if info is None:
                return None

            return {
                'name': info.name,
                'point': info.point,
                'digits': info.digits,
                'spread': info.spread,
                'trade_tick_value': info.trade_tick_value,
                'trade_tick_size': info.trade_tick_size,
                'volume_min': info.volume_min,
                'volume_max': info.volume_max,
                'volume_step': info.volume_step,
                'margin_initial': info.margin_initial,
            }
        except Exception as e:
            logger.error(f"Error getting symbol info for {symbol}: {e}")
            return None

    def validate_data(self, df: pd.DataFrame, max_gap_minutes: int = 30) -> bool:
        """
        Validate data quality and check for gaps.

        Args:
            df: OHLC DataFrame
            max_gap_minutes: Maximum allowed gap in minutes

        Returns:
            True if data is valid
        """
        if df is None or len(df) == 0:
            return False

        # Check for missing values
        if df.isnull().any().any():
            logger.warning("Data contains missing values")
            return False

        # Check for price anomalies
        if (df['high'] < df['low']).any():
            logger.warning("Data contains invalid high/low values")
            return False

        if (df['close'] > df['high']).any() or (df['close'] < df['low']).any():
            logger.warning("Data contains close outside high/low range")
            return False

        # Check for gaps
        time_diff = df.index.to_series().diff()
        max_gap = pd.Timedelta(minutes=max_gap_minutes)
        if time_diff.max() > max_gap:
            logger.warning(f"Data contains gaps larger than {max_gap_minutes} minutes")
            return False

        return True

    def get_multiple_timeframe_data(
        self,
        symbol: str,
        timeframes: list[TimeFrame],
        count: int = 100
    ) -> dict[TimeFrame, pd.DataFrame]:
        """
        Fetch data from multiple timeframes.

        Args:
            symbol: Trading symbol
            timeframes: List of timeframes
            count: Number of candles per timeframe

        Returns:
            Dict mapping timeframe to DataFrame
        """
        result = {}
        for tf in timeframes:
            df = self.get_historical_candles(symbol, tf, count)
            if df is not None:
                result[tf] = df
        return result


# Factory function for easy initialization
def create_data_collector() -> Optional[DataCollector]:
    """Create and return a DataCollector instance with connection."""
    connection = MT5Connection()
    if connection.connect():
        return DataCollector(connection)
    return None


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("MT5 Data Collection Module Test")
    print("=" * 60)

    # Initialize connection
    connection = MT5Connection()

    # Try to connect (will fail without actual MT5 terminal)
    if connection.connect():
        print("✓ MT5 Connected")

        # Get account info
        account = connection.get_account_info()
        if account:
            print(f"Account: {account['login']}")
            print(f"Balance: ${account['balance']:.2f}")
            print(f"Equity: ${account['equity']:.2f}")

        # Get symbols
        symbols = connection.get_symbols()
        print(f"Available symbols: {len(symbols)}")

        # Create data collector
        collector = DataCollector(connection)

        # Test data fetch
        df = collector.get_historical_candles("EURUSD", TimeFrame.H1, 100)
        if df is not None:
            print(f"✓ Fetched {len(df)} candles for EURUSD")
            print(f"  Columns: {list(df.columns)}")
            print(f"  Date range: {df.index[0]} to {df.index[-1]}")
        else:
            print("✗ Failed to fetch data")

        # Test current price
        price = collector.get_current_price("EURUSD")
        if price:
            print(f"✓ EURUSD: Bid={price['bid']:.5f}, Ask={price['ask']:.5f}")

        connection.disconnect()
    else:
        print("✗ MT5 Connection failed (expected without terminal)")
        print("  This is normal when MT5 terminal is not running")
