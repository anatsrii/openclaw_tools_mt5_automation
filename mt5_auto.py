#!/usr/bin/env python3
"""
MT5 Automation CLI - Unified Command Interface

Usage:
    python mt5_auto.py status          - Show MT5 status
    python mt5_auto.py compile EA      - Compile and deploy EA
    python mt5_auto.py backtest EA SYMBOL TF START END  - Run backtest
    python mt5_auto.py close-all       - Emergency close all positions
    python mt5_auto.py report          - Generate trading report
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MT5CLI:
    """CLI interface for MT5 automation."""

    def __init__(self):
        """Initialize CLI."""
        self.project_root = PROJECT_ROOT

    def status(self, args) -> int:
        """
        Show MT5 status.

        Returns:
            0 if healthy, 1 if degraded/critical
        """
        try:
            from tools.process import get_mt5_status, watch_mt5
            from tools.scheduler import get_current_session
            from tools.manager import get_system_health

            print("\n" + "=" * 70)
            print("  MT5 Automation Status Report")
            print("=" * 70)

            # MT5 Process Status
            print("\n[Process Control]")
            mt5_status = get_mt5_status()
            print(f"  MT5 Running:     {'✅ Yes' if mt5_status.get('is_running') else '❌ No'}")
            if mt5_status.get('pid'):
                print(f"  Process ID:      {mt5_status['pid']}")
            if mt5_status.get('memory_mb'):
                print(f"  Memory Usage:    {mt5_status['memory_mb']:.1f} MB")
            if mt5_status.get('cpu_percent'):
                print(f"  CPU Usage:       {mt5_status['cpu_percent']:.1f}%")

            # Market Session Status
            print("\n[Market Session]")
            session = get_current_session()
            if session.get('status') == 'success':
                sessions = session.get('sessions', [])
                print(f"  Active Sessions: {', '.join(sessions) if sessions else 'None'}")
                print(f"  Local Time:      {session.get('local_time')}")
                print(f"  Is Weekend:      {'Yes' if session.get('is_weekend') else 'No'}")
            else:
                print(f"  Error: {session.get('error', 'Unknown')}")

            # System Health
            print("\n[System Health]")
            health = get_system_health()
            health_status = health.get('status', 'unknown')
            health_icon = '✅' if health_status == 'healthy' else '⚠️' if health_status == 'degraded' else '❌'
            print(f"  Status:          {health_icon} {health_status.upper()}")
            print(f"  Active Bots:     {health.get('active_bots', 0)}")
            print(f"  Connection:      {health.get('connection_quality', 'unknown')}")

            print("\n" + "=" * 70)

            # Return status code
            if health_status == 'healthy':
                return 0
            else:
                return 1

        except Exception as e:
            logger.error(f"Status check failed: {str(e)}", exc_info=True)
            print(f"❌ Error: {str(e)}")
            return 1

    def compile(self, args) -> int:
        """
        Compile and deploy EA.

        Args:
            args.ea: EA name to compile
            args.symbol: Optional symbol (auto-detect if not specified)
            args.timeframe: Optional timeframe (default M30)

        Returns:
            0 if successful, 1 if failed
        """
        try:
            from tools.developer import compile_and_fix, deploy_ea
            from tools.process import get_mt5_status
            from tools.notify import send

            ea_name = args.ea
            symbol = getattr(args, 'symbol', None) or 'EURUSD'
            timeframe = getattr(args, 'timeframe', None) or '30'

            print(f"\n{'=' * 70}")
            print(f"  Compiling EA: {ea_name}")
            print(f"{'=' * 70}\n")

            # Ensure MT5 is running
            status = get_mt5_status()
            if not status.get('is_running'):
                print("⏳ MT5 not running, starting...")
                from tools.process import start_mt5
                start_mt5()
                import time
                time.sleep(5)

            # Compile with auto-fix
            print(f"🔨 Compiling {ea_name}...")
            result = compile_and_fix(ea_name, max_attempts=3)

            if result.get('success'):
                print(f"✅ Compilation successful!")

                # Deploy to chart
                print(f"📊 Deploying to {symbol} {timeframe}...")
                deploy_result = deploy_ea(ea_name, symbol, timeframe)

                if deploy_result.get('success'):
                    print(f"✅ Deployed to {symbol} {timeframe}")
                    send(f"✅ {ea_name} deployed to {symbol} {timeframe}", severity="info")
                    print(f"\n{'=' * 70}")
                    return 0
                else:
                    print(f"⚠️  Deploy warning: {deploy_result.get('error')}")
                    send(f"⚠️  {ea_name} compiled but deploy warning: {deploy_result.get('error')}", severity="warning")
                    print(f"\n{'=' * 70}")
                    return 1
            else:
                error_count = len(result.get('final_errors', []))
                print(f"❌ Compilation failed with {error_count} errors remaining:")
                for error in result.get('final_errors', [])[:5]:  # Show first 5
                    print(f"   - {error}")
                if error_count > 5:
                    print(f"   ... and {error_count - 5} more errors")

                send(f"❌ {ea_name} compilation failed with {error_count} errors", severity="critical")
                print(f"\n{'=' * 70}")
                return 1

        except Exception as e:
            logger.error(f"Compile failed: {str(e)}", exc_info=True)
            print(f"❌ Error: {str(e)}")
            return 1

    def backtest(self, args) -> int:
        """
        Run backtest on EA.

        Args:
            args.ea: EA name
            args.symbol: Trading symbol
            args.timeframe: Timeframe (M1, M5, M15, M30, H1, etc.)
            args.start_date: Start date (YYYY-MM-DD)
            args.end_date: End date (YYYY-MM-DD)

        Returns:
            0 if successful, 1 if failed
        """
        try:
            from tools.tester import run_backtest
            from tools.notify import send

            ea_name = args.ea
            symbol = args.symbol
            timeframe = args.timeframe
            start_date = args.start_date
            end_date = args.end_date

            print(f"\n{'=' * 70}")
            print(f"  Backtest: {ea_name}")
            print(f"  Symbol: {symbol} | TF: {timeframe} | Period: {start_date} to {end_date}")
            print(f"{'=' * 70}\n")

            print(f"⏳ Running backtest (this may take a few minutes)...")
            result = run_backtest(
                ea_name=ea_name,
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )

            if result.get('status') == 'success':
                report = result.get('report', {})
                print(f"✅ Backtest completed!")
                print(f"\n  Results:")
                print(f"    Total Net Profit:    ${report.get('total_net_profit', 0):.2f}")
                print(f"    Total Trades:        {report.get('total_trades', 0)}")
                print(f"    Win Rate:            {report.get('win_rate', 0):.1f}%")
                print(f"    Profit Factor:       {report.get('profit_factor', 0):.2f}")
                print(f"    Max Drawdown:        {report.get('max_drawdown', 0):.2f}%")
                print(f"    Sharpe Ratio:        {report.get('sharpe_ratio', 0):.2f}")

                send(
                    f"✅ Backtest {ea_name}/{symbol}/{timeframe}: "
                    f"Profit ${report.get('total_net_profit', 0):.2f}, "
                    f"Win Rate {report.get('win_rate', 0):.1f}%, "
                    f"Trades {report.get('total_trades', 0)}",
                    severity="info"
                )
                print(f"\n{'=' * 70}")
                return 0
            else:
                error = result.get('error', 'Unknown error')
                print(f"❌ Backtest failed: {error}")
                send(f"❌ Backtest {ea_name}/{symbol} failed: {error}", severity="critical")
                print(f"\n{'=' * 70}")
                return 1

        except Exception as e:
            logger.error(f"Backtest failed: {str(e)}", exc_info=True)
            print(f"❌ Error: {str(e)}")
            return 1

    def close_all(self, args) -> int:
        """
        Emergency close all open positions.

        Args:
            args.confirm: Optional confirmation flag

        Returns:
            0 if successful, 1 if failed or cancelled
        """
        try:
            from tools.operator import get_open_positions, close_all_positions
            from tools.notify import send

            print(f"\n{'=' * 70}")
            print(f"  Emergency Close All Positions")
            print(f"{'=' * 70}\n")

            # Get current positions
            print("📊 Checking open positions...")
            positions = get_open_positions()

            if positions.get('status') == 'error':
                print(f"❌ Error: {positions.get('error')}")
                return 1

            open_positions = positions.get('positions', [])
            total_pnl = positions.get('total_pnl', 0)

            if not open_positions:
                print("✅ No open positions")
                print(f"\n{'=' * 70}")
                return 0

            print(f"\n  Open Positions: {len(open_positions)}")
            print(f"  Total P&L: ${total_pnl:.2f}")
            for pos in open_positions[:5]:  # Show first 5
                print(f"    - {pos.get('symbol')} {pos.get('type')} x{pos.get('volume')} @ ${pos.get('open_price')} (P&L: ${pos.get('profit')})")
            if len(open_positions) > 5:
                print(f"    ... and {len(open_positions) - 5} more")

            # Confirm
            if not args.confirm:
                print(f"\n⚠️  This will close {len(open_positions)} position(s) with total P&L ${total_pnl:.2f}")
                response = input("Continue? (yes/no): ").strip().lower()
                if response != 'yes':
                    print("❌ Cancelled")
                    return 1

            # Close all
            print(f"\n🔴 Closing all positions...")
            close_result = close_all_positions(comment="Emergency close via CLI")

            if close_result.get('status') == 'success':
                closed_count = close_result.get('closed_count', len(open_positions))
                print(f"✅ Closed {closed_count} position(s)")
                send(f"🚨 Emergency closed {closed_count} positions (P&L: ${total_pnl:.2f})", severity="critical")
                print(f"\n{'=' * 70}")
                return 0
            else:
                print(f"❌ Close failed: {close_result.get('error')}")
                send(f"❌ Emergency close failed: {close_result.get('error')}", severity="critical")
                print(f"\n{'=' * 70}")
                return 1

        except Exception as e:
            logger.error(f"Close all failed: {str(e)}", exc_info=True)
            print(f"❌ Error: {str(e)}")
            return 1

    def report(self, args) -> int:
        """
        Generate trading report.

        Args:
            args.period: Report period (1h, 24h, 7d, 30d, default 24h)

        Returns:
            0 if successful, 1 if failed
        """
        try:
            from tools.logs import get_trade_history
            from tools.operator import get_account_summary
            from tools.notify import send_daily_report

            period = getattr(args, 'period', '24h')

            # Convert period to hours
            hours_map = {'1h': 1, '24h': 24, '7d': 168, '30d': 720}
            hours = hours_map.get(period, 24)

            print(f"\n{'=' * 70}")
            print(f"  Trading Report ({period})")
            print(f"{'=' * 70}\n")

            # Get trade history
            print(f"📊 Fetching trade history...")
            trades_result = get_trade_history(hours=hours)

            if trades_result.get('status') != 'success':
                print(f"❌ Error: {trades_result.get('error')}")
                return 1

            trades = trades_result.get('trades', [])

            # Get account summary
            account = get_account_summary()

            # Calculate metrics
            total_profit = sum(t.get('profit', 0) for t in trades)
            winning_trades = [t for t in trades if t.get('profit', 0) > 0]
            losing_trades = [t for t in trades if t.get('profit', 0) < 0]
            win_rate = (len(winning_trades) / len(trades) * 100) if trades else 0

            # Display
            print(f"  Period: Last {hours} hours")
            print(f"\n  Account Summary:")
            print(f"    Balance:         ${account.get('balance', 0):.2f}")
            print(f"    Equity:          ${account.get('equity', 0):.2f}")
            print(f"    Margin Used:     {account.get('margin_percent', 0):.1f}%")
            print(f"    Drawdown:        {account.get('drawdown_percent', 0):.2f}%")

            print(f"\n  Trade Statistics:")
            print(f"    Total Trades:    {len(trades)}")
            print(f"    Wins:            {len(winning_trades)}")
            print(f"    Losses:          {len(losing_trades)}")
            print(f"    Win Rate:        {win_rate:.1f}%")
            print(f"    Total Profit:    ${total_profit:.2f}")

            if trades:
                avg_profit = total_profit / len(trades)
                largest_win = max([t.get('profit', 0) for t in trades])
                largest_loss = min([t.get('profit', 0) for t in trades])
                print(f"    Avg/Trade:       ${avg_profit:.2f}")
                print(f"    Largest Win:     ${largest_win:.2f}")
                print(f"    Largest Loss:    ${largest_loss:.2f}")

            # Send daily report
            send_daily_report(
                total_profit=total_profit,
                trade_count=len(trades),
                wins=len(winning_trades),
                losses=len(losing_trades),
                account=account
            )

            print(f"\n✅ Report sent to enabled channels")
            print(f"\n{'=' * 70}")
            return 0

        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}", exc_info=True)
            print(f"❌ Error: {str(e)}")
            return 1

    def run(self) -> int:
        """Run CLI with arguments."""
        parser = argparse.ArgumentParser(
            description='MT5 Automation CLI - Unified command interface',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python mt5_auto.py status
  python mt5_auto.py compile MyEA --symbol EURUSD
  python mt5_auto.py backtest MyEA XAUUSD H1 2024-01-01 2024-12-31
  python mt5_auto.py close-all --confirm
  python mt5_auto.py report --period 7d
            """
        )

        subparsers = parser.add_subparsers(dest='command', help='Command to execute')

        # Status command
        status_parser = subparsers.add_parser('status', help='Show MT5 status')

        # Compile command
        compile_parser = subparsers.add_parser('compile', help='Compile and deploy EA')
        compile_parser.add_argument('ea', help='EA name to compile')
        compile_parser.add_argument('--symbol', default='EURUSD', help='Chart symbol (default: EURUSD)')
        compile_parser.add_argument('--timeframe', default='30', help='Chart timeframe (default: M30)')

        # Backtest command
        backtest_parser = subparsers.add_parser('backtest', help='Run backtest')
        backtest_parser.add_argument('ea', help='EA name')
        backtest_parser.add_argument('symbol', help='Trading symbol (e.g., EURUSD, XAUUSD)')
        backtest_parser.add_argument('timeframe', help='Timeframe (M1, M5, M15, M30, H1, H4, D1)')
        backtest_parser.add_argument('start_date', help='Start date (YYYY-MM-DD)')
        backtest_parser.add_argument('end_date', help='End date (YYYY-MM-DD)')

        # Close-all command
        close_parser = subparsers.add_parser('close-all', help='Emergency close all positions')
        close_parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompt')

        # Report command
        report_parser = subparsers.add_parser('report', help='Generate trading report')
        report_parser.add_argument('--period', default='24h', choices=['1h', '24h', '7d', '30d'],
                                   help='Report period (default: 24h)')

        # Parse arguments
        args = parser.parse_args()

        # Execute command
        if args.command == 'status':
            return self.status(args)
        elif args.command == 'compile':
            return self.compile(args)
        elif args.command == 'backtest':
            return self.backtest(args)
        elif args.command == 'close-all':
            return self.close_all(args)
        elif args.command == 'report':
            return self.report(args)
        else:
            parser.print_help()
            return 1


def main():
    """Entry point."""
    cli = MT5CLI()
    sys.exit(cli.run())


if __name__ == '__main__':
    main()
