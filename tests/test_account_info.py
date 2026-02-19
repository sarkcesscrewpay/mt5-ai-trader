"""Unit tests for account information retrieval."""

from unittest.mock import Mock, patch

import pytest
from fastmcp import Client

from mcp_mt5.main import mcp


@pytest.mark.unit
class TestAccountInfo:
    """Test account information retrieval."""

    @patch("mcp_mt5.main.mt5")
    async def test_get_account_info_success(self, mock_mt5):
        """Test successful account info retrieval."""
        # Create mock account info
        mock_account = Mock()
        mock_account._asdict.return_value = {
            "login": 123456,
            "trade_mode": 0,
            "leverage": 100,
            "limit_orders": 200,
            "margin_so_mode": 0,
            "trade_allowed": True,
            "trade_expert": True,
            "margin_mode": 0,
            "currency_digits": 2,
            "fifo_close": False,
            "balance": 10000.0,
            "credit": 0.0,
            "profit": 150.50,
            "equity": 10150.50,
            "margin": 500.0,
            "margin_free": 9650.50,
            "margin_level": 2030.1,
            "margin_so_call": 50.0,
            "margin_so_so": 30.0,
            "margin_initial": 0.0,
            "margin_maintenance": 0.0,
            "assets": 0.0,
            "liabilities": 0.0,
            "commission_blocked": 0.0,
            "name": "Test Account",
            "server": "TestServer",
            "currency": "USD",
            "company": "Test Company",
        }
        mock_mt5.account_info.return_value = mock_account

        async with Client(mcp) as client:
            result = await client.call_tool("get_account_info", {})

        assert result.data.login == 123456
        assert result.data.balance == 10000.0
        assert result.data.equity == 10150.50
        assert result.data.profit == 150.50
        assert result.data.currency == "USD"
        assert result.data.leverage == 100
        mock_mt5.account_info.assert_called_once()

    @patch("mcp_mt5.main.mt5")
    async def test_get_account_info_failure(self, mock_mt5):
        """Test account info retrieval failure."""
        mock_mt5.account_info.return_value = None
        mock_mt5.last_error.return_value = (1, "Not connected")

        async with Client(mcp) as client:
            with pytest.raises(Exception, match="Failed to get account info"):
                await client.call_tool("get_account_info", {})

        mock_mt5.account_info.assert_called_once()
        mock_mt5.last_error.assert_called_once()

    @patch("mcp_mt5.main.mt5")
    async def test_account_info_all_fields(self, mock_mt5):
        """Test that all expected fields are present in account info."""
        mock_account = Mock()
        mock_account._asdict.return_value = {
            "login": 123456,
            "trade_mode": 0,
            "leverage": 100,
            "limit_orders": 200,
            "margin_so_mode": 0,
            "trade_allowed": True,
            "trade_expert": True,
            "margin_mode": 0,
            "currency_digits": 2,
            "fifo_close": False,
            "balance": 10000.0,
            "credit": 0.0,
            "profit": 0.0,
            "equity": 10000.0,
            "margin": 0.0,
            "margin_free": 10000.0,
            "margin_level": 0.0,
            "margin_so_call": 50.0,
            "margin_so_so": 30.0,
            "margin_initial": 0.0,
            "margin_maintenance": 0.0,
            "assets": 0.0,
            "liabilities": 0.0,
            "commission_blocked": 0.0,
            "name": "Test",
            "server": "Test",
            "currency": "USD",
            "company": "Test",
        }
        mock_mt5.account_info.return_value = mock_account

        async with Client(mcp) as client:
            result = await client.call_tool("get_account_info", {})

        # Check all required fields exist
        required_fields = [
            "login",
            "balance",
            "equity",
            "margin",
            "margin_free",
            "profit",
            "currency",
            "leverage",
            "name",
            "server",
        ]

        for field in required_fields:
            assert hasattr(result.data, field), f"Missing field: {field}"


@pytest.mark.unit
class TestTerminalInfo:
    """Test terminal information retrieval."""

    @patch("mcp_mt5.main.mt5")
    async def test_get_terminal_info_success(self, mock_mt5):
        """Test successful terminal info retrieval."""
        mock_terminal = Mock()
        mock_terminal._asdict.return_value = {
            "community_account": False,
            "community_connection": False,
            "connected": True,
            "dlls_allowed": True,
            "trade_allowed": True,
            "tradeapi_disabled": False,
            "email_enabled": False,
            "ftp_enabled": False,
            "notifications_enabled": False,
            "mqid": False,
            "build": 3802,
            "maxbars": 100000,
            "codepage": 1252,
            "ping_last": 10,
            "community_balance": 0.0,
            "retransmission": 0.0,
            "company": "MetaQuotes",
            "name": "MetaTrader 5",
            "language": "English",
            "path": "C:\\Program Files\\MetaTrader 5",
            "data_path": "C:\\Users\\Test\\AppData\\Roaming\\MetaQuotes\\Terminal",
            "commondata_path": "C:\\Users\\Test\\AppData\\Roaming\\MetaQuotes\\Common",
        }
        mock_mt5.terminal_info.return_value = mock_terminal

        async with Client(mcp) as client:
            result = await client.call_tool("get_terminal_info", {})

        assert result.data["connected"] is True
        assert result.data["trade_allowed"] is True
        assert result.data["build"] == 3802
        assert result.data["company"] == "MetaQuotes"
        mock_mt5.terminal_info.assert_called_once()

    @patch("mcp_mt5.main.mt5")
    async def test_get_terminal_info_failure(self, mock_mt5):
        """Test terminal info retrieval failure."""
        mock_mt5.terminal_info.return_value = None
        mock_mt5.last_error.return_value = (1, "Not initialized")

        async with Client(mcp) as client:
            with pytest.raises(Exception, match="Failed to get terminal info"):
                await client.call_tool("get_terminal_info", {})

        mock_mt5.terminal_info.assert_called_once()
        mock_mt5.last_error.assert_called_once()
