"""Tests for market data tools to ensure JSON serialization compatibility"""

import json
from datetime import datetime
from unittest.mock import patch

import numpy as np
import pytest

from mcp_mt5.main import (
    copy_rates_from_date,
    copy_rates_from_pos,
    copy_rates_range,
    copy_ticks_from_date,
    copy_ticks_from_pos,
    copy_ticks_range,
)


@pytest.fixture
def mock_rates_data():
    """Create mock rate data that simulates MT5 response"""
    # MT5 returns a structured numpy array
    dtype = [
        ("time", "i8"),
        ("open", "f8"),
        ("high", "f8"),
        ("low", "f8"),
        ("close", "f8"),
        ("tick_volume", "i8"),
        ("spread", "i4"),
        ("real_volume", "i8"),
    ]

    data = np.array(
        [
            (1634025600, 1.1615, 1.1625, 1.1610, 1.1620, 1250, 2, 125000),
            (1634029200, 1.1620, 1.1630, 1.1615, 1.1625, 1100, 2, 110000),
            (1634032800, 1.1625, 1.1635, 1.1620, 1.1630, 1350, 2, 135000),
        ],
        dtype=dtype,
    )
    return data


@pytest.fixture
def mock_ticks_data():
    """Create mock tick data that simulates MT5 response"""
    dtype = [
        ("time", "i8"),
        ("bid", "f8"),
        ("ask", "f8"),
        ("last", "f8"),
        ("volume", "i8"),
        ("time_msc", "i8"),
        ("flags", "i4"),
        ("volume_real", "f8"),
    ]

    data = np.array(
        [
            (1634025600, 1.1615, 1.1617, 1.1616, 100, 1634025600000, 134, 10.0),
            (1634025601, 1.1616, 1.1618, 1.1617, 150, 1634025601000, 134, 15.0),
        ],
        dtype=dtype,
    )
    return data


class TestCopyRatesFromPosJsonSerialization:
    """Test that copy_rates_from_pos returns JSON-serializable data"""

    @patch("mcp_mt5.main.mt5.copy_rates_from_pos")
    def test_returns_json_serializable_data(self, mock_copy_rates, mock_rates_data):
        """Test that the returned data can be serialized to JSON"""
        mock_copy_rates.return_value = mock_rates_data

        result = copy_rates_from_pos(symbol="EURUSD", timeframe=60, start_pos=0, count=3)

        # This should not raise an exception if data is JSON-serializable
        try:
            json_str = json.dumps(result)
            assert isinstance(json_str, str)
        except (TypeError, ValueError) as e:
            pytest.fail(f"Result is not JSON-serializable: {e}")

    @patch("mcp_mt5.main.mt5.copy_rates_from_pos")
    def test_datetime_fields_are_strings(self, mock_copy_rates, mock_rates_data):
        """Test that datetime fields are returned as ISO format strings"""
        mock_copy_rates.return_value = mock_rates_data

        result = copy_rates_from_pos(symbol="EURUSD", timeframe=60, start_pos=0, count=3)

        assert len(result) > 0
        # Check that time field is a string (ISO format)
        assert isinstance(result[0]["time"], str)
        # Verify it's a valid datetime string
        datetime.fromisoformat(result[0]["time"])

    @patch("mcp_mt5.main.mt5.copy_rates_from_pos")
    def test_numeric_fields_preserved(self, mock_copy_rates, mock_rates_data):
        """Test that numeric fields maintain their values"""
        mock_copy_rates.return_value = mock_rates_data

        result = copy_rates_from_pos(symbol="EURUSD", timeframe=60, start_pos=0, count=3)

        assert len(result) == 3
        # Check first bar
        assert isinstance(result[0]["open"], (int, float))
        assert isinstance(result[0]["high"], (int, float))
        assert isinstance(result[0]["low"], (int, float))
        assert isinstance(result[0]["close"], (int, float))
        assert isinstance(result[0]["tick_volume"], (int, float))


class TestCopyRatesFromDateJsonSerialization:
    """Test that copy_rates_from_date returns JSON-serializable data"""

    @patch("mcp_mt5.main.mt5.copy_rates_from_date")
    def test_returns_json_serializable_data(self, mock_copy_rates, mock_rates_data):
        """Test that the returned data can be serialized to JSON"""
        mock_copy_rates.return_value = mock_rates_data

        result = copy_rates_from_date(
            symbol="EURUSD", timeframe=60, date_from=datetime(2024, 1, 1), count=3
        )

        # This should not raise an exception
        try:
            json_str = json.dumps(result)
            assert isinstance(json_str, str)
        except (TypeError, ValueError) as e:
            pytest.fail(f"Result is not JSON-serializable: {e}")


class TestCopyRatesRangeJsonSerialization:
    """Test that copy_rates_range returns JSON-serializable data"""

    @patch("mcp_mt5.main.mt5.copy_rates_range")
    def test_returns_json_serializable_data(self, mock_copy_rates, mock_rates_data):
        """Test that the returned data can be serialized to JSON"""
        mock_copy_rates.return_value = mock_rates_data

        result = copy_rates_range(
            symbol="EURUSD",
            timeframe=60,
            date_from=datetime(2024, 1, 1),
            date_to=datetime(2024, 1, 2),
        )

        # This should not raise an exception
        try:
            json_str = json.dumps(result)
            assert isinstance(json_str, str)
        except (TypeError, ValueError) as e:
            pytest.fail(f"Result is not JSON-serializable: {e}")


class TestCopyTicksJsonSerialization:
    """Test that tick-related functions return JSON-serializable data"""

    @patch("mcp_mt5.main.mt5.copy_ticks_from")
    def test_copy_ticks_from_pos_json_serializable(self, mock_copy_ticks, mock_ticks_data):
        """Test that copy_ticks_from_pos returns JSON-serializable data"""
        mock_copy_ticks.return_value = mock_ticks_data

        result = copy_ticks_from_pos(symbol="EURUSD", start_time=datetime(2024, 1, 1), count=2)

        # This should not raise an exception
        try:
            json_str = json.dumps(result)
            assert isinstance(json_str, str)
        except (TypeError, ValueError) as e:
            pytest.fail(f"Result is not JSON-serializable: {e}")

        # Check datetime fields are strings
        assert isinstance(result[0]["time"], str)
        assert isinstance(result[0]["time_msc"], str)

    @patch("mcp_mt5.main.mt5.copy_ticks_from")
    def test_copy_ticks_from_date_json_serializable(self, mock_copy_ticks, mock_ticks_data):
        """Test that copy_ticks_from_date returns JSON-serializable data"""
        mock_copy_ticks.return_value = mock_ticks_data

        result = copy_ticks_from_date(symbol="EURUSD", date_from=datetime(2024, 1, 1), count=2)

        # This should not raise an exception
        try:
            json_str = json.dumps(result)
            assert isinstance(json_str, str)
        except (TypeError, ValueError) as e:
            pytest.fail(f"Result is not JSON-serializable: {e}")

    @patch("mcp_mt5.main.mt5.copy_ticks_range")
    def test_copy_ticks_range_json_serializable(self, mock_copy_ticks, mock_ticks_data):
        """Test that copy_ticks_range returns JSON-serializable data"""
        mock_copy_ticks.return_value = mock_ticks_data

        result = copy_ticks_range(
            symbol="EURUSD", date_from=datetime(2024, 1, 1), date_to=datetime(2024, 1, 2)
        )

        # This should not raise an exception
        try:
            json_str = json.dumps(result)
            assert isinstance(json_str, str)
        except (TypeError, ValueError) as e:
            pytest.fail(f"Result is not JSON-serializable: {e}")
