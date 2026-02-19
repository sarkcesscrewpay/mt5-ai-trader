"""
Live Trading Script - AI-Powered MT5 Trading System
"""

import sys
import os
import time
import logging
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    print("=" * 60)
    print("MT5 LIVE TRADING SYSTEM")
    print("=" * 60)
    print()
    
    # Check if MetaTrader5 is available
    try:
        import MetaTrader5 as mt5
        print("[OK] MetaTrader5 package found")
    except ImportError:
        print("[ERROR] MetaTrader5 not installed")
        print("")
        print("REQUIREMENTS:")
        print("1. Install MetaTrader5 Python package:")
        print("   pip install MetaTrader5")
        print("")
        print("2. Install MetaTrader 5 terminal:")
        print("   Download from your broker or mql5.com")
        print("")
        print("3. Have MT5 terminal running and logged in")
        print("")
        return
    
    # Initialize MT5
    if not mt5.initialize():
        print(f"[ERROR] MT5 initialize failed: {mt5.last_error()}")
        return
    
    print("[OK] Connected to MT5")
    
    # Get account info
    account_info = mt5.account_info()
    if account_info is None:
        print("[ERROR] Could not get account info")
        mt5.shutdown()
        return
    
    print(f"  Account: {account_info.login}")
    print(f"  Server: {account_info.server}")
    print(f"  Balance: ${account_info.balance:.2f}")
    print(f"  Equity: ${account_info.equity:.2f}")
    print()
    
    print("[OK] Trading system ready!")
    print("  The bot will check for trading signals every 60 seconds")
    print("  Press Ctrl+C to stop")
    print()
    
    # Trading loop - runs continuously
    symbols = ["EURUSD"]
    
    try:
        while True:
            current_time = datetime.now()
            print(f"\n[{current_time}] Checking markets...")
            
            for symbol in symbols:
                # Get live price
                symbol_info = mt5.symbol_info(symbol)
                if symbol_info is None:
                    continue
                    
                if not symbol_info.visible:
                    mt5.symbol_select(symbol, True)
                
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    print(f"  {symbol}: Bid={tick.bid:.5f}, Ask={tick.ask:.5f}")
            
            print("  Sleeping 60s... (Ctrl+C to stop)")
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\n\nStopping...")
    
    mt5.shutdown()
    print("[OK] Disconnected")


if __name__ == "__main__":
    main()
