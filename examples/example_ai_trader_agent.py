"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           ⚠️  EDUCATIONAL USE ONLY ⚠️                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

DISCLAIMER: This trading agent example is provided for EDUCATIONAL and
DEMONSTRATION purposes ONLY. It is NOT financial advice and should NOT be used
with real money or live trading accounts.

⚠️  CRITICAL WARNINGS:
    • Algorithmic trading carries substantial risk of financial loss
    • Past performance does not guarantee future results
    • This code has NOT been tested in production environments
    • Using this with real funds may result in complete capital loss
    • No warranty or guarantee of profitability is provided

📋 BEFORE USING THIS CODE:
    • Thoroughly test on demo accounts only
    • Understand all risks involved in automated trading
    • Consult with licensed financial advisors
    • Comply with all applicable financial regulations
    • Never risk money you cannot afford to lose

By using this code, you acknowledge that you are solely responsible for any
financial losses or damages. The authors and contributors are not liable for
any trading losses or issues arising from the use of this software.

For educational purposes only. Use at your own risk.
"""

import asyncio
import os
from typing import Literal

import dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

dotenv.load_dotenv()

# Validate required environment variables
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_MODEL:
    raise ValueError(
        "OPENROUTER_MODEL environment variable is required.\n"
        "Please set it in your .env file or environment:\n"
        "  OPENROUTER_MODEL=mistralai/mistral-small-3.2-24b-instruct:free\n"
        "See https://openrouter.ai/models for available models."
    )

if not OPENROUTER_API_KEY:
    raise ValueError(
        "OPENROUTER_API_KEY environment variable is required.\n"
        "Please set it in your .env file or environment:\n"
        "  OPENROUTER_API_KEY=your_api_key_here\n"
        "Get your API key from https://openrouter.ai/keys"
    )


# Define structured output for trading decisions
class TradingDecision(BaseModel):
    """Autonomous trading decision with risk management"""

    symbol: str = Field(description="Trading symbol (e.g., EURUSD)")
    action: Literal["BUY", "SELL", "HOLD", "CLOSE"] = Field(description="Trading action to take")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence level 0-1")
    entry_price: float | None = Field(default=None, description="Planned entry price")
    stop_loss_pips: float | None = Field(default=None, description="Stop loss distance in pips")
    take_profit_pips: float | None = Field(default=None, description="Take profit distance in pips")
    reasoning: str = Field(description="Detailed reasoning for the decision")
    market_condition: str = Field(description="Current market condition assessment")


# Setup MCP server for MetaTrader 5
mt5_server = MCPServerStdio("uv", args=["run", "mt5mcp"], timeout=60)

# Create the AI model with validated credentials
model = OpenAIChatModel(
    OPENROUTER_MODEL,
    provider=OpenRouterProvider(api_key=OPENROUTER_API_KEY),
)

# Create the automated trading agent
trading_agent = Agent(
    model,
    output_type=TradingDecision,
    system_prompt="""You are an AUTONOMOUS forex trading agent with real money management responsibility.

    CRITICAL RULES:
    1. ALWAYS prioritize capital preservation - losing trades must be minimized
    2. Use STRICT risk management - stop losses are MANDATORY
    3. Only trade when you have HIGH confidence (>0.7)
    4. Never revenge trade - accept losses and move on
    5. Respect maximum concurrent positions limit
    6. Use technical analysis: support/resistance, trends, momentum, volume
    7. Consider market sessions and volatility

    TRADING STRATEGY:
    - Identify clear trends and trade with them
    - Wait for pullbacks to support/resistance for better entries
    - Set stop loss at recent swing low/high + buffer
    - Target 2:1 or 3:1 risk-reward ratio minimum
    - Monitor existing positions and close if conditions reverse
    - Avoid trading during high-impact news events
    - Scale position size based on confidence and volatility

    POSITION SIZING:
    - Risk is automatically calculated at 1% of account per trade
    - Stop loss distance determines position size
    - Recommend stop losses between 20-50 pips for major pairs
    - Take profits should be 40-150 pips (aim for 2:1+ RR)

    DECISION OUTPUTS:
    - BUY: Open long position with specified SL/TP
    - SELL: Open short position with specified SL/TP
    - HOLD: No trade opportunity meets criteria
    - CLOSE: Close existing position if conditions changed

    Available MT5 tools:
    - initialize, copy_rates_from_pos, get_symbol_info_tick
    - get_account_info, positions_get, order_send, shutdown

    Your goal: Achieve consistent profitability through disciplined, high-probability trading.""",
    toolsets=[mt5_server],
    retries=2,
)


async def run_trading_agent():
    """
    Run the trading agent with proper MCP server lifecycle management.

    The async context manager ensures the MCP server is started before use
    and properly shut down after completion or on errors.
    """
    try:
        # Use async context manager to handle MCP server lifecycle
        async with trading_agent:
            print("🤖 Trading agent started with MCP server connection...")

            decision = await trading_agent.run("Should I buy or sell XAUUSD?")
            print(f"\nDecision: {decision}")
            # Implement actual trading logic here

            print("\n✅ Trading agent completed successfully")
        # MCP server is automatically shut down here

    except ModelHTTPError as e:
        print(f"❌ Model error: {e}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise
    finally:
        print("\n🔒 MCP server connection closed")


if __name__ == "__main__":
    asyncio.run(run_trading_agent())
