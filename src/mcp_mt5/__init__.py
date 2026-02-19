"""MetaTrader 5 MCP Server"""

# Don't auto-import main.py to avoid MetaTrader5 dependency for trading modules
__version__ = "0.1.4"

def get_mcp():
    """Lazy load MCP server to avoid MT5 dependency"""
    from .main import mcp
    return mcp

mcp = property(lambda self: get_mcp())

def main():
    """Entry point for the MCP server CLI"""
    import os
    from dotenv import load_dotenv
    load_dotenv()
    transport = os.getenv("MT5_MCP_TRANSPORT", "stdio")
    if transport == "http":
        host = os.getenv("MT5_MCP_HOST", "127.0.0.1")
        port = int(os.getenv("MT5_MCP_PORT", "8000"))
        get_mcp().run(transport="http", host=host, port=port)
    else:
        get_mcp().run(transport="stdio")

# Export trading submodule
from . import trading

__all__ = ["main", "get_mcp", "trading"]
