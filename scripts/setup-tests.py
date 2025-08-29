#!/usr/bin/env python3
"""
Test setup and troubleshooting script for the Audit Log Framework.

This script helps set up the testing environment and troubleshoot common issues.
"""

import os
import subprocess
import sys
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ Python 3.11+ is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """Check if all required dependencies are installed."""
    print("\n🔍 Checking dependencies...")
    
    dependencies = {
        "pytest": "python -m pytest --version",
        "pytest-asyncio": "python -c 'import pytest_asyncio; print(pytest_asyncio.__version__)'",
        "pytest-cov": "python -c 'import pytest_cov; print(pytest_cov.__version__)'",
        "httpx": "python -c 'import httpx; print(httpx.__version__)'",
        "sqlalchemy": "python -c 'import sqlalchemy; print(sqlalchemy.__version__)'",
        "alembic": "python -c 'import alembic; print(alembic.__version__)'",
        "fastapi": "python -c 'import fastapi; print(fastapi.__version__)'",
        "uvicorn": "python -c 'import uvicorn; print(uvicorn.__version__)'",
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
            else:
                version = result.stdout.strip()
                print(f"✅ {dep_name}: {version}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            missing_deps.append(dep_name)
    
    if missing_deps:
        print(f"\n❌ Missing dependencies: {', '.join(missing_deps)}")
        print("\nPlease install missing dependencies:")
        print("cd backend")
        print("pip install -r requirements-dev.txt")
        return False
    
    print("\n✅ All dependencies are available")
    return True


def setup_test_environment():
    """Set up the test environment."""
    print("\n🔧 Setting up test environment...")
    
    # Change to backend directory
    backend_dir = Path(__file__).parent.parent / "backend"
    os.chdir(backend_dir)
    
    # Create test database directory if it doesn't exist
    test_db_dir = backend_dir / "tests" / "test_data"
    test_db_dir.mkdir(exist_ok=True)
    
    # Set test environment variables
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    os.environ["REDIS_URL"] = "redis://localhost:6379/1"
    os.environ["NATS_URL"] = "nats://localhost:4222"
    os.environ["SECURITY_SECRET_KEY"] = "test-secret-key-for-testing"
    
    print("✅ Test environment variables set")
    print("✅ Test database directory created")
    
    return True


def run_simple_test():
    """Run a simple test to verify the setup."""
    print("\n🧪 Running simple test...")
    
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "-v", "-k", "test_health", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("✅ Simple test passed!")
            return True
        else:
            print("❌ Simple test failed!")
            print("Error output:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Simple test timed out!")
        return False
    except Exception as e:
        print(f"💥 Simple test failed with exception: {e}")
        return False


def main():
    """Main function."""
    print("🚀 Audit Log Framework Test Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Setup test environment
    if not setup_test_environment():
        sys.exit(1)
    
    # Run simple test
    if not run_simple_test():
        print("\n❌ Test setup failed. Please check the error messages above.")
        sys.exit(1)
    
    print("\n🎉 Test setup completed successfully!")
    print("\nYou can now run tests using:")
    print("  python scripts/run-tests.py --unit")
    print("  python scripts/run-tests.py --all")


if __name__ == "__main__":
    main()
