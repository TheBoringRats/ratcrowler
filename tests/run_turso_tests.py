#!/usr/bin/env python3
"""
Run Turso Integration Tests
Quick test runner for Turso database integration
"""

import sys
import os
import subprocess
from pathlib import Path

def run_turso_tests():
    """Run Turso-related tests"""
    print("🚀 Turso Integration Test Runner")
    print("=" * 50)

    # Get the tests directory
    tests_dir = Path(__file__).parent / "tests"

    # Turso-related test files
    turso_tests = [
        "test_turso_integration.py",
        "test_turso_monitoring.py"
    ]

    passed = 0
    total = len(turso_tests)

    for test_file in turso_tests:
        test_path = tests_dir / test_file

        if not test_path.exists():
            print(f"❌ {test_file} not found")
            continue

        print(f"\n🧪 Running {test_file}...")
        print("-" * 40)

        try:
            result = subprocess.run(
                [sys.executable, str(test_path)],
                cwd=Path(__file__).parent,  # Run from project root
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                print(f"✅ {test_file} passed")
                passed += 1
            else:
                print(f"❌ {test_file} failed")
                if result.stderr:
                    print("Error:", result.stderr[-500:])  # Last 500 chars

        except subprocess.TimeoutExpired:
            print(f"⏰ {test_file} timed out")
        except Exception as e:
            print(f"💥 {test_file} error: {e}")

    print(f"\n📊 Turso Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All Turso tests passed!")
        print("\n📝 Your Turso integration is ready!")
        print("   Run: python turso_monitoring_dashboard.py")
        print("   Then visit: http://localhost:8000")
        return True
    else:
        print(f"⚠️  {total - passed} Turso tests failed")
        return False

if __name__ == "__main__":
    success = run_turso_tests()
    sys.exit(0 if success else 1)
