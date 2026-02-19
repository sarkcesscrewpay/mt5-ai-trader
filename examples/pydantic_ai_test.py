"""
Example demonstrating the JSON serialization fix for Pydantic AI integration.

This example shows that the copy_rates_from_pos function now returns
JSON-serializable data that works with Pydantic AI and MCP protocol.
"""

import asyncio
import json
from datetime import datetime

# This example demonstrates the fix without requiring actual MT5 connection


def demonstrate_json_serialization():
    """Show that the returned data structure is JSON-serializable"""

    # Simulated response from copy_rates_from_pos after the fix
    mock_response = [
        {
            "time": "2024-01-22T10:00:00",  # Now a string, not Timestamp!
            "open": 1.0850,
            "high": 1.0865,
            "low": 1.0845,
            "close": 1.0860,
            "tick_volume": 1250,
            "spread": 2,
            "real_volume": 125000,
        },
        {
            "time": "2024-01-22T11:00:00",
            "open": 1.0860,
            "high": 1.0875,
            "low": 1.0855,
            "close": 1.0870,
            "tick_volume": 1100,
            "spread": 2,
            "real_volume": 110000,
        },
    ]

    # This will now work - before the fix, this would fail!
    try:
        json_str = json.dumps(mock_response, indent=2)
        print("✅ JSON Serialization Successful!")
        print("\nJSON Output:")
        print(json_str)
        return True
    except (TypeError, ValueError) as e:
        print(f"❌ JSON Serialization Failed: {e}")
        return False


def demonstrate_datetime_parsing():
    """Show how to parse the ISO format datetime strings if needed"""

    time_str = "2024-01-22T10:00:00"

    # Parse back to datetime if needed
    dt = datetime.fromisoformat(time_str)
    print(f"\n✅ DateTime parsing successful!")
    print(f"Original string: {time_str}")
    print(f"Parsed datetime: {dt}")
    print(f"Type: {type(dt)}")


async def demonstrate_pydantic_ai_usage():
    """
    Pseudo-code example showing how this works with Pydantic AI.
    
    Note: This is a conceptual example. For actual implementation,
    see the pydantic_ai_integration.md documentation.
    """
    print("\n" + "=" * 60)
    print("Pydantic AI Integration Example (Conceptual)")
    print("=" * 60)

    # When using with Pydantic AI through MCP:
    # 1. Agent calls the tool through MCP protocol
    # 2. Tool returns JSON-serializable data (now works!)
    # 3. MCP serializes the response to JSON
    # 4. Agent receives and processes the data

    example_tool_call = {
        "tool": "copy_rates_from_pos",
        "arguments": {"symbol": "EURUSD", "timeframe": 60, "start_pos": 0, "count": 100},
    }

    example_response = {
        "success": True,
        "data": [
            {
                "time": "2024-01-22T10:00:00",
                "open": 1.0850,
                "high": 1.0865,
                "low": 1.0845,
                "close": 1.0860,
                "tick_volume": 1250,
                "spread": 2,
                "real_volume": 125000,
            }
        ],
    }

    print(f"\nTool Call: {json.dumps(example_tool_call, indent=2)}")
    print(f"\nTool Response (JSON-serializable): {json.dumps(example_response, indent=2)}")
    print("\n✅ This now works with Pydantic AI!")


if __name__ == "__main__":
    print("=" * 60)
    print("MT5 MCP Server - JSON Serialization Fix Demonstration")
    print("=" * 60)

    # Test 1: JSON serialization
    print("\n1. Testing JSON Serialization")
    print("-" * 60)
    demonstrate_json_serialization()

    # Test 2: DateTime parsing
    print("\n2. Testing DateTime Parsing")
    print("-" * 60)
    demonstrate_datetime_parsing()

    # Test 3: Pydantic AI conceptual example
    asyncio.run(demonstrate_pydantic_ai_usage())

    print("\n" + "=" * 60)
    print("All demonstrations completed successfully! ✅")
    print("=" * 60)
