# Test Suite Documentation

This directory contains the comprehensive test suite for the Audit Service project. The test suite is organized into different categories and provides a unified entry point for running all tests.

## 📁 Directory Structure

```
tests/
├── unit/                    # Unit tests (backend & frontend)
├── integration/            # Integration tests (API, database, services)
├── e2e/                   # End-to-end tests (full system)
├── scripts/               # Manual test scripts
├── run_test_suite.py      # Main test runner
├── requirements.txt       # Test dependencies
└── README.md             # This file
```

## 🚀 Quick Start

### Run All Tests
```bash
# From project root
python run_tests.py

# Or directly
python tests/run_test_suite.py
```

### Run Specific Test Types
```bash
# Unit tests only
python run_tests.py --unit

# Integration tests only
python run_tests.py --integration

# E2E tests only
python run_tests.py --e2e

# Manual scripts only
python run_tests.py --manual
```

### Advanced Options
```bash
# Continue running tests even if some fail
python run_tests.py --continue-on-fail

# Enable verbose output
python run_tests.py --verbose

# CI mode (non-interactive, exit codes)
python run_tests.py --ci

# Run with coverage
python run_tests.py --coverage
```

## 📋 Test Categories

### 1. Unit Tests (`unit/`)
- **Backend Unit Tests**: Test individual functions and classes in isolation
- **Frontend Unit Tests**: Test React components and utilities
- **Location**: `backend/tests/` and `frontend/src/__tests__/`

### 2. Integration Tests (`integration/`)
- **API Integration**: Test API endpoints with real database
- **Service Integration**: Test service layer interactions
- **Database Integration**: Test database operations
- **Location**: `tests/integration/`

### 3. End-to-End Tests (`e2e/`)
- **Full System Tests**: Test complete user workflows
- **Frontend-Backend Integration**: Test UI interactions with API
- **Cross-Service Communication**: Test service-to-service communication
- **Location**: `tests/e2e/`

### 4. Manual Scripts (`scripts/`)
- **Manual Test Scripts**: Scripts for manual testing scenarios
- **Debugging Scripts**: Scripts for troubleshooting
- **Performance Scripts**: Scripts for performance testing
- **Location**: `tests/scripts/`

## 🔧 Test Configuration

### Environment Variables
```bash
# Test database
TEST_DATABASE_URL=postgresql://test:test@localhost:5432/audit_test

# Test Redis
TEST_REDIS_URL=redis://localhost:6379/1

# Test NATS
TEST_NATS_URL=nats://localhost:4222

# API base URL
API_BASE_URL=http://localhost:8000

# Frontend URL
FRONTEND_URL=http://localhost:3000
```

### Test Timeouts
- **Unit Tests**: 5 minutes
- **Integration Tests**: 10 minutes
- **E2E Tests**: 15 minutes
- **Manual Scripts**: 5 minutes

## 🏃‍♂️ Running Tests in CI/CD

### GitHub Actions
The test suite is integrated with GitHub Actions. The workflow supports:

- **Automatic testing** on push/PR to main/develop branches
- **Manual triggering** with custom parameters
- **Continue on fail** option for debugging
- **Test result artifacts** for analysis

### Local CI Simulation
```bash
# Run tests in CI mode
python run_tests.py --ci --continue-on-fail

# Run specific test type in CI mode
python run_tests.py --ci --unit --continue-on-fail
```

## 📊 Test Results

### Output Format
The test runner provides:
- **Colored output** for easy reading
- **Progress indicators** for long-running tests
- **Detailed error messages** for failed tests
- **Summary statistics** at the end

### Example Output
```
🚀 Starting Frontend-Backend Integration Tests
============================================================

✅ API Health Check
   API is healthy

✅ Frontend Access
   Frontend is accessible

✅ Create Audit Event
   Event created with ID: abc123-def456

============================================================
📋 E2E Test Summary
============================================================
Total Tests: 8
Passed: 8
Failed: 0

Overall Status: PASSED
```

## 🛠️ Adding New Tests

### Adding Unit Tests
1. Create test file in appropriate directory
2. Follow naming convention: `test_*.py`
3. Use pytest fixtures and assertions
4. Add to test suite configuration

### Adding Integration Tests
1. Create test file in `tests/integration/`
2. Use `test_*.py` naming convention
3. Test real service interactions
4. Include proper setup/teardown

### Adding E2E Tests
1. Create test file in `tests/e2e/`
2. Test complete user workflows
3. Use real browser automation if needed
4. Include service health checks

### Adding Manual Scripts
1. Create script in `tests/scripts/`
2. Make it executable and self-contained
3. Include proper error handling
4. Add documentation

## 🔍 Debugging Tests

### Common Issues
1. **Service not ready**: Wait for health checks
2. **Database connection**: Check connection strings
3. **Port conflicts**: Ensure ports are available
4. **Timeout issues**: Increase timeout values

### Debug Mode
```bash
# Run with verbose output
python run_tests.py --verbose

# Run single test file
python tests/integration/test_specific.py

# Run with debug logging
DEBUG=1 python run_tests.py
```

### Test Isolation
```bash
# Run tests in isolation
python run_tests.py --unit --continue-on-fail

# Skip specific test types
python run_tests.py --integration --e2e
```

## 📈 Coverage Reports

### Generate Coverage
```bash
# Run with coverage
python run_tests.py --coverage

# Generate HTML report
pytest --cov=app --cov-report=html
```

### Coverage Targets
- **Backend**: 80% minimum
- **Frontend**: 70% minimum
- **Critical paths**: 90% minimum

## 🤝 Contributing

### Test Guidelines
1. **Write descriptive test names**
2. **Use meaningful assertions**
3. **Include proper error messages**
4. **Follow the existing patterns**
5. **Add documentation for complex tests**

### Code Review Checklist
- [ ] Tests are comprehensive
- [ ] Error cases are covered
- [ ] Performance is acceptable
- [ ] Documentation is updated
- [ ] CI/CD integration works

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Compose Testing](https://docs.docker.com/compose/compose-file/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)

## 🆘 Support

For issues with the test suite:
1. Check the troubleshooting section
2. Review test logs and error messages
3. Verify environment setup
4. Create an issue with detailed information
