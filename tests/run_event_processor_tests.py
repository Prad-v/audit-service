#!/usr/bin/env python3
"""
Event Processor Test Runner

This script runs all event processor transformation tests and provides
detailed reporting on test results and coverage.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_tests_in_docker(test_type="all", verbose=False, coverage=False):
    """Run event processor tests in Docker environment"""
    
    # Build the docker-compose exec command
    cmd = ["docker-compose", "exec", "-T", "events"]
    
    # Add pytest command
    pytest_cmd = ["python", "-m", "pytest"]
    
    # Add test file
    pytest_cmd.append("/app/tests/unit/test_event_processors.py")
    
    # Add verbosity
    if verbose:
        pytest_cmd.append("-v")
    
    # Add coverage if requested
    if coverage:
        pytest_cmd.extend([
            "--cov=/app/app/api/v1/processors",
            "--cov-report=term-missing",
            "--cov-report=html:/app/coverage/event_processors"
        ])
    
    # Add test discovery
    pytest_cmd.extend([
        "--tb=short",
        "--strict-markers",
        "--disable-warnings"
    ])
    
    # Combine commands
    full_cmd = cmd + pytest_cmd
    
    print(f"Running Event Processor Tests in Docker...")
    print(f"Command: {' '.join(full_cmd)}")
    print("-" * 80)
    
    try:
        # Run the tests
        result = subprocess.run(full_cmd, capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n" + "=" * 80)
            print("✅ ALL EVENT PROCESSOR TESTS PASSED!")
            print("=" * 80)
        else:
            print("\n" + "=" * 80)
            print("❌ SOME EVENT PROCESSOR TESTS FAILED!")
            print("=" * 80)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

def run_specific_test_category_in_docker(category, verbose=False):
    """Run tests for a specific category in Docker"""
    
    # Map categories to test markers
    category_markers = {
        "transformations": "TestTransformationFunctions",
        "transformer": "TestTransformerRules", 
        "enrichment": "TestEnrichmentRules",
        "filter": "TestFilterRules",
        "routing": "TestRoutingRules",
        "utility": "TestUtilityFunctions",
        "integration": "TestIntegrationScenarios"
    }
    
    if category not in category_markers:
        print(f"Unknown test category: {category}")
        print(f"Available categories: {', '.join(category_markers.keys())}")
        return False
    
    marker = category_markers[category]
    cmd = [
        "docker-compose", "exec", "-T", "events",
        "python", "-m", "pytest",
        "/app/tests/unit/test_event_processors.py",
        f"-k {marker}",
        "--tb=short"
    ]
    
    if verbose:
        cmd.append("-v")
    
    print(f"Running {category} tests in Docker...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 80)
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running {category} tests: {e}")
        return False

def run_simple_tests_in_docker(verbose=False):
    """Run simplified event processor tests in Docker"""
    
    cmd = [
        "docker-compose", "exec", "-T", "events",
        "python", "-m", "pytest",
        "/app/tests/unit/test_event_processors_simple.py"
    ]
    
    if verbose:
        cmd.append("-v")
    
    print(f"Running Simple Event Processor Tests in Docker...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 80)
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running simple tests: {e}")
        return False

def list_test_categories():
    """List all available test categories"""
    categories = {
        "transformations": "Individual transformation functions (uppercase, lowercase, etc.)",
        "transformer": "Transformer rule processing and field mapping",
        "enrichment": "Enrichment rule processing and type conversion", 
        "filter": "Filter rule processing and condition evaluation",
        "routing": "Routing rule processing and destination assignment",
        "utility": "Utility functions (nested field access, type conversion)",
        "integration": "Complex integration scenarios and processor chains"
    }
    
    print("Available Event Processor Test Categories:")
    print("=" * 60)
    for category, description in categories.items():
        print(f"{category:15} - {description}")
    print()

def check_docker_services():
    """Check if required Docker services are running"""
    try:
        result = subprocess.run(
            ["docker-compose", "ps", "events"], 
            capture_output=True, 
            text=True
        )
        return "Up" in result.stdout
    except Exception:
        return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run Event Processor Transformation Tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_event_processor_tests.py                    # Run all tests
  python run_event_processor_tests.py --category filter # Run only filter tests
  python run_event_processor_tests.py --verbose         # Run with verbose output
  python run_event_processor_tests.py --coverage        # Run with coverage report
  python run_event_processor_tests.py --simple          # Run simplified tests only
  python run_event_processor_tests.py --list            # List test categories
        """
    )
    
    parser.add_argument(
        "--category", "-c",
        choices=["transformations", "transformer", "enrichment", "filter", "routing", "utility", "integration"],
        help="Run tests for a specific category"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--coverage", "--cov",
        action="store_true", 
        help="Generate coverage report"
    )
    
    parser.add_argument(
        "--simple", "-s",
        action="store_true",
        help="Run only simplified tests (no external imports)"
    )
    
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available test categories"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_test_categories()
        return
    
    # Check if Docker services are running
    if not check_docker_services():
        print("❌ Docker services are not running!")
        print("Please start the services with: docker-compose up -d")
        sys.exit(1)
    
    print("✅ Docker services are running")
    
    if args.simple:
        success = run_simple_tests_in_docker(args.verbose)
    elif args.category:
        success = run_specific_test_category_in_docker(args.category, args.verbose)
    else:
        success = run_tests_in_docker(verbose=args.verbose, coverage=args.coverage)
    
    if success:
        print("\n🎉 Event Processor tests completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Event Processor tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
