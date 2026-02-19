"""
PyInstaller Build Script for MT5 Trading System

Build Windows executable:
    pip install pyinstaller
    python setup_windows.py

Usage:
    python setup_windows.py build
"""

import os
import sys
import shutil
from pathlib import Path

# Configuration
APP_NAME = "MT5_Trading_Bot"
VERSION = "1.0.0"
AUTHOR = "AI Trading System"
DESCRIPTION = "AI-Powered MetaTrader 5 Trading System"

# Source files
SOURCE_DIR = Path("src/mcp_mt5/trading")
MAIN_SCRIPT = SOURCE_DIR / "starter_example.py"

# Hidden imports for PyInstaller
HIDDEN_IMPORTS = [
    "numpy",
    "pandas", 
    "scikit_learn",
    "xgboost",
    "lightgbm",
    "yaml",
    "dotenv",
]

# Data files to include
DATA_FILES = [
    ("config", "config"),
]

def build_exe():
    """Build Windows executable using PyInstaller."""
    print("=" * 60)
    print(f"Building {APP_NAME} v{VERSION}")
    print("=" * 60)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        os.system("pip install pyinstaller")
    
    # Build command
    cmd = [
        "pyinstaller",
        "--name=" + APP_NAME,
        "--onefile",  # Single executable
        "--windowed",  # No console window
        f"--add-data=config;config",  # Include config
        "--hidden-import=numpy",
        "--hidden-import=pandas", 
        "--hidden-import=scipy",
        "--hidden-import=sklearn",
        "--hidden-import=xgboost",
        "--hidden-import=lightgbm",
        "--hidden-import=MetaTrader5",
        "--hidden-import=dotenv",
        "--collect-all=xgboost",
        "--collect-all=lightgbm",
        "--clean",
        "--noconfirm",
        str(MAIN_SCRIPT)
    ]
    
    print("\nRunning PyInstaller...")
    print("Command:", " ".join(cmd))
    print()
    
    os.system(" ".join(cmd))
    
    # Copy executable to root
    dist_dir = Path("dist")
    exe_path = dist_dir / f"{APP_NAME}.exe"
    
    if exe_path.exists():
        print(f"\n✅ Build successful!")
        print(f"   Executable: {exe_path.absolute()}")
        print(f"   Size: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
    else:
        print(f"\n❌ Build failed. Check dist/ folder.")

def create_config():
    """Create default configuration files."""
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    # Create default config
    config_content = """# MT5 Trading Bot Configuration
system:
  mode: paper_trading
  symbols:
    - EURUSD
    - GBPUSD
    - USDJPY
  max_concurrent_trades: 5

data:
  timeframe: H1
  lookback_periods: 1000
  update_interval: 300

ai_model:
  model_type: xgboost
  min_confidence: 0.65
  retrain_frequency: weekly

risk:
  max_risk_per_trade: 0.02
  max_daily_drawdown: 0.05
  max_open_positions: 5
  atr_multiplier_sl: 2.0
  atr_multiplier_tp: 4.0

execution:
  slippage_protection: true
  max_slippage_pips: 2

safety:
  kill_switch_enabled: true
  capital_protection_mode: true
"""
    
    (config_dir / "trading_config.yaml").write_text(config_content)
    print(f"Created config/trading_config.yaml")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        create_config()
        build_exe()
    else:
        print(f"""
{APP_NAME} v{VERSION} - Build Script

Usage:
    python setup_windows.py build    # Build executable
    
Requirements:
    pip install pyinstaller numpy pandas scikit-learn xgboost lightgbm
    
Note: MetaTrader5 package requires Windows and MT5 terminal installed.
""")

if __name__ == "__main__":
    main()
