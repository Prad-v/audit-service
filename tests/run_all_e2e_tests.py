#!/usr/bin/env python3
"""
Run All E2E Tests

This script runs all E2E tests individually and reports their status.
"""

import subprocess
import sys
import time
from pathlib import Path
from colorama import Fore, Style, init

# Initialize colorama
init()

def run_test(test_file: Path) -> tuple[bool, str, float]:
    """Run a single test file and return (success, output, duration)"""
    print(f"\n{Fore.CYAN}Running {test_file.name}...{Style.RESET_ALL}")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            [sys.executable, str(test_file)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        duration = time.time() - start_time
        
        if result.returncode == 0:
            status = f"{Fore.GREEN}✅ PASS{Style.RESET_ALL}"
            success = True
        else:
            status = f"{Fore.RED}❌ FAIL{Style.RESET_ALL}"
            success = False
        
        output = result.stdout + result.stderr
        print(f"{status} {test_file.name} ({duration:.2f}s)")
        
        if not success and output:
            print(f"{Fore.YELLOW}Error output:{Style.RESET_ALL}")
            print(output[:500] + "..." if len(output) > 500 else output)
        
        return success, output, duration
        
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        print(f"{Fore.RED}⏰ TIMEOUT{Style.RESET_ALL} {test_file.name} ({duration:.2f}s)")
        return False, "Test timeout", duration
    except Exception as e:
        duration = time.time() - start_time
        print(f"{Fore.RED}💥 ERROR{Style.RESET_ALL} {test_file.name} ({duration:.2f}s)")
        return False, str(e), duration


def main():
    """Main function"""
    print(f"{Fore.CYAN}🧪 Running All E2E Tests{Style.RESET_ALL}")
    print("=" * 60)
    
    # Find all E2E test files
    e2e_dir = Path("tests/e2e")
    test_files = list(e2e_dir.glob("test_*.py"))
    
    if not test_files:
        print(f"{Fore.RED}No E2E test files found in {e2e_dir}{Style.RESET_ALL}")
        return False
    
    print(f"Found {len(test_files)} E2E test files:")
    for test_file in test_files:
        print(f"  - {test_file.name}")
    
    # Run all tests
    results = []
    total_passed = 0
    total_failed = 0
    total_duration = 0
    
    for test_file in test_files:
        success, output, duration = run_test(test_file)
        results.append((test_file.name, success, duration))
        
        if success:
            total_passed += 1
        else:
            total_failed += 1
        
        total_duration += duration
    
    # Print summary
    print(f"\n{Fore.CYAN}📊 E2E Test Summary{Style.RESET_ALL}")
    print("=" * 60)
    
    for name, success, duration in results:
        status = f"{Fore.GREEN}✅ PASS{Style.RESET_ALL}" if success else f"{Fore.RED}❌ FAIL{Style.RESET_ALL}"
        print(f"{status} {name} ({duration:.2f}s)")
    
    print(f"\n{Fore.CYAN}Overall Results:{Style.RESET_ALL}")
    print(f"  Total Tests: {len(results)}")
    print(f"  Passed: {Fore.GREEN}{total_passed}{Style.RESET_ALL}")
    print(f"  Failed: {Fore.RED}{total_failed}{Style.RESET_ALL}")
    print(f"  Total Duration: {total_duration:.2f}s")
    
    if total_failed == 0:
        print(f"\n{Fore.GREEN}🎉 All E2E tests passed!{Style.RESET_ALL}")
        return True
    else:
        print(f"\n{Fore.RED}⚠️  {total_failed} E2E test(s) failed{Style.RESET_ALL}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
