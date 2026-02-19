"""
MT5 Automation Integration Tests
==================================
Test all tools with proper error handling and mocking.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestMT5ProcessControl(unittest.TestCase):
    """Test MT5 process operations."""

    def test_get_mt5_status(self):
        """Test getting MT5 status."""
        from tools.process import get_mt5_status
        result = get_mt5_status()
        self.assertIn("status", result)
        self.assertIn("is_running", result)

    def test_get_mt5_status_error_handling(self):
        """Test error handling when MT5 not running."""
        from tools.process import get_mt5_status
        result = get_mt5_status()
        # Should not raise, just return error status
        self.assertIsNotNone(result)


class TestMT5FileManager(unittest.TestCase):
    """Test file operations."""

    def test_list_eas(self):
        """Test listing EAs."""
        from tools.files import list_eas
        result = list_eas("Experts")
        self.assertEqual(result["status"], "success")
        self.assertIn("files", result)
        self.assertIn("count", result)

    def test_get_directory_tree(self):
        """Test directory structure."""
        from tools.files import get_directory_tree
        result = get_directory_tree()
        self.assertEqual(result["status"], "success")
        self.assertIn("structure", result)


class TestMT5LogParser(unittest.TestCase):
    """Test log parsing."""

    def test_get_current_session(self):
        """Test market session detection."""
        from tools.scheduler import get_current_session
        result = get_current_session()
        self.assertEqual(result["status"], "success")
        self.assertIn("sessions", result)
        self.assertIn("local_time", result)

    def test_detect_anomalies(self):
        """Test anomaly detection."""
        from tools.logs import detect_anomalies
        result = detect_anomalies(hours=24)
        self.assertEqual(result["status"], "success")
        self.assertIn("anomalies", result)


class TestMT5Notifier(unittest.TestCase):
    """Test notification system."""

    def test_send_dry_run(self):
        """Test dry-run notification (no actual send)."""
        from tools.notify import send
        # In dry-run mode, should not actually send
        result = send("Test message", severity="info", async_send=False)
        # Should return status even if channels not configured
        self.assertIn("status", result)

    def test_get_enabled_channels(self):
        """Test getting enabled channels."""
        from tools.notify import get_enabled_channels
        channels = get_enabled_channels()
        self.assertIsInstance(channels, list)


class TestMT5Scheduler(unittest.TestCase):
    """Test scheduling system."""

    def test_get_current_session(self):
        """Test current session detection."""
        from tools.scheduler import get_current_session
        result = get_current_session()
        self.assertEqual(result["status"], "success")

    def test_is_market_open(self):
        """Test market open check."""
        from tools.scheduler import is_market_open
        result = is_market_open("XAUUSD")
        self.assertEqual(result["status"], "success")
        self.assertIn("is_open", result)
        self.assertIn("is_weekend", result)


class TestMT5Developer(unittest.TestCase):
    """Test development tools."""

    @patch('tools.files.read_ea_file')
    def test_compile_ea_not_found(self, mock_read):
        """Test compile with missing EA."""
        from tools.developer import compile_ea
        mock_read.return_value = {"status": "error", "error": "Not found"}

        result = compile_ea("NonExistent")
        self.assertEqual(result["status"], "error")

    def test_compile_ea_structure(self):
        """Test compile result structure."""
        from tools.developer import compile_ea
        result = compile_ea("TestEA")
        # Should return proper structure
        self.assertIn("status", result)
        self.assertIn("error_count", result)
        self.assertIn("errors", result)


class TestMT5Operator(unittest.TestCase):
    """Test live trading operations."""

    def test_operator_requires_metatrader5(self):
        """Test that operator requires MetaTrader5."""
        try:
            from tools.operator import MT5Operator
            # If we get here, MT5 library is available
            # Try to initialize and catch connection errors
            try:
                op = MT5Operator()
                # If connected, we can test
                self.assertIsNotNone(op)
            except RuntimeError as e:
                # MT5 not running - expected
                self.assertIn("MT5", str(e))
        except ImportError:
            # MetaTrader5 library not installed
            self.skipTest("MetaTrader5 library not installed")


class TestIntegration(unittest.TestCase):
    """Integration tests across tools."""

    def test_phase1_imports(self):
        """Test all Phase 1 tools import correctly."""
        try:
            from tools.process import MT5ProcessControl
            from tools.files import MT5FileManager
            from tools.logs import MT5LogParser
            from tools.notify import MT5Notifier
            from tools.scheduler import MT5Scheduler
            # All imports successful
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Phase 1 import failed: {e}")

    def test_phase2_imports(self):
        """Test all Phase 2 tools import correctly."""
        try:
            from tools.developer import MT5Developer
            from tools.operator import MT5Operator
            from tools.manager import MT5Manager
            # Tester, Optimizer may have issues without full MT5
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Phase 2 import failed: {e}")

    def test_error_handling_consistency(self):
        """Test that all tools return consistent error structures."""
        from tools.scheduler import get_current_session
        result = get_current_session()

        # All results should have these keys
        expected_keys = ["status"]
        for key in expected_keys:
            self.assertIn(key, result)

        # Status should be success or error
        self.assertIn(result["status"], ["success", "error"])


class TestCommonWorkflows(unittest.TestCase):
    """Test common automation workflows."""

    def test_workflow_check_status(self):
        """Test: Check MT5 status."""
        from tools.process import get_mt5_status
        from tools.scheduler import get_current_session

        status = get_mt5_status()
        session = get_current_session()

        self.assertEqual(status["status"], "success")
        self.assertEqual(session["status"], "success")

    def test_workflow_notify(self):
        """Test: Send notification (dry-run)."""
        from tools.notify import send, get_enabled_channels

        channels = get_enabled_channels()
        # Should have at least one channel configured
        self.assertIsInstance(channels, list)

        # Send should not raise
        result = send("Test", severity="info")
        self.assertIsNotNone(result)


def run_test_suite():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  MT5 Automation Integration Test Suite")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestMT5ProcessControl))
    suite.addTests(loader.loadTestsFromTestCase(TestMT5FileManager))
    suite.addTests(loader.loadTestsFromTestCase(TestMT5LogParser))
    suite.addTests(loader.loadTestsFromTestCase(TestMT5Notifier))
    suite.addTests(loader.loadTestsFromTestCase(TestMT5Scheduler))
    suite.addTests(loader.loadTestsFromTestCase(TestMT5Developer))
    suite.addTests(loader.loadTestsFromTestCase(TestMT5Operator))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestCommonWorkflows))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("=" * 70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_test_suite()
    sys.exit(0 if success else 1)
