"""
AI Trading Dashboard - Web Interface for MT5 Trading Bot

Run with: streamlit run app.py

Features:
- Dashboard overview
- Account status
- Open positions
- Risk settings
- Start/Stop trading
- View logs
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime

# Page config
st.set_page_config(
    page_title="MT5 AI Trading Bot",
    page_icon="📈",
    layout="wide"
)


def main():
    # Title
    st.title("🤖 MT5 AI Trading Dashboard")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.title("Settings")
    
    # Connection Status
    st.sidebar.subheader("Connection")
    mt5_connected = st.sidebar.checkbox("MT5 Connected", value=False)
    
    if mt5_connected:
        st.sidebar.success("✓ Connected")
    else:
        st.sidebar.warning("○ Not connected")
    
    # Navigation
    page = st.sidebar.radio("Navigate", [
        "Dashboard", "Positions", "Risk Settings", "Logs", "Backtest"
    ])
    
    # Main content
    if page == "Dashboard":
        dashboard_page()
    elif page == "Positions":
        positions_page()
    elif page == "Risk Settings":
        risk_settings_page()
    elif page == "Logs":
        logs_page()
    elif page == "Backtest":
        backtest_page()


def dashboard_page():
    """Main dashboard page"""
    col1, col2, col3, col4 = st.columns(4)
    
    # Account Info
    with col1:
        st.metric("Balance", "$10,000.00")
    with col2:
        st.metric("Equity", "$10,250.00")
    with col3:
        st.metric("Open Positions", "2")
    with col4:
        st.metric("Daily P/L", "$250.00", delta=2.5)
    
    st.markdown("---")
    
    # Trading Controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        trading_mode = st.selectbox("Trading Mode", ["Paper Trading", "Live Trading"])
    
    with col2:
        symbols = st.multiselect(
            "Active Symbols",
            ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"],
            default=["EURUSD"]
        )
    
    with col3:
        if st.button("▶️ Start Trading", type="primary"):
            st.success("Trading started!")
    
    st.markdown("---")
    
    # Market Overview
    st.subheader("📊 Market Overview")
    
    # Sample market data
    market_data = {
        "Symbol": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"],
        "Bid": ["1.0852", "1.2654", "149.85", "0.6542"],
        "Ask": ["1.0854", "1.2656", "149.87", "0.6544"],
        "Change": ["+0.12%", "-0.08%", "+0.25%", "-0.15%"],
        "Signal": ["🟢 BUY", "🔴 SELL", "🟢 BUY", "🟡 HOLD"]
    }
    
    df = pd.DataFrame(market_data)
    st.dataframe(df, width='stretch')
    
    st.markdown("---")
    
    # Recent Trades
    st.subheader("📋 Recent Trades")
    
    trades_data = {
        "Time": ["10:30", "09:45", "08:15", "Yesterday"],
        "Symbol": ["EURUSD", "GBPUSD", "USDJPY", "EURUSD"],
        "Type": ["BUY", "SELL", "BUY", "SELL"],
        "Volume": ["0.10", "0.05", "0.08", "0.12"],
        "P/L": ["+$25.00", "-$12.50", "+$18.00", "+$45.00"]
    }
    
    df_trades = pd.DataFrame(trades_data)
    st.dataframe(df_trades, width='stretch')
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Equity Curve")
        # Simple line chart
        chart_data = pd.DataFrame(
            np.random.randn(50, 1),
            columns=["Equity"],
            index=pd.date_range(start="1/1/2024", periods=50)
        )
        st.line_chart(chart_data)
    
    with col2:
        st.subheader("📊 Win Rate")
        # Simple bar chart
        win_data = pd.DataFrame({
            "Wins": [65, 35],
            "Losses": [35, 65]
        }, index=["Wins", "Losses"])
        st.bar_chart(win_data)


def positions_page():
    """Open positions page"""
    st.header("📋 Open Positions")
    
    # Sample positions
    positions = {
        "Ticket": [12345, 12346],
        "Symbol": ["EURUSD", "GBPUSD"],
        "Type": ["BUY", "SELL"],
        "Volume": [0.10, 0.05],
        "Open Price": [1.0825, 1.2680],
        "Current": [1.0852, 1.2654],
        "Profit": ["+$27.00", "-$13.00"],
        "SL": [1.0800, 1.2720],
        "TP": [1.0900, 1.2600]
    }
    
    df = pd.DataFrame(positions)
    st.dataframe(df, width='stretch')
    
    # Position controls
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Modify Position"):
            st.info("Select a position to modify")
    
    with col2:
        if st.button("Close Position", type="primary"):
            st.warning("Select a position to close")


def risk_settings_page():
    """Risk management settings"""
    st.header("⚙️ Risk Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Position Sizing")
        max_risk = st.slider("Max Risk per Trade (%)", 0.5, 5.0, 2.0)
        max_positions = st.slider("Max Open Positions", 1, 10, 5)
        st.write(f"Position size: ${10000 * max_risk / 100}")
    
    with col2:
        st.subheader("Stop Loss / Take Profit")
        atr_multiplier_sl = st.slider("ATR Multiplier (SL)", 1.0, 4.0, 2.0)
        atr_multiplier_tp = st.slider("ATR Multiplier (TP)", 2.0, 8.0, 4.0)
        min_risk_reward = st.slider("Min Risk:Reward", 1.0, 3.0, 1.5)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Safety Settings")
        kill_switch = st.checkbox("Enable Kill Switch", value=True)
        capital_protection = st.checkbox("Capital Protection Mode", value=True)
        drawdown_limit = st.slider("Max Daily Drawdown (%)", 1, 10, 5)
    
    with col2:
        st.subheader("Filters")
        news_filter = st.checkbox("News Volatility Filter", value=False)
        time_filter = st.checkbox("Trading Hours Filter", value=True)
        allowed_sessions = st.multiselect(
            "Allowed Sessions",
            ["Sydney", "Tokyo", "London", "New York"],
            default=["London", "New York"]
        )
    
    if st.button("Save Settings", type="primary"):
        st.success("Settings saved!")


def logs_page():
    """System logs"""
    st.header("📝 System Logs")
    
    # Log level filter
    log_level = st.selectbox("Log Level", ["ALL", "INFO", "WARNING", "ERROR"])
    
    # Sample logs
    logs = [
        ("2024-01-15 10:30:25", "INFO", "Trade executed: BUY EURUSD @ 1.0852"),
        ("2024-01-15 10:30:26", "INFO", "Position opened: Ticket #12345"),
        ("2024-01-15 10:25:00", "WARNING", "High volatility detected"),
        ("2024-01-15 10:20:15", "INFO", "Signal generated: BUY GBPUSD (confidence: 0.72)"),
        ("2024-01-15 10:15:00", "ERROR", "Order failed: Insufficient margin"),
    ]
    
    for timestamp, level, message in logs:
        if log_level == "ALL" or log_level == level:
            if level == "ERROR":
                st.error(f"`{timestamp}` [{level}] {message}")
            elif level == "WARNING":
                st.warning(f"`{timestamp}` [{level}] {message}")
            else:
                st.info(f"`{timestamp}` [{level}] {message}")
    
    if st.button("Clear Logs"):
        st.info("Logs cleared")


def backtest_page():
    """Backtesting page"""
    st.header("📊 Backtest")
    
    col1, col2 = st.columns(2)
    
    with col1:
        symbol = st.selectbox("Symbol", ["EURUSD", "GBPUSD", "USDJPY"])
        timeframe = st.selectbox("Timeframe", ["M5", "M15", "H1", "H4", "D1"])
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")
    
    with col2:
        initial_balance = st.number_input("Initial Balance", value=10000)
        risk_per_trade = st.slider("Risk per Trade (%)", 0.5, 5.0, 2.0)
    
    if st.button("Run Backtest", type="primary"):
        with st.spinner("Running backtest..."):
            time.sleep(2)  # Simulate
        
        # Results
        st.success("Backtest complete!")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Trades", "156")
        col2.metric("Win Rate", "62.5%")
        col3.metric("Net Profit", "$3,245.00")
        col4.metric("Max Drawdown", "8.2%")
        
        # Equity curve
        st.subheader("Equity Curve")
        chart_data = pd.DataFrame(
            np.cumsum(np.random.randn(100)) + 10000,
            columns=["Equity"]
        )
        st.line_chart(chart_data)


if __name__ == "__main__":
    main()
