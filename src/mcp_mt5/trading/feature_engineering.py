"""
Feature Engineering Module for MT5 Trading System

This module handles technical indicator calculation, feature generation,
and data preparation for ML models.

Indicators supported:
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- EMA (Exponential Moving Average)
- ATR (Average True Range)
- Bollinger Bands
- Stochastic Oscillator
- Volume indicators
- Price patterns

Author: AI Trading System
Version: 1.0.0
"""

import logging
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler

logger = logging.getLogger(__name__)


class ScalerType(Enum):
    """Types of feature scaling."""
    STANDARD = "standard"  # Zero mean, unit variance
    MINMAX = "minmax"      # 0-1 range
    NONE = "none"          # No scaling


class FeatureEngineer:
    """
    Generates features from OHLC data for ML models.

    Responsibilities:
    - Calculate technical indicators
    - Generate price-based features
    - Normalize features
    - Create target labels
    """

    def __init__(self, scaler_type: ScalerType = ScalerType.STANDARD):
        self._scaler_type = scaler_type
        self._scaler: Optional[StandardScaler | MinMaxScaler] = None

    # ==================== TREND INDICATORS ====================

    def calculate_ema(
        self,
        data: pd.Series,
        periods: list[int] = [9, 21, 50, 100, 200]
    ) -> pd.DataFrame:
        """
        Calculate Exponential Moving Averages.

        Args:
            data: Price series
            periods: List of EMA periods

        Returns:
            DataFrame with EMA columns
        """
        result = pd.DataFrame(index=data.index)
        for period in periods:
            result[f'ema_{period}'] = data.ewm(
                span=period,
                adjust=False
            ).mean()
        return result

    def calculate_sma(
        self,
        data: pd.Series,
        periods: list[int] = [20, 50, 200]
    ) -> pd.DataFrame:
        """
        Calculate Simple Moving Averages.

        Args:
            data: Price series
            periods: List of SMA periods

        Returns:
            DataFrame with SMA columns
        """
        result = pd.DataFrame(index=data.index)
        for period in periods:
            result[f'sma_{period}'] = data.rolling(window=period).mean()
        return result

    def calculate_macd(
        self,
        data: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> pd.DataFrame:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        Args:
            data: Price series
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period

        Returns:
            DataFrame with MACD, signal, and histogram
        """
        ema_fast = data.ewm(span=fast, adjust=False).mean()
        ema_slow = data.ewm(span=slow, adjust=False).mean()

        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line

        result = pd.DataFrame({
            'macd': macd,
            'macd_signal': signal_line,
            'macd_histogram': histogram
        }, index=data.index)

        return result

    # ==================== MOMENTUM INDICATORS ====================

    def calculate_rsi(
        self,
        data: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """
        Calculate Relative Strength Index.

        Args:
            data: Price series
            period: RSI period

        Returns:
            Series with RSI values
        """
        delta = data.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        # Use EMA for more responsive RSI
        avg_gain = gain.ewm(span=period, adjust=False).mean()
        avg_loss = loss.ewm(span=period, adjust=False).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def calculate_stochastic(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        k_period: int = 14,
        d_period: int = 3
    ) -> pd.DataFrame:
        """
        Calculate Stochastic Oscillator.

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            k_period: %K period
            d_period: %D period

        Returns:
            DataFrame with %K and %D
        """
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()

        k = 100 * (close - lowest_low) / (highest_high - lowest_low)
        d = k.rolling(window=d_period).mean()

        result = pd.DataFrame({
            'stoch_k': k,
            'stoch_d': d
        }, index=close.index)

        return result

    # ==================== VOLATILITY INDICATORS ====================

    def calculate_atr(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """
        Calculate Average True Range (ATR).

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: ATR period

        Returns:
            Series with ATR values
        """
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(span=period, adjust=False).mean()

        return atr

    def calculate_bollinger_bands(
        self,
        data: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> pd.DataFrame:
        """
        Calculate Bollinger Bands.

        Args:
            data: Price series
            period: Moving average period
            std_dev: Standard deviation multiplier

        Returns:
            DataFrame with upper, middle, lower bands
        """
        middle = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()

        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        # Calculate bandwidth and %B
        bandwidth = (upper - lower) / middle
        percent_b = (data - lower) / (upper - lower)

        result = pd.DataFrame({
            'bb_upper': upper,
            'bb_middle': middle,
            'bb_lower': lower,
            'bb_width': bandwidth,
            'bb_percent': percent_b
        }, index=data.index)

        return result

    # ==================== VOLUME INDICATORS ====================

    def calculate_volume_features(
        self,
        close: pd.Series,
        volume: pd.Series,
        periods: list[int] = [5, 20]
    ) -> pd.DataFrame:
        """
        Calculate volume-based features.

        Args:
            close: Close prices
            volume: Volume data
            periods: Periods for calculations

        Returns:
            DataFrame with volume features
        """
        result = pd.DataFrame(index=close.index)

        # Volume SMA
        for period in periods:
            result[f'volume_sma_{period}'] = volume.rolling(window=period).mean()

        # Volume ratio
        result['volume_ratio'] = volume / result['volume_sma_20']

        # Price-volume correlation
        result['price_volume_corr'] = close.rolling(window=20).corr(volume)

        # OBV (On Balance Volume)
        obv = pd.Series(0.0, index=close.index)
        obv.iloc[1:] = np.where(
            close.iloc[1:] > close.iloc[:-1].values,
            volume.iloc[1:].values,
            np.where(
                close.iloc[1:] < close.iloc[:-1].values,
                -volume.iloc[1:].values,
                0
            )
        ).cumsum()
        result['obv'] = obv
        result['obv_ema'] = obv.ewm(span=10).mean()

        return result

    # ==================== PRICE PATTERNS ====================

    def calculate_price_patterns(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series
    ) -> pd.DataFrame:
        """
        Calculate price pattern features.

        Args:
            high: High prices
            low: Low prices
            close: Close prices

        Returns:
            DataFrame with pattern features
        """
        result = pd.DataFrame(index=close.index)

        # Body size (as percentage of range)
        body = abs(close - (high + low) / 2) * 2
        candle_range = high - low
        result['body_ratio'] = body / candle_range.replace(0, np.nan)

        # Upper/lower shadow
        upper_shadow = high - pd.concat([close, high], axis=1).max(axis=1)
        lower_shadow = pd.concat([close, low], axis=1).min(axis=1) - low
        result['upper_shadow'] = upper_shadow / candle_range.replace(0, np.nan)
        result['lower_shadow'] = lower_shadow / candle_range.replace(0, np.nan)

        # Returns
        result['returns'] = close.pct_change()
        result['returns_log'] = np.log(close / close.shift(1))

        # Volatility (rolling std of returns)
        result['volatility_10'] = close.pct_change().rolling(window=10).std()
        result['volatility_20'] = close.pct_change().rolling(window=20).std()

        # High/Low position
        result['hl_position'] = (close - low) / (high - low).replace(0, np.nan)

        # Momentum
        result['momentum_5'] = close - close.shift(5)
        result['momentum_10'] = close - close.shift(10)
        result['momentum_20'] = close - close.shift(20)

        return result

    # ==================== MAIN FEATURE GENERATION ====================

    def generate_features(
        self,
        df: pd.DataFrame,
        include_patterns: bool = True
    ) -> pd.DataFrame:
        """
        Generate all features from OHLC data.

        Args:
            df: DataFrame with OHLC columns (open, high, low, close, tick_volume)
            include_patterns: Whether to include price pattern features

        Returns:
            DataFrame with all generated features
        """
        logger.info("Generating features from OHLC data")

        features = pd.DataFrame(index=df.index)

        close = df['close']
        high = df['high']
        low = df['low']
        volume = df.get('tick_volume', pd.Series(0, index=df.index))

        # Trend features
        logger.debug("Calculating trend indicators...")
        features = pd.concat([
            features,
            self.calculate_ema(close),
            self.calculate_sma(close)
        ], axis=1)

        logger.debug("Calculating MACD...")
        features = pd.concat([
            features,
            self.calculate_macd(close)
        ], axis=1)

        # Momentum features
        logger.debug("Calculating RSI...")
        features['rsi'] = self.calculate_rsi(close)

        logger.debug("Calculating Stochastic...")
        features = pd.concat([
            features,
            self.calculate_stochastic(high, low, close)
        ], axis=1)

        # Volatility features
        logger.debug("Calculating ATR...")
        features['atr'] = self.calculate_atr(high, low, close)
        features['atr_percent'] = features['atr'] / close * 100  # ATR as % of price

        logger.debug("Calculating Bollinger Bands...")
        features = pd.concat([
            features,
            self.calculate_bollinger_bands(close)
        ], axis=1)

        # Volume features
        if volume.sum() > 0:
            logger.debug("Calculating volume features...")
            features = pd.concat([
                features,
                self.calculate_volume_features(close, volume)
            ], axis=1)

        # Price patterns
        if include_patterns:
            logger.debug("Calculating price patterns...")
            features = pd.concat([
                features,
                self.calculate_price_patterns(high, low, close)
            ], axis=1)

        # Drop rows with NaN values (from indicator lookback)
        features = features.dropna()

        logger.info(f"Generated {len(features.columns)} features from {len(df)} candles")
        return features

    def create_labels(
        self,
        df: pd.DataFrame,
        direction_threshold: float = 0.001,
        holding_periods: list[int] = [1, 4, 12]
    ) -> pd.DataFrame:
        """
        Create target labels for ML training.

        Args:
            df: DataFrame with close prices
            direction_threshold: Minimum return to consider as signal
            holding_periods: Periods to predict ahead

        Returns:
            DataFrame with binary labels
        """
        labels = pd.DataFrame(index=df.index)

        for period in holding_periods:
            # Future return
            future_return = df['close'].shift(-period) / df['close'] - 1

            # Direction label (1 = buy, -1 = sell, 0 = hold)
            labels[f'direction_{period}'] = np.where(
                future_return > direction_threshold, 1,
                np.where(future_return < -direction_threshold, -1, 0)
            )

            # Binary label (1 = up, 0 = down/flat)
            labels[f'binary_{period}'] = (future_return > 0).astype(int)

            # Return label
            labels[f'return_{period}'] = future_return

        return labels

    def normalize_features(
        self,
        features: pd.DataFrame,
        fit: bool = True
    ) -> pd.DataFrame:
        """
        Normalize features using fitted scaler.

        Args:
            features: Feature DataFrame
            fit: Whether to fit the scaler

        Returns:
            Normalized features
        """
        if self._scaler_type == ScalerType.NONE:
            return features

        if fit:
            if self._scaler_type == ScalerType.STANDARD:
                self._scaler = StandardScaler()
            else:
                self._scaler = MinMaxScaler()
            scaled = self._scaler.fit_transform(features)
        else:
            if self._scaler is None:
                logger.warning("Scaler not fitted, returning original features")
                return features
            scaled = self._scaler.transform(features)

        return pd.DataFrame(
            scaled,
            columns=features.columns,
            index=features.index
        )

    def get_feature_importance(
        self,
        feature_names: list[str],
        importance: np.ndarray
    ) -> pd.DataFrame:
        """
        Create feature importance DataFrame.

        Args:
            feature_names: List of feature names
            importance: Importance values from model

        Returns:
            Sorted DataFrame with importance
        """
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)

        return importance_df


# Example usage
if __name__ == "__main__":
    import tempfile

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("Feature Engineering Module Test")
    print("=" * 60)

    # Create sample data
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=500, freq='1h')

    # Generate realistic price data
    returns = np.random.normal(0.0001, 0.001, 500)
    close = 100 * np.exp(np.cumsum(returns))

    # Create OHLC data
    df = pd.DataFrame({
        'open': close * (1 + np.random.uniform(-0.0005, 0.0005, 500)),
        'high': close * (1 + np.random.uniform(0, 0.002, 500)),
        'low': close * (1 + np.random.uniform(-0.002, 0, 500)),
        'close': close,
        'tick_volume': np.random.randint(100, 10000, 500)
    }, index=dates)

    print(f"Input data: {len(df)} candles")
    print(f"Columns: {list(df.columns)}")

    # Initialize feature engineer
    engineer = FeatureEngineer(scaler_type=ScalerType.STANDARD)

    # Generate features
    features = engineer.generate_features(df)
    print(f"\n✓ Generated {len(features.columns)} features:")
    print(f"  {list(features.columns)[:10]}...")

    # Generate labels
    labels = engineer.create_labels(df)
    print(f"\n✓ Generated label columns:")
    print(f"  {list(labels.columns)}")

    # Normalize features
    features_normalized = engineer.normalize_features(features, fit=True)
    print(f"\n✓ Features normalized (StandardScaler)")

    print("\n" + "=" * 60)
    print("Feature Engineering Module - Complete")
    print("=" * 60)
