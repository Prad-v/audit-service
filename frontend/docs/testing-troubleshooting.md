# Testing Troubleshooting Guide

This guide helps you resolve common issues when running tests for the Audit Log Framework.

## Common Issues and Solutions

### 1. Import Errors

**Problem**: `ModuleNotFoundError` or `ImportError` when running tests

**Solution**:
```bash
# Make sure you're in the backend directory
cd backend

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### 2. Database Connection Issues

**Problem**: Database connection errors in tests

**Solution**:
```bash
# Check if test database is accessible
python -c "from app.db.database import get_database_manager; print('DB OK')"

# Reset test database
rm -f test.db test_async.db
```

### 3. Missing Dependencies

**Problem**: Missing packages when running tests

**Solution**:
```bash
# Install all development dependencies
pip install -r requirements-dev.txt

# Or install specific packages
pip install pytest pytest-asyncio pytest-cov httpx
```

### 4. Test Environment Issues

**Problem**: Tests failing due to environment configuration

**Solution**:
```bash
# Run the setup script
python scripts/setup-tests.py

# Or set environment variables manually
export ENVIRONMENT=test
export DATABASE_URL=sqlite:///./test.db
export SECURITY_SECRET_KEY=test-secret-key
```

### 5. Async Test Issues

**Problem**: Async tests not running properly

**Solution**:
```bash
# Make sure pytest-asyncio is installed
pip install pytest-asyncio

# Run with explicit asyncio mode
pytest --asyncio-mode=auto tests/
```

### 6. Coverage Issues

**Problem**: Coverage reports not generating

**Solution**:
```bash
# Install coverage tools
pip install coverage pytest-cov

# Run with coverage
pytest --cov=app --cov-report=html tests/
```

## Running Tests

### Basic Test Commands

```bash
# Run all tests
python scripts/run-tests.py --all

# Run only unit tests
python scripts/run-tests.py --unit

# Run with coverage
python scripts/run-tests.py --unit --coverage

# Run specific test file
cd backend
pytest tests/test_auth_service.py -v

# Run specific test function
pytest tests/test_auth_service.py::TestAuthService::test_create_user_success -v
```

### Debugging Tests

```bash
# Run with verbose output
python scripts/run-tests.py --unit --verbose

# Run with debug logging
pytest --log-cli-level=DEBUG tests/

# Run with print statements visible
pytest -s tests/

# Run with full traceback
pytest --tb=long tests/
```

### Performance Testing

```bash
# Run load tests
python scripts/run-tests.py --load --users 50 --duration 60s

# Run with custom host
python scripts/run-tests.py --load --host api.example.com:443
```

## Test Structure

### Test Files
- `tests/test_auth_service.py` - Authentication service tests
- `tests/test_audit_service.py` - Audit log service tests
- `tests/test_api_integration.py` - API integration tests
- `tests/load/locustfile.py` - Load testing scenarios
- `tests/security/security_tests.py` - Security tests

### Test Fixtures
- `tests/conftest.py` - Shared test fixtures and configuration
- Database fixtures for both sync and async testing
- Mock services for external dependencies

### Test Categories
- **Unit tests** (`@pytest.mark.unit`) - Test individual functions
- **Integration tests** (`@pytest.mark.integration`) - Test component interactions
- **API tests** (`@pytest.mark.api`) - Test HTTP endpoints
- **Security tests** (`@pytest.mark.security`) - Test security features

## Continuous Integration

The tests are configured to run in CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: Run tests
  run: |
    cd backend
    python -m pytest tests/ --cov=app --cov-report=xml
```

## Getting Help

If you're still experiencing issues:

1. Check the test output for specific error messages
2. Verify your Python version (3.11+ required)
3. Ensure all dependencies are installed
4. Check that you're running from the correct directory
5. Review the test logs for detailed error information

For additional help, check the project documentation or create an issue with:
- Python version
- Operating system
- Full error message
- Steps to reproduce
