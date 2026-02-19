"""
MT5 Execution Bridge for Trading System

This module handles order execution, position management,
and error handling for MetaTrader 5 trading.

Features:
- Market and limit order execution
- Position management (modify, close)
- Slippage protection
- Order retry logic
- Comprehensive logging

Author: AI Trading System
Version: 1.0.0
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

import MetaTrader5 as mt5

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order execution types."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


class OrderResult(Enum):
    """Order execution results."""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    PENDING = "pending"
    TIMEOUT = "timeout"


@dataclass
class OrderRequest:
    """
    Order request parameters.

    Attributes:
        symbol: Trading symbol
        order_type: Type of order (market, limit, stop)
        direction: Buy or Sell
        volume: Position size in lots
        price: Order price (for limit/stop orders)
        stop_loss: Stop loss price
        take_profit: Take profit price
        comment: Order comment
        magic: Expert advisor magic number
    """
    symbol: str
    order_type: OrderType = OrderType.MARKET
    direction: str = "buy"  # "buy" or "sell"
    volume: float = 0.01
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    comment: str = ""
    magic: int = 123456


@dataclass
class OrderResponse:
    """
    Order execution response.

    Attributes:
        result: Order result status
        order_id: MT5 order/ticket number
        price: Executed price
        volume: Executed volume
        message: Status message
        error_code: Error code if failed
        timestamp: Execution timestamp
    """
    result: OrderResult
    order_id: Optional[int]
    price: Optional[float]
    volume: Optional[float]
    message: str
    error_code: Optional[int] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ExecutionBridge:
    """
    MT5 execution bridge for order management.

    Responsibilities:
    - Execute market and pending orders
    - Modify existing orders/positions
    - Close positions
    - Handle errors and retries
    - Manage slippage protection
    """

    def __init__(
        self,
        max_slippage_pips: float = 2.0,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        timeout: int = 30
    ):
        self.max_slippage_pips = max_slippage_pips
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout

    def is_connected(self) -> bool:
        """Check if MT5 is connected."""
        return mt5.terminal_info() is not None

    def execute_order(self, request: OrderRequest) -> OrderResponse:
        """
        Execute an order with retry logic.

        Args:
            request: Order request parameters

        Returns:
            OrderResponse with execution results
        """
        if not self.is_connected():
            return OrderResponse(
                result=OrderResult.FAILED,
                order_id=None,
                price=None,
                volume=None,
                message="MT5 not connected",
                error_code=-1
            )

        # Validate symbol
        if not mt5.symbol_select(request.symbol, True):
            return OrderResponse(
                result=OrderResult.FAILED,
                order_id=None,
                price=None,
                volume=None,
                message=f"Symbol not available: {request.symbol}",
                error_code=-1
            )

        # Get symbol info for validation
        symbol_info = mt5.symbol_info(request.symbol)
        if symbol_info is None:
            return OrderResponse(
                result=OrderResult.FAILED,
                order_id=None,
                price=None,
                volume=None,
                message=f"Cannot get symbol info: {request.symbol}",
                error_code=-1
            )

        # Prepare order request
        order_type = self._get_order_type(request, symbol_info)
        price = request.price
        if request.order_type == OrderType.MARKET:
            price = self._get_market_price(request.direction, request.symbol)

        # Check slippage for market orders
        if request.order_type == OrderType.MARKET and price:
            slippage_check = self._check_slippage(
                request.direction,
                price,
                request.symbol
            )
            if not slippage_check['acceptable']:
                return OrderResponse(
                    result=OrderResult.FAILED,
                    order_id=None,
                    price=price,
                    volume=request.volume,
                    message=f"Slippage too high: {slippage_check['slippage']:.1f} pips",
                    error_code=-2
                )

        # Prepare MT5 order request
        mt5_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": request.symbol,
            "volume": request.volume,
            "type": order_type,
            "price": price,
            "sl": request.stop_loss if request.stop_loss else 0,
            "tp": request.take_profit if request.take_profit else 0,
            "deviation": int(self.max_slippage_pips * 10),  # Convert to points
            "magic": request.magic,
            "comment": request.comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        # Execute with retries
        for attempt in range(self.max_retries):
            try:
                result = mt5.order_send(mt5_request)

                if result is None:
                    error = mt5.last_error()
                    logger.error(f"Order send failed: {error}")
                    continue

                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    logger.info(
                        f"Order executed: {request.direction} {request.volume} "
                        f"{request.symbol} @ {result.price}, order={result.order}"
                    )
                    return OrderResponse(
                        result=OrderResult.SUCCESS,
                        order_id=result.order,
                        price=result.price,
                        volume=result.volume,
                        message=f"Order executed successfully",
                        timestamp=datetime.now()
                    )
                else:
                    logger.warning(
                        f"Order retcode {result.retcode}: {self._get_retcode_message(result.retcode)}"
                    )

                    # Check for retryable errors
                    if self._is_retryable(result.retcode):
                        time.sleep(self.retry_delay)
                        continue

                    return OrderResponse(
                        result=OrderResult.FAILED,
                        order_id=None,
                        price=price,
                        volume=request.volume,
                        message=self._get_retcode_message(result.retcode),
                        error_code=result.retcode
                    )

            except Exception as e:
                logger.error(f"Order execution error: {e}")
                time.sleep(self.retry_delay)

        return OrderResponse(
            result=OrderResult.FAILED,
            order_id=None,
            price=price,
            volume=request.volume,
            message="Max retries exceeded",
            error_code=-3
        )

    def close_position(self, ticket: int, volume: Optional[float] = None) -> OrderResponse:
        """
        Close an existing position.

        Args:
            ticket: Position ticket number
            volume: Volume to close (None = full position)

        Returns:
            OrderResponse with results
        """
        if not self.is_connected():
            return OrderResponse(
                result=OrderResult.FAILED,
                order_id=None,
                price=None,
                volume=None,
                message="MT5 not connected",
                error_code=-1
            )

        # Get position
        position = mt5.positions_get(ticket=ticket)
        if position is None or len(position) == 0:
            return OrderResponse(
                result=OrderResult.FAILED,
                order_id=None,
                price=None,
                volume=None,
                message=f"Position not found: {ticket}",
                error_code=-1
            )

        position = position[0]

        # Determine close volume
        close_volume = volume if volume else position.volume

        # Determine opposite direction
        direction = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY

        # Get current price
        symbol_info = mt5.symbol_info(position.symbol)
        if symbol_info is None:
            return OrderResponse(
                result=OrderResult.FAILED,
                order_id=None,
                price=None,
                volume=None,
                message="Cannot get symbol info",
                error_code=-1
            )

        price = symbol_info.bid if direction == mt5.ORDER_TYPE_SELL else symbol_info.ask

        # Prepare close request
        close_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": close_volume,
            "type": direction,
            "position": ticket,
            "price": price,
            "deviation": int(self.max_slippage_pips * 10),
            "magic": position.magic,
            "comment": "Close position",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        try:
            result = mt5.order_send(close_request)

            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"Position closed: {ticket}, volume: {close_volume}")
                return OrderResponse(
                    result=OrderResult.SUCCESS,
                    order_id=ticket,
                    price=result.price,
                    volume=result.volume,
                    message="Position closed",
                    timestamp=datetime.now()
                )
            else:
                msg = self._get_retcode_message(result.retcode) if result else "Unknown error"
                return OrderResponse(
                    result=OrderResult.FAILED,
                    order_id=ticket,
                    price=price,
                    volume=close_volume,
                    message=msg,
                    error_code=result.retcode if result else -1
                )

        except Exception as e:
            logger.error(f"Close position error: {e}")
            return OrderResponse(
                result=OrderResult.FAILED,
                order_id=ticket,
                price=price,
                volume=close_volume,
                message=str(e),
                error_code=-1
            )

    def modify_position(
        self,
        ticket: int,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> OrderResponse:
        """
        Modify position stop loss and take profit.

        Args:
            ticket: Position ticket number
            stop_loss: New stop loss price
            take_profit: New take profit price

        Returns:
            OrderResponse with results
        """
        if not self.is_connected():
            return OrderResponse(
                result=OrderResult.FAILED,
                order_id=None,
                price=None,
                volume=None,
                message="MT5 not connected",
                error_code=-1
            )

        # Get current position
        position = mt5.positions_get(ticket=ticket)
        if position is None or len(position) == 0:
            return OrderResponse(
                result=OrderResult.FAILED,
                order_id=None,
                price=None,
                volume=None,
                message=f"Position not found: {ticket}",
                error_code=-1
            )

        position = position[0]

        # Use current values if not provided
        sl = stop_loss if stop_loss is not None else position.sl
        tp = take_profit if take_profit is not None else position.tp

        # Prepare modification request
        modify_request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": position.symbol,
            "position": ticket,
            "sl": sl,
            "tp": tp,
            "magic": position.magic,
        }

        try:
            result = mt5.order_send(modify_request)

            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"Position modified: {ticket}, SL: {sl}, TP: {tp}")
                return OrderResponse(
                    result=OrderResult.SUCCESS,
                    order_id=ticket,
                    price=position.price_open,
                    volume=position.volume,
                    message="Position modified",
                    timestamp=datetime.now()
                )
            else:
                msg = self._get_retcode_message(result.retcode) if result else "Unknown error"
                return OrderResponse(
                    result=OrderResult.FAILED,
                    order_id=ticket,
                    price=position.price_open,
                    volume=position.volume,
                    message=msg,
                    error_code=result.retcode if result else -1
                )

        except Exception as e:
            logger.error(f"Modify position error: {e}")
            return OrderResponse(
                result=OrderResult.FAILED,
                order_id=ticket,
                price=position.price_open,
                volume=position.volume,
                message=str(e),
                error_code=-1
            )

    def get_open_positions(self) -> list:
        """Get all open positions."""
        if not self.is_connected():
            return []
        return mt5.positions_get()

    def get_position(self, ticket: int) -> Optional:
        """Get specific position by ticket."""
        if not self.is_connected():
            return None
        positions = mt5.positions_get(ticket=ticket)
        return positions[0] if positions else None

    def _get_order_type(self, request: OrderRequest, symbol_info) -> int:
        """Convert order type to MT5 constant."""
        direction = mt5.ORDER_TYPE_BUY if request.direction == "buy" else mt5.ORDER_TYPE_SELL

        if request.order_type == OrderType.MARKET:
            return direction

        # For pending orders
        if request.order_type == OrderType.LIMIT:
            return mt5.ORDER_TYPE_BUY_LIMIT if request.direction == "buy" else mt5.ORDER_TYPE_SELL_LIMIT
        elif request.order_type == OrderType.STOP:
            return mt5.ORDER_TYPE_BUY_STOP if request.direction == "buy" else mt5.ORDER_TYPE_SELL_STOP

        return direction

    def _get_market_price(self, direction: str, symbol: str) -> float:
        """Get current market price."""
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return 0

        if direction == "buy":
            return symbol_info.ask
        else:
            return symbol_info.bid

    def _check_slippage(self, direction: str, order_price: float, symbol: str) -> dict:
        """Check if slippage is within acceptable range."""
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return {'acceptable': True, 'slippage': 0}

        market_price = symbol_info.ask if direction == "buy" else symbol_info.bid
        slippage_pips = abs(order_price - market_price) / symbol_info.point / 10

        return {
            'acceptable': slippage_pips <= self.max_slippage_pips,
            'slippage': slippage_pips
        }

    def _is_retryable(self, retcode: int) -> bool:
        """Check if error is retryable."""
        retryable_codes = [
            mt5.TRADE_RETCODE_REQUOTE,
            mt5.TRADE_RETCODE_PRICE_CHANGED,
            mt5.TRADE_RETCODE_PRICE_OFF,
        ]
        return retcode in retryable_codes

    def _get_retcode_message(self, retcode: int) -> str:
        """Get human-readable message for MT5 return code."""
        messages = {
            mt5.TRADE_RETCODE_DONE: "Order done",
            mt5.TRADE_RETCODE_REQUOTE: "Requote",
            mt5.TRADE_RETCODE_REJECT: "Order rejected",
            mt5.TRADE_RETCODE_CANCEL: "Order canceled",
            mt5.TRADE_RETCODE_PLACED: "Order placed",
            mt5.TRADE_RETCODE_NOCHANGES: "No changes",
            mt5.TRADE_RETCODE_NOERROR: "No error",
            mt5.TRADE_RETCODE_PRICE_CHANGED: "Price changed",
            mt5.TRADE_RETCODE_PRICE_OFF: "Price off",
            mt5.TRADE_RETCODE_INVALID_VOLUME: "Invalid volume",
            mt5.TRADE_RETCODE_INVALID_PRICE: "Invalid price",
            mt5.TRADE_RETCODE_INVALID_STOPS: "Invalid stops",
            mt5.TRADE_RETCODE_TRADE_DISABLED: "Trading disabled",
            mt5.TRADE_RETCODE_NO_MONEY: "Insufficient funds",
            mt5.TRADE_RETCODE_PRICE_CHANGED: "Price changed",
            mt5.TRADE_RETCODE_TIMEOUT: "Timeout",
        }
        return messages.get(retcode, f"Unknown error: {retcode}")


# Factory function
def create_execution_bridge(
    max_slippage_pips: float = 2.0,
    max_retries: int = 3
) -> ExecutionBridge:
    """Create execution bridge instance."""
    return ExecutionBridge(
        max_slippage_pips=max_slippage_pips,
        max_retries=max_retries
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("MT5 Execution Bridge Test")
    print("=" * 60)

    bridge = ExecutionBridge(max_slippage_pips=2.0, max_retries=3)

    if bridge.is_connected():
        print("✓ MT5 Connected")

        # Get positions
        positions = bridge.get_open_positions()
        print(f"Open positions: {len(positions)}")
    else:
        print("✗ MT5 not connected (expected without terminal)")

    print("\n" + "=" * 60)
    print("Execution Bridge - Complete")
    print("=" * 60)
