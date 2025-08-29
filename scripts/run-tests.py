#!/usr/bin/env python3
"""
Comprehensive test runner for the Audit Log Framework.

This script provides a unified interface for running all types of tests:
- Unit tests with pytest
- Integration tests
- Load tests with Locust
- Security tests
- Performance tests

Usage:
    python scripts/run-tests.py --all
    python scripts/run-tests.py --unit --coverage
    python scripts/run-tests.py --load --users 50 --duration 60s
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
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
        
        # Change to backend directory for running tests
        original_cwd = os.getcwd()
        os.chdir(self.backend_dir)
        
        try:
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
        finally:
            # Restore original working directory
            os.chdir(original_cwd)
    
    def run_integration_tests(self, verbose: bool = False) -> bool:
        """Run integration tests."""
        print("\n🔗 Running Integration Tests...")
        print("-" * 50)
        
        # Change to backend directory for running tests
        original_cwd = os.getcwd()
        os.chdir(self.backend_dir)
        
        try:
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
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minutes timeout for integration tests
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
                    "error": "Test execution timed out",
                    "command": " ".join(cmd)
                }
                return False
            except Exception as e:
                print(f"💥 Integration tests failed with exception: {e}")
                self.results["test_results"]["integration_tests"] = {
                    "passed": False,
                    "duration": time.time() - start_time,
                    "error": str(e),
                    "command": " ".join(cmd)
                }
                return False
        finally:
            # Restore original working directory
            os.chdir(original_cwd)
    
    def run_load_tests(self, host: str = "localhost:8000", users: int = 10, 
                      duration: str = "30s", verbose: bool = False) -> bool:
        """Run load tests with Locust."""
        print(f"\n⚡ Running Load Tests...")
        print("-" * 50)
        print(f"Host: {host}")
        print(f"Users: {users}")
        print(f"Duration: {duration}")
        
        # Change to tests directory for running load tests
        original_cwd = os.getcwd()
        os.chdir(self.tests_dir / "load")
        
        try:
            cmd = [
                "locust",
                "-f", "locustfile.py",
                "--host", f"http://{host}",
                "--users", str(users),
                "--spawn-rate", "2",
                "--run-time", duration,
                "--headless",
                "--html", "load_test_report.html",
                "--csv", "load_test_results"
            ]
            
            if verbose:
                cmd.append("--loglevel=DEBUG")
            
            start_time = time.time()
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=1800  # 30 minutes timeout for load tests
                )
                
                duration_actual = time.time() - start_time
                
                self.results["test_results"]["load_tests"] = {
                    "passed": result.returncode == 0,
                    "duration": duration_actual,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "command": " ".join(cmd)
                }
                
                if result.returncode == 0:
                    print("✅ Load tests completed!")
                else:
                    print("❌ Load tests failed!")
                    print(f"Error output: {result.stderr}")
                
                return result.returncode == 0
                
            except subprocess.TimeoutExpired:
                print("⏰ Load tests timed out!")
                self.results["test_results"]["load_tests"] = {
                    "passed": False,
                    "duration": 1800,
                    "error": "Test execution timed out",
                    "command": " ".join(cmd)
                }
                return False
            except Exception as e:
                print(f"💥 Load tests failed with exception: {e}")
                self.results["test_results"]["load_tests"] = {
                    "passed": False,
                    "duration": time.time() - start_time,
                    "error": str(e),
                    "command": " ".join(cmd)
                }
                return False
        finally:
            # Restore original working directory
            os.chdir(original_cwd)
    
    def run_security_tests(self, host: str = "localhost:8000", verbose: bool = False) -> bool:
        """Run security tests."""
        print(f"\n🔒 Running Security Tests...")
        print("-" * 50)
        print(f"Target: {host}")
        
        # Change to tests directory for running security tests
        original_cwd = os.getcwd()
        os.chdir(self.tests_dir / "security")
        
        try:
            cmd = ["python", "security_tests.py", "--host", host]
            
            if verbose:
                cmd.append("--verbose")
            
            start_time = time.time()
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minutes timeout for security tests
                )
                
                duration = time.time() - start_time
                
                self.results["test_results"]["security_tests"] = {
                    "passed": result.returncode == 0,
                    "duration": duration,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "command": " ".join(cmd)
                }
                
                if result.returncode == 0:
                    print("✅ Security tests passed!")
                else:
                    print("❌ Security tests failed!")
                    print(f"Error output: {result.stderr}")
                
                return result.returncode == 0
                
            except subprocess.TimeoutExpired:
                print("⏰ Security tests timed out!")
                self.results["test_results"]["security_tests"] = {
                    "passed": False,
                    "duration": 600,
                    "error": "Test execution timed out",
                    "command": " ".join(cmd)
                }
                return False
            except Exception as e:
                print(f"💥 Security tests failed with exception: {e}")
                self.results["test_results"]["security_tests"] = {
                    "passed": False,
                    "duration": time.time() - start_time,
                    "error": str(e),
                    "command": " ".join(cmd)
                }
                return False
        finally:
            # Restore original working directory
            os.chdir(original_cwd)
    
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