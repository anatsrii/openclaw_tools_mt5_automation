#!/usr/bin/env python3
"""
MT5 Notifier - Usage Examples

Practical examples of notification usage.
"""

from tools.notify import (
    MT5Notifier,
    send,
    send_trade_alert,
    send_daily_report,
    send_error,
    send_bot_status,
    test_connection,
    get_enabled_channels
)


# ==============================================================================
# EXAMPLE 1: Simple Message
# ==============================================================================
def example_simple_message():
    """Example: Send a simple message."""
    print("\n=== Example 1: Simple Message ===")

    # Send info message
    result = send("Trading system is online", severity="info")
    print(f"Status: {result['status']}")
    print(f"Sent to: {result['sent_to']}")

    # Send warning
    result = send("Large position detected", severity="warning")
    print(f"Warning sent: {result['status']}")


# ==============================================================================
# EXAMPLE 2: Trade Notifications
# ==============================================================================
def example_trade_notifications():
    """Example: Send trading notifications."""
    print("\n=== Example 2: Trade Notifications ===")

    # BUY signal
    send_trade_alert(
        action="BUY",
        symbol="EURUSD",
        volume=0.1,
        entry_price=1.0850,
        comment="Moving average breakout"
    )
    print("✓ Buy signal sent")

    # SELL with profit
    send_trade_alert(
        action="CLOSE",
        symbol="EURUSD",
        volume=0.1,
        profit=+250.50,
        comment="TP1 reached"
    )
    print("✓ Close (Profit) sent")

    # SELL with loss
    send_trade_alert(
        action="CLOSE",
        symbol="GBPUSD",
        profit=-100.00,
        comment="SL hit"
    )
    print("✓ Close (Loss) sent")


# ==============================================================================
# EXAMPLE 3: Daily Report
# ==============================================================================
def example_daily_report():
    """Example: Send daily trading report."""
    print("\n=== Example 3: Daily Report ===")

    send_daily_report(
        total_profit=500.75,
        trade_count=8,
        wins=5,
        losses=3,
        max_drawdown=3.2,
        date="2025-02-19"
    )

    print("✓ Daily report sent")
    # Output:
    # 📊 DAILY REPORT - 2025-02-19
    # 💰 Total P/L: +500.75
    # 📈 Trades: 8 (5W / 3L)
    # 🎯 Win Rate: 62.5%
    # 📉 Max Drawdown: 3.20%


# ==============================================================================
# EXAMPLE 4: Error Handling
# ==============================================================================
def example_error_handling():
    """Example: Send error notifications."""
    print("\n=== Example 4: Error Handling ===")

    try:
        # Simulate error
        result = 1 / 0
    except Exception as e:
        send_error(
            source="trading_engine",
            error_message=str(e),
            ea_name="MyEA"
        )
        print("✓ Error alert sent")


# ==============================================================================
# EXAMPLE 5: Bot Status
# ==============================================================================
def example_bot_status():
    """Example: Send bot status notifications."""
    print("\n=== Example 5: Bot Status ===")

    # Started
    send_bot_status(
        status="started",
        ea_name="ScalpingBot",
        details="Connected to demo account | Memory: 125 MB"
    )
    print("✓ Bot started notification")

    # Working fine
    send(
        "ScalpingBot: 5 trades, +225 pips",
        severity="info"
    )
    print("✓ Status update sent")

    # Crashed
    send_bot_status(
        status="crashed",
        ea_name="ScalpingBot",
        details="Connection lost to order server"
    )
    print("✓ Bot crashed alert sent")


# ==============================================================================
# EXAMPLE 6: Severity Filtering
# ==============================================================================
def example_severity_filtering():
    """Example: Control message levels."""
    print("\n=== Example 6: Severity Filtering ===")

    notifier = MT5Notifier()

    # Set minimum severity to "warning"
    notifier.set_min_severity("warning")
    print("Set minimum severity to: warning\n")

    # These messages will be SKIPPED
    result = notifier.send("Debug info", severity="debug", async_send=False)
    print(f"Debug message: {result['status']} (skipped)")

    result = notifier.send("Info message", severity="info", async_send=False)
    print(f"Info message: {result['status']} (skipped)")

    # These messages will be SENT
    result = notifier.send("Warning!", severity="warning", async_send=False)
    print(f"Warning message: {result['status']} (sent)")

    result = notifier.send("CRITICAL!", severity="critical", async_send=False)
    print(f"Critical message: {result['status']} (sent)")


# ==============================================================================
# EXAMPLE 7: Multi-Channel Notifications
# ==============================================================================
def example_multichanne():
    """Example: Send to specific channels."""
    print("\n=== Example 7: Multi-Channel ===")

    # Get enabled channels
    channels = get_enabled_channels()
    print(f"Enabled channels: {channels}\n")

    # Send to all enabled
    send("Alert to all channels", severity="warning")
    print("✓ Sent to all channels")

    # Send to specific channel
    if "telegram" in channels:
        send(
            "Only to Telegram",
            severity="info",
            channel="telegram"
        )
        print("✓ Sent to Telegram only")

    if "line" in channels:
        send(
            "Only to Line",
            severity="info",
            channel="line"
        )
        print("✓ Sent to Line only")


# ==============================================================================
# EXAMPLE 8: Async Non-blocking
# ==============================================================================
def example_async_notifications():
    """Example: Async message queuing."""
    print("\n=== Example 8: Async Queuing ===")

    # Queue multiple messages quickly (non-blocking)
    for i in range(5):
        result = send(
            f"Trade {i+1} closed",
            severity="info",
            async_send=True  # Queue immediately
        )
        print(f"Message {i+1}: {result['status']} (instant return)")

    print("\n✓ All messages queued and being processed in background")


# ==============================================================================
# EXAMPLE 9: Test Connections
# ==============================================================================
def example_test_connections():
    """Example: Verify channel connections."""
    print("\n=== Example 9: Connection Test ===")

    result = test_connection()

    if result["status"] == "success":
        print("✓ All channels connected\n")
    else:
        print(f"Partial success: {result['status']}\n")

    for channel, success in result.get("results", {}).items():
        status = "✓" if success else "✗"
        print(f"  {status} {channel}")


# ==============================================================================
# EXAMPLE 10: Complete Trading Bot
# ==============================================================================
def example_trading_bot_integration():
    """Example: Complete trading bot integration."""
    print("\n=== Example 10: Trading Bot Integration ===")

    class TradingBot:
        def __init__(self, name):
            self.name = name
            self.trades = []

        def start(self):
            send_bot_status("started", self.name, "All systems online")
            print("✓ Bot started")

        def on_trade_open(self, symbol, action, volume, price):
            send_trade_alert(
                action=action,
                symbol=symbol,
                volume=volume,
                entry_price=price
            )
            print(f"✓ {action} {symbol} {volume} sent")

        def on_trade_close(self, symbol, profit, comment=""):
            send_trade_alert(
                action="CLOSE",
                symbol=symbol,
                profit=profit,
                comment=comment
            )
            print(f"✓ Close {symbol} {profit:+.2f} sent")

        def on_error(self, error):
            send_error(
                source="bot_engine",
                error_message=error,
                ea_name=self.name
            )
            print("✓ Error alert sent")

        def send_daily_summary(self, stats):
            send_daily_report(
                total_profit=stats['profit'],
                trade_count=stats['trades'],
                wins=stats['wins'],
                losses=stats['losses'],
                max_drawdown=stats['drawdown']
            )
            print("✓ Daily report sent")

    # Usage
    bot = TradingBot("MyRobot")

    # Lifecycle
    bot.start()
    bot.on_trade_open("EURUSD", "BUY", 0.1, 1.0850)
    bot.on_trade_close("EURUSD", +150.50, "TP reached")
    bot.on_trade_open("GBPUSD", "SELL", 0.2, 1.2750)
    bot.on_trade_close("GBPUSD", -80.25, "SL hit")

    bot.send_daily_summary({
        'profit': 70.25,
        'trades': 2,
        'wins': 1,
        'losses': 1,
        'drawdown': 2.5
    })

    print("\n✓ Complete bot workflow executed")


# ==============================================================================
# Main
# ==============================================================================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("MT5 Notifier - Examples")
    print("=" * 60)

    examples = [
        ("Simple Message", example_simple_message),
        ("Trade Notifications", example_trade_notifications),
        ("Daily Report", example_daily_report),
        ("Error Handling", example_error_handling),
        ("Bot Status", example_bot_status),
        ("Severity Filtering", example_severity_filtering),
        ("Multi-Channel", example_multichanne),
        ("Async Queuing", example_async_notifications),
        ("Test Connections", example_test_connections),
        ("Trading Bot", example_trading_bot_integration),
    ]

    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    while True:
        try:
            choice = input("\nSelect example (1-10) or 'q' to quit: ").strip()
            if choice.lower() == 'q':
                break

            idx = int(choice) - 1
            if 0 <= idx < len(examples):
                try:
                    examples[idx][1]()
                except Exception as e:
                    print(f"Error: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("Invalid selection")
        except ValueError:
            print("Please enter a number")
        except KeyboardInterrupt:
            print("\nStopped")
            break
