#!/usr/bin/env python3
"""
Comprehensive Test Suite Runner for Audit Service

This script provides a unified entry point for running all types of tests:
- Unit tests (backend)
- Integration tests (API, database, services)
- E2E tests (frontend + backend)
- Manual test scripts

Usage:
    python tests/run_test_suite.py [options]

Options:
    --unit              Run unit tests only
    --integration       Run integration tests only
    --e2e              Run end-to-end tests only
    --all              Run all tests (default)
    --continue-on-fail Continue running tests even if some fail
    --verbose          Enable verbose output
    --coverage         Generate coverage reports
    --parallel         Run tests in parallel (where supported)
    --ci               CI mode (non-interactive, exit codes)
"""

import argparse
import os
import sys
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import colorama
from colorama import Fore, Back, Style

# Initialize colorama for cross-platform colored output
colorama.init()

class TestType(Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    MANUAL = "manual"

class TestStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"

@dataclass
class TestResult:
    name: str
    type: TestType
    status: TestStatus
    duration: float
    output: str
    error: Optional[str] = None

@dataclass
class TestSuiteResult:
    type: TestType
    total: int
    passed: int
    failed: int
    skipped: int
    duration: float
    results: List[TestResult]

class TestRunner:
    def __init__(self, continue_on_fail: bool = False, verbose: bool = False, ci_mode: bool = False):
        self.continue_on_fail = continue_on_fail
        self.verbose = verbose
        self.ci_mode = ci_mode
        self.results: Dict[TestType, TestSuiteResult] = {}
        
        # Get project root
        self.project_root = Path(__file__).parent.parent
        self.tests_dir = self.project_root / "tests"
        
        # Test configuration
        self.test_config = {
            TestType.UNIT: {
                "dir": "unit",
                "pattern": "test_*.py",
                "timeout": 300,  # 5 minutes
                "description": "Backend Unit Tests"
            },
            TestType.INTEGRATION: {
                "dir": "integration",
                "pattern": "test_*.py",
                "timeout": 600,  # 10 minutes
                "description": "Integration Tests"
            },
            TestType.E2E: {
                "dir": "e2e",
                "pattern": "test_*.py",
                "timeout": 900,  # 15 minutes
                "description": "End-to-End Tests"
            },
            TestType.MANUAL: {
                "dir": "scripts",
                "pattern": "*.py",
                "timeout": 300,  # 5 minutes
                "description": "Manual Test Scripts"
            }
        }

    def print_header(self, message: str):
        """Print a formatted header."""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{message:^60}")
        print(f"{'='*60}{Style.RESET_ALL}\n")

    def print_section(self, message: str):
        """Print a formatted section header."""
        print(f"\n{Fore.YELLOW}{'─'*50}")
        print(f"{message}")
        print(f"{'─'*50}{Style.RESET_ALL}")

    def print_result(self, result: TestResult):
        """Print a test result with appropriate colors."""
        status_colors = {
            TestStatus.PASSED: Fore.GREEN,
            TestStatus.FAILED: Fore.RED,
            TestStatus.SKIPPED: Fore.YELLOW,
            TestStatus.ERROR: Fore.RED
        }
        
        status_symbols = {
            TestStatus.PASSED: "✅",
            TestStatus.FAILED: "❌",
            TestStatus.SKIPPED: "⏭️",
            TestStatus.ERROR: "💥"
        }
        
        color = status_colors.get(result.status, Fore.WHITE)
        symbol = status_symbols.get(result.status, "❓")
        
        print(f"{color}{symbol} {result.name} ({result.duration:.2f}s)")
        
        if result.error and self.verbose:
            print(f"   {Fore.RED}Error: {result.error}{Style.RESET_ALL}")
        
        if self.verbose and result.output:
            print(f"   {Fore.BLUE}Output: {result.output[:200]}...{Style.RESET_ALL}")

    def run_backend_unit_tests(self) -> TestSuiteResult:
        """Run backend unit tests using pytest."""
        self.print_section("Running Backend Unit Tests")
        
        backend_dir = self.project_root / "backend"
        if not backend_dir.exists():
            return TestSuiteResult(
                type=TestType.UNIT,
                total=0,
                passed=0,
                failed=0,
                skipped=0,
                duration=0.0,
                results=[]
            )
        
        start_time = time.time()
        results = []
        
        try:
            # Run pytest with coverage if requested
            cmd = [
                sys.executable, "-m", "pytest",
                str(backend_dir / "tests"),
                "-v",
                "--tb=short"
            ]
            
            if not self.verbose:
                cmd.append("-q")
            
            result = subprocess.run(
                cmd,
                cwd=backend_dir,
                capture_output=True,
                text=True,
                timeout=self.test_config[TestType.UNIT]["timeout"]
            )
            
            duration = time.time() - start_time
            
            # Parse pytest output
            if result.returncode == 0:
                status = TestStatus.PASSED
                error = None
            else:
                status = TestStatus.FAILED
                error = result.stderr
            
            test_result = TestResult(
                name="Backend Unit Tests",
                type=TestType.UNIT,
                status=status,
                duration=duration,
                output=result.stdout,
                error=error
            )
            results.append(test_result)
            
            # Count results from pytest output
            passed = result.stdout.count("PASSED") if "PASSED" in result.stdout else 0
            failed = result.stdout.count("FAILED") if "FAILED" in result.stdout else 0
            skipped = result.stdout.count("SKIPPED") if "SKIPPED" in result.stdout else 0
            total = passed + failed + skipped
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            test_result = TestResult(
                name="Backend Unit Tests",
                type=TestType.UNIT,
                status=TestStatus.ERROR,
                duration=duration,
                output="",
                error="Test timeout"
            )
            results.append(test_result)
            total = passed = failed = skipped = 0
            
        except Exception as e:
            duration = time.time() - start_time
            test_result = TestResult(
                name="Backend Unit Tests",
                type=TestType.UNIT,
                status=TestStatus.ERROR,
                duration=duration,
                output="",
                error=str(e)
            )
            results.append(test_result)
            total = passed = failed = skipped = 0
        
        return TestSuiteResult(
            type=TestType.UNIT,
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration=duration,
            results=results
        )

    def run_frontend_unit_tests(self) -> TestSuiteResult:
        """Run frontend unit tests using npm."""
        self.print_section("Running Frontend Unit Tests")
        
        frontend_dir = self.project_root / "frontend"
        if not frontend_dir.exists():
            return TestSuiteResult(
                type=TestType.UNIT,
                total=0,
                passed=0,
                failed=0,
                skipped=0,
                duration=0.0,
                results=[]
            )
        
        start_time = time.time()
        results = []
        
        try:
            # Check if npm test script exists
            package_json = frontend_dir / "package.json"
            if not package_json.exists():
                return TestSuiteResult(
                    type=TestType.UNIT,
                    total=0,
                    passed=0,
                    failed=0,
                    skipped=0,
                    duration=0.0,
                    results=[]
                )
            
            # Run npm test
            cmd = ["npm", "test", "--", "--run"]
            
            result = subprocess.run(
                cmd,
                cwd=frontend_dir,
                capture_output=True,
                text=True,
                timeout=self.test_config[TestType.UNIT]["timeout"]
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                status = TestStatus.PASSED
                error = None
            else:
                status = TestStatus.FAILED
                error = result.stderr
            
            test_result = TestResult(
                name="Frontend Unit Tests",
                type=TestType.UNIT,
                status=status,
                duration=duration,
                output=result.stdout,
                error=error
            )
            results.append(test_result)
            
            # Parse test results
            passed = result.stdout.count("✓") if "✓" in result.stdout else 0
            failed = result.stdout.count("✗") if "✗" in result.stdout else 0
            total = passed + failed
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            test_result = TestResult(
                name="Frontend Unit Tests",
                type=TestType.UNIT,
                status=TestStatus.ERROR,
                duration=duration,
                output="",
                error="Test timeout"
            )
            results.append(test_result)
            total = passed = failed = 0
            
        except Exception as e:
            duration = time.time() - start_time
            test_result = TestResult(
                name="Frontend Unit Tests",
                type=TestType.UNIT,
                status=TestStatus.ERROR,
                duration=duration,
                output="",
                error=str(e)
            )
            results.append(test_result)
            total = passed = failed = 0
        
        return TestSuiteResult(
            type=TestType.UNIT,
            total=total,
            passed=passed,
            failed=failed,
            skipped=0,
            duration=duration,
            results=results
        )

    def run_integration_tests(self) -> TestSuiteResult:
        """Run integration tests."""
        self.print_section("Running Integration Tests")
        
        integration_dir = self.tests_dir / "integration"
        if not integration_dir.exists():
            return TestSuiteResult(
                type=TestType.INTEGRATION,
                total=0,
                passed=0,
                failed=0,
                skipped=0,
                duration=0.0,
                results=[]
            )
        
        start_time = time.time()
        results = []
        total = passed = failed = skipped = 0
        
        # Find all test files
        test_files = list(integration_dir.glob("test_*.py"))
        
        for test_file in test_files:
            test_name = test_file.stem
            test_start = time.time()
            
            try:
                result = subprocess.run(
                    [sys.executable, str(test_file)],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=self.test_config[TestType.INTEGRATION]["timeout"]
                )
                
                test_duration = time.time() - test_start
                
                if result.returncode == 0:
                    status = TestStatus.PASSED
                    error = None
                    passed += 1
                else:
                    status = TestStatus.FAILED
                    error = result.stderr
                    failed += 1
                
                test_result = TestResult(
                    name=test_name,
                    type=TestType.INTEGRATION,
                    status=status,
                    duration=test_duration,
                    output=result.stdout,
                    error=error
                )
                results.append(test_result)
                total += 1
                
                self.print_result(test_result)
                
                if not self.continue_on_fail and status == TestStatus.FAILED:
                    break
                    
            except subprocess.TimeoutExpired:
                test_duration = time.time() - test_start
                test_result = TestResult(
                    name=test_name,
                    type=TestType.INTEGRATION,
                    status=TestStatus.ERROR,
                    duration=test_duration,
                    output="",
                    error="Test timeout"
                )
                results.append(test_result)
                total += 1
                failed += 1
                
                self.print_result(test_result)
                
                if not self.continue_on_fail:
                    break
                    
            except Exception as e:
                test_duration = time.time() - test_start
                test_result = TestResult(
                    name=test_name,
                    type=TestType.INTEGRATION,
                    status=TestStatus.ERROR,
                    duration=test_duration,
                    output="",
                    error=str(e)
                )
                results.append(test_result)
                total += 1
                failed += 1
                
                self.print_result(test_result)
                
                if not self.continue_on_fail:
                    break
        
        duration = time.time() - start_time
        
        return TestSuiteResult(
            type=TestType.INTEGRATION,
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration=duration,
            results=results
        )

    def run_e2e_tests(self) -> TestSuiteResult:
        """Run end-to-end tests."""
        self.print_section("Running End-to-End Tests")
        
        e2e_dir = self.tests_dir / "e2e"
        if not e2e_dir.exists():
            return TestSuiteResult(
                type=TestType.E2E,
                total=0,
                passed=0,
                failed=0,
                skipped=0,
                duration=0.0,
                results=[]
            )
        
        start_time = time.time()
        results = []
        total = passed = failed = skipped = 0
        
        # Find all test files
        test_files = list(e2e_dir.glob("test_*.py"))
        
        for test_file in test_files:
            test_name = test_file.stem
            test_start = time.time()
            
            try:
                result = subprocess.run(
                    [sys.executable, str(test_file)],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=self.test_config[TestType.E2E]["timeout"]
                )
                
                test_duration = time.time() - test_start
                
                if result.returncode == 0:
                    status = TestStatus.PASSED
                    error = None
                    passed += 1
                else:
                    status = TestStatus.FAILED
                    error = result.stderr
                    failed += 1
                
                test_result = TestResult(
                    name=test_name,
                    type=TestType.E2E,
                    status=status,
                    duration=test_duration,
                    output=result.stdout,
                    error=error
                )
                results.append(test_result)
                total += 1
                
                self.print_result(test_result)
                
                if not self.continue_on_fail and status == TestStatus.FAILED:
                    break
                    
            except subprocess.TimeoutExpired:
                test_duration = time.time() - test_start
                test_result = TestResult(
                    name=test_name,
                    type=TestType.E2E,
                    status=TestStatus.ERROR,
                    duration=test_duration,
                    output="",
                    error="Test timeout"
                )
                results.append(test_result)
                total += 1
                failed += 1
                
                self.print_result(test_result)
                
                if not self.continue_on_fail:
                    break
                    
            except Exception as e:
                test_duration = time.time() - test_start
                test_result = TestResult(
                    name=test_name,
                    type=TestType.E2E,
                    status=TestStatus.ERROR,
                    duration=test_duration,
                    output="",
                    error=str(e)
                )
                results.append(test_result)
                total += 1
                failed += 1
                
                self.print_result(test_result)
                
                if not self.continue_on_fail:
                    break
        
        duration = time.time() - start_time
        
        return TestSuiteResult(
            type=TestType.E2E,
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration=duration,
            results=results
        )

    def run_manual_scripts(self) -> TestSuiteResult:
        """Run manual test scripts."""
        self.print_section("Running Manual Test Scripts")
        
        scripts_dir = self.tests_dir / "scripts"
        if not scripts_dir.exists():
            return TestSuiteResult(
                type=TestType.MANUAL,
                total=0,
                passed=0,
                failed=0,
                skipped=0,
                duration=0.0,
                results=[]
            )
        
        start_time = time.time()
        results = []
        total = passed = failed = skipped = 0
        
        # Find all script files
        script_files = list(scripts_dir.glob("*.py"))
        
        for script_file in script_files:
            script_name = script_file.stem
            script_start = time.time()
            
            try:
                result = subprocess.run(
                    [sys.executable, str(script_file)],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=self.test_config[TestType.MANUAL]["timeout"]
                )
                
                script_duration = time.time() - script_start
                
                if result.returncode == 0:
                    status = TestStatus.PASSED
                    error = None
                    passed += 1
                else:
                    status = TestStatus.FAILED
                    error = result.stderr
                    failed += 1
                
                test_result = TestResult(
                    name=script_name,
                    type=TestType.MANUAL,
                    status=status,
                    duration=script_duration,
                    output=result.stdout,
                    error=error
                )
                results.append(test_result)
                total += 1
                
                self.print_result(test_result)
                
                if not self.continue_on_fail and status == TestStatus.FAILED:
                    break
                    
            except subprocess.TimeoutExpired:
                script_duration = time.time() - script_start
                test_result = TestResult(
                    name=script_name,
                    type=TestType.MANUAL,
                    status=TestStatus.ERROR,
                    duration=script_duration,
                    output="",
                    error="Script timeout"
                )
                results.append(test_result)
                total += 1
                failed += 1
                
                self.print_result(test_result)
                
                if not self.continue_on_fail:
                    break
                    
            except Exception as e:
                script_duration = time.time() - script_start
                test_result = TestResult(
                    name=script_name,
                    type=TestType.MANUAL,
                    status=TestStatus.ERROR,
                    duration=script_duration,
                    output="",
                    error=str(e)
                )
                results.append(test_result)
                total += 1
                failed += 1
                
                self.print_result(test_result)
                
                if not self.continue_on_fail:
                    break
        
        duration = time.time() - start_time
        
        return TestSuiteResult(
            type=TestType.MANUAL,
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration=duration,
            results=results
        )

    def run_tests(self, test_types: List[TestType]) -> Dict[TestType, TestSuiteResult]:
        """Run the specified test types."""
        results = {}
        
        for test_type in test_types:
            if test_type == TestType.UNIT:
                # Run both backend and frontend unit tests
                backend_result = self.run_backend_unit_tests()
                frontend_result = self.run_frontend_unit_tests()
                
                # Combine results
                combined_result = TestSuiteResult(
                    type=TestType.UNIT,
                    total=backend_result.total + frontend_result.total,
                    passed=backend_result.passed + frontend_result.passed,
                    failed=backend_result.failed + frontend_result.failed,
                    skipped=backend_result.skipped + frontend_result.skipped,
                    duration=backend_result.duration + frontend_result.duration,
                    results=backend_result.results + frontend_result.results
                )
                results[test_type] = combined_result
                
            elif test_type == TestType.INTEGRATION:
                results[test_type] = self.run_integration_tests()
                
            elif test_type == TestType.E2E:
                results[test_type] = self.run_e2e_tests()
                
            elif test_type == TestType.MANUAL:
                results[test_type] = self.run_manual_scripts()
        
        return results

    def print_summary(self, results: Dict[TestType, TestSuiteResult]):
        """Print a summary of all test results."""
        self.print_header("Test Suite Summary")
        
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        total_duration = 0.0
        
        for test_type, result in results.items():
            total_tests += result.total
            total_passed += result.passed
            total_failed += result.failed
            total_skipped += result.skipped
            total_duration += result.duration
            
            # Print individual suite results
            status_color = Fore.GREEN if result.failed == 0 else Fore.RED
            print(f"{status_color}{test_type.value.upper()} Tests:{Style.RESET_ALL}")
            print(f"  Total: {result.total}, Passed: {result.passed}, Failed: {result.failed}, Skipped: {result.skipped}")
            print(f"  Duration: {result.duration:.2f}s")
            print()
        
        # Print overall summary
        print(f"{'─'*50}")
        overall_status = "PASSED" if total_failed == 0 else "FAILED"
        status_color = Fore.GREEN if total_failed == 0 else Fore.RED
        
        print(f"{status_color}Overall Status: {overall_status}{Style.RESET_ALL}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {Fore.GREEN}{total_passed}{Style.RESET_ALL}")
        print(f"Failed: {Fore.RED}{total_failed}{Style.RESET_ALL}")
        print(f"Skipped: {Fore.YELLOW}{total_skipped}{Style.RESET_ALL}")
        print(f"Total Duration: {total_duration:.2f}s")
        
        # Return overall success status
        return total_failed == 0

def main():
    parser = argparse.ArgumentParser(description="Run the complete test suite")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests only")
    parser.add_argument("--manual", action="store_true", help="Run manual scripts only")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")
    parser.add_argument("--continue-on-fail", action="store_true", help="Continue running tests even if some fail")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage reports")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel (where supported)")
    parser.add_argument("--ci", action="store_true", help="CI mode (non-interactive, exit codes)")
    
    args = parser.parse_args()
    
    # Determine which test types to run
    if args.unit:
        test_types = [TestType.UNIT]
    elif args.integration:
        test_types = [TestType.INTEGRATION]
    elif args.e2e:
        test_types = [TestType.E2E]
    elif args.manual:
        test_types = [TestType.MANUAL]
    else:
        # Default to all tests
        test_types = [TestType.UNIT, TestType.INTEGRATION, TestType.E2E, TestType.MANUAL]
    
    # Create test runner
    runner = TestRunner(
        continue_on_fail=args.continue_on_fail,
        verbose=args.verbose,
        ci_mode=args.ci
    )
    
    # Run tests
    try:
        results = runner.run_tests(test_types)
        success = runner.print_summary(results)
        
        # Exit with appropriate code
        if args.ci:
            sys.exit(0 if success else 1)
        else:
            sys.exit(0 if success else 0)  # Don't exit with error in interactive mode
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test suite interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Test suite failed with error: {e}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
