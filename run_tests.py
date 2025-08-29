#!/usr/bin/env python3
"""
Simple entry point for running the test suite.

This script is a convenience wrapper around the main test runner.
It can be run from the project root directory.

Usage:
    python run_tests.py [options]

For full options, see: python tests/run_test_suite.py --help
"""

import sys
import subprocess
from pathlib import Path

def main():
    # Get the path to the main test runner
    script_dir = Path(__file__).parent
    test_runner = script_dir / "tests" / "run_test_suite.py"
    
    if not test_runner.exists():
        print("Error: Test runner not found at tests/run_test_suite.py")
        sys.exit(1)
    
    # Pass all arguments to the main test runner
    cmd = [sys.executable, str(test_runner)] + sys.argv[1:]
    
    try:
        result = subprocess.run(cmd, check=False)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error running tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
