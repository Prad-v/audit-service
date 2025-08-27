#!/usr/bin/env python3
"""
Comprehensive test runner for the Audit Log Framework.

This script runs all types of tests including unit tests, integration tests,
load tests, and security tests with proper reporting and CI/CD integration.
"""

import argparse
import os
import sys
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class TestRunner:
    """Main test runner class."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_dir = project_root / "backend"
        self.tests_dir = project_root / "tests"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(project_root),
            "test_results": {},
            "summary": {
                "total_suites": 0,
                "passed_suites": 0,
                "failed_suites": 0,
                "total_duration": 0
            }
        }
    
    def run_unit_tests(self, coverage: bool = True, verbose: bool = False) -> bool:
        """Run unit tests with pytest."""
        print("🧪 Running Unit Tests...")
        print("-" * 50)
        
        cmd = ["python", "-m", "pytest"]
        
        if coverage:
            cmd.extend([
                "--cov=app",
                "--cov-report=html:htmlcov",
                "--cov-report=term-missing",
                "--cov-report=xml",
                "--cov-fail-under=80"
            ])
        
        if verbose:
            cmd.append("-v")
        
        cmd.extend([
            "--tb=short",
            "--color=yes",
            "--durations=10",
            "-m", "unit or not integration and not slow",
            "tests/"
        ])
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.backend_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            duration = time.time() - start_time
            
            self.results["test_results"]["unit_tests"] = {
                "passed": result.returncode == 0,
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd)
            }
            
            if result.returncode == 0:
                print("✅ Unit tests passed!")
            else:
                print("❌ Unit tests failed!")
                print(f"Error output: {result.stderr}")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("⏰ Unit tests timed out!")
            self.results["test_results"]["unit_tests"] = {
                "passed": False,
                "duration": 300,
                "error": "Test execution timed out",
                "command": " ".join(cmd)
            }
            return False
        except Exception as e:
            print(f"💥 Unit tests failed with exception: {e}")
            self.results["test_results"]["unit_tests"] = {
                "passed": False,
                "duration": time.time() - start_time,
                "error": str(e),
                "command": " ".join(cmd)
            }
            return False
    
    def run_integration_tests(self, verbose: bool = False) -> bool:
        """Run integration tests."""
        print("\n🔗 Running Integration Tests...")
        print("-" * 50)
        
        cmd = ["python", "-m", "pytest"]
        
        if verbose:
            cmd.append("-v")
        
        cmd.extend([
            "--tb=short",
            "--color=yes",
            "-m", "integration",
            "tests/test_api_integration.py"
        ])
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.backend_dir,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            duration = time.time() - start_time
            
            self.results["test_results"]["integration_tests"] = {
                "passed": result.returncode == 0,
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd)
            }
            
            if result.returncode == 0:
                print("✅ Integration tests passed!")
            else:
                print("❌ Integration tests failed!")
                print(f"Error output: {result.stderr}")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("⏰ Integration tests timed out!")
            self.results["test_results"]["integration_tests"] = {
                "passed": False,
                "duration": 600,
                "error": "Test execution timed out"
            }
            return False
        except Exception as e:
            print(f"💥 Integration tests failed with exception: {e}")
            self.results["test_results"]["integration_tests"] = {
                "passed": False,
                "duration": time.time() - start_time,
                "error": str(e)
            }
            return False
    
    def run_load_tests(self, host: str = "localhost:8000", users: int = 10, 
                      duration: str = "30s", verbose: bool = False) -> bool:
        """Run load tests with Locust."""
        print(f"\n⚡ Running Load Tests (Users: {users}, Duration: {duration})...")
        print("-" * 50)
        
        locust_file = self.tests_dir / "load" / "locustfile.py"
        
        if not locust_file.exists():
            print("❌ Locust file not found!")
            self.results["test_results"]["load_tests"] = {
                "passed": False,
                "error": "Locust file not found"
            }
            return False
        
        cmd = [
            "locust",
            "-f", str(locust_file),
            "--host", f"http://{host}",
            "--users", str(users),
            "--spawn-rate", str(min(users, 10)),
            "--run-time", duration,
            "--headless",
            "--html", str(self.project_root / "load_test_report.html"),
            "--csv", str(self.project_root / "load_test_results")
        ]
        
        if verbose:
            cmd.append("--loglevel=DEBUG")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=int(duration.rstrip('s')) + 60  # Duration + 1 minute buffer
            )
            
            duration_actual = time.time() - start_time
            
            # Parse Locust results if available
            stats_file = self.project_root / "load_test_results_stats.csv"
            load_test_stats = {}
            
            if stats_file.exists():
                try:
                    import csv
                    with open(stats_file, 'r') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            if row['Name'] == 'Aggregated':
                                load_test_stats = {
                                    "total_requests": int(row['Request Count']),
                                    "failure_count": int(row['Failure Count']),
                                    "avg_response_time": float(row['Average Response Time']),
                                    "max_response_time": float(row['Max Response Time']),
                                    "requests_per_second": float(row['Requests/s'])
                                }
                                break
                except Exception as e:
                    print(f"Warning: Could not parse load test stats: {e}")
            
            self.results["test_results"]["load_tests"] = {
                "passed": result.returncode == 0,
                "duration": duration_actual,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd),
                "stats": load_test_stats
            }
            
            if result.returncode == 0:
                print("✅ Load tests completed successfully!")
                if load_test_stats:
                    print(f"📊 Total requests: {load_test_stats.get('total_requests', 'N/A')}")
                    print(f"📊 Failure rate: {load_test_stats.get('failure_count', 0)} failures")
                    print(f"📊 Avg response time: {load_test_stats.get('avg_response_time', 'N/A')}ms")
                    print(f"📊 Requests/sec: {load_test_stats.get('requests_per_second', 'N/A')}")
            else:
                print("❌ Load tests failed!")
                print(f"Error output: {result.stderr}")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("⏰ Load tests timed out!")
            self.results["test_results"]["load_tests"] = {
                "passed": False,
                "error": "Load test execution timed out"
            }
            return False
        except Exception as e:
            print(f"💥 Load tests failed with exception: {e}")
            self.results["test_results"]["load_tests"] = {
                "passed": False,
                "duration": time.time() - start_time,
                "error": str(e)
            }
            return False
    
    def run_security_tests(self, host: str = "localhost:8000", verbose: bool = False) -> bool:
        """Run security tests."""
        print(f"\n🔒 Running Security Tests against {host}...")
        print("-" * 50)
        
        security_script = self.tests_dir / "security" / "security_tests.py"
        
        if not security_script.exists():
            print("❌ Security test script not found!")
            self.results["test_results"]["security_tests"] = {
                "passed": False,
                "error": "Security test script not found"
            }
            return False
        
        cmd = [
            "python", str(security_script),
            "--url", f"http://{host}",
            "--output", str(self.project_root / "security_report.json")
        ]
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            duration = time.time() - start_time
            
            # Try to load security report
            security_report = {}
            report_file = self.project_root / "security_report.json"
            if report_file.exists():
                try:
                    with open(report_file, 'r') as f:
                        security_report = json.load(f)
                except Exception as e:
                    print(f"Warning: Could not parse security report: {e}")
            
            self.results["test_results"]["security_tests"] = {
                "passed": result.returncode == 0,
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd),
                "report": security_report
            }
            
            if result.returncode == 0:
                print("✅ Security tests passed!")
                if security_report and "summary" in security_report:
                    summary = security_report["summary"]
                    print(f"🔍 Total tests: {summary.get('total_tests', 'N/A')}")
                    print(f"🔍 Passed: {summary.get('passed_tests', 'N/A')}")
                    print(f"🔍 Failed: {summary.get('failed_tests', 'N/A')}")
            else:
                print("❌ Security tests failed!")
                print(f"Error output: {result.stderr}")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("⏰ Security tests timed out!")
            self.results["test_results"]["security_tests"] = {
                "passed": False,
                "error": "Security test execution timed out"
            }
            return False
        except Exception as e:
            print(f"💥 Security tests failed with exception: {e}")
            self.results["test_results"]["security_tests"] = {
                "passed": False,
                "duration": time.time() - start_time,
                "error": str(e)
            }
            return False
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed."""
        print("🔍 Checking dependencies...")
        
        dependencies = {
            "pytest": "python -m pytest --version",
            "locust": "locust --version",
            "coverage": "python -m coverage --version"
        }
        
        missing_deps = []
        
        for dep_name, check_cmd in dependencies.items():
            try:
                result = subprocess.run(
                    check_cmd.split(),
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode != 0:
                    missing_deps.append(dep_name)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                missing_deps.append(dep_name)
        
        if missing_deps:
            print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
            print("Please install missing dependencies:")
            for dep in missing_deps:
                if dep == "pytest":
                    print("  pip install pytest pytest-asyncio pytest-cov")
                elif dep == "locust":
                    print("  pip install locust")
                elif dep == "coverage":
                    print("  pip install coverage")
            return False
        
        print("✅ All dependencies are available")
        return True
    
    def generate_report(self, output_file: str = "test_report.json") -> None:
        """Generate comprehensive test report."""
        # Calculate summary
        total_suites = len(self.results["test_results"])
        passed_suites = sum(1 for result in self.results["test_results"].values() 
                           if result.get("passed", False))
        failed_suites = total_suites - passed_suites
        total_duration = sum(result.get("duration", 0) 
                           for result in self.results["test_results"].values())
        
        self.results["summary"].update({
            "total_suites": total_suites,
            "passed_suites": passed_suites,
            "failed_suites": failed_suites,
            "total_duration": total_duration
        })
        
        # Save detailed report
        report_path = self.project_root / output_file
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📊 Test Report Generated: {report_path}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("TEST EXECUTION SUMMARY")
        print("=" * 60)
        print(f"Total test suites: {total_suites}")
        print(f"Passed: {passed_suites}")
        print(f"Failed: {failed_suites}")
        print(f"Total duration: {total_duration:.2f}s")
        
        if failed_suites > 0:
            print("\n❌ SOME TESTS FAILED")
            for suite_name, result in self.results["test_results"].items():
                if not result.get("passed", False):
                    print(f"  - {suite_name}: {result.get('error', 'Failed')}")
        else:
            print("\n✅ ALL TESTS PASSED")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Comprehensive test runner for Audit Log Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python scripts/run-tests.py --all
  
  # Run only unit tests with coverage
  python scripts/run-tests.py --unit --coverage
  
  # Run load tests with custom parameters
  python scripts/run-tests.py --load --users 50 --duration 60s
  
  # Run security tests against specific host
  python scripts/run-tests.py --security --host api.example.com:443
  
  # Run tests for CI/CD (no interactive output)
  python scripts/run-tests.py --all --ci
        """
    )
    
    # Test selection
    parser.add_argument("--all", action="store_true", 
                       help="Run all test suites")
    parser.add_argument("--unit", action="store_true",
                       help="Run unit tests")
    parser.add_argument("--integration", action="store_true",
                       help="Run integration tests")
    parser.add_argument("--load", action="store_true",
                       help="Run load tests")
    parser.add_argument("--security", action="store_true",
                       help="Run security tests")
    
    # Test configuration
    parser.add_argument("--coverage", action="store_true",
                       help="Generate coverage report for unit tests")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    parser.add_argument("--host", default="localhost:8000",
                       help="Host for load and security tests")
    
    # Load test specific
    parser.add_argument("--users", type=int, default=10,
                       help="Number of concurrent users for load tests")
    parser.add_argument("--duration", default="30s",
                       help="Duration for load tests (e.g., 30s, 2m)")
    
    # Output options
    parser.add_argument("--output", default="test_report.json",
                       help="Output file for test report")
    parser.add_argument("--ci", action="store_true",
                       help="CI/CD mode (non-interactive)")
    
    args = parser.parse_args()
    
    # Determine project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Initialize test runner
    runner = TestRunner(project_root)
    
    # Check dependencies
    if not runner.check_dependencies():
        sys.exit(1)
    
    # Determine which tests to run
    run_unit = args.all or args.unit
    run_integration = args.all or args.integration
    run_load = args.all or args.load
    run_security = args.all or args.security
    
    if not any([run_unit, run_integration, run_load, run_security]):
        print("❌ No tests selected. Use --all or specify individual test types.")
        sys.exit(1)
    
    print("🚀 Starting Audit Log Framework Test Suite")
    print(f"📁 Project root: {project_root}")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Run selected tests
    all_passed = True
    
    if run_unit:
        passed = runner.run_unit_tests(coverage=args.coverage, verbose=args.verbose)
        all_passed = all_passed and passed
    
    if run_integration:
        passed = runner.run_integration_tests(verbose=args.verbose)
        all_passed = all_passed and passed
    
    if run_load:
        passed = runner.run_load_tests(
            host=args.host,
            users=args.users,
            duration=args.duration,
            verbose=args.verbose
        )
        all_passed = all_passed and passed
    
    if run_security:
        passed = runner.run_security_tests(host=args.host, verbose=args.verbose)
        all_passed = all_passed and passed
    
    # Generate report
    runner.generate_report(args.output)
    
    # Exit with appropriate code
    if all_passed:
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()