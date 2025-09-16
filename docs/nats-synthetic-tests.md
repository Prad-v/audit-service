# NATS Synthetic Tests

## Overview

This document describes the NATS synthetic tests available in the StackStorm Synthetic Test Framework. These tests validate NATS messaging functionality by posting messages and validating received fields.

## Available Tests

### 1. NATS Positive Test - Message Validation

**Purpose**: Tests NATS message publishing and receiving with field validation.

**What it tests**:
- NATS connection and messaging
- Message publishing to a subject
- Message subscription and receiving
- Field validation in received messages
- Nested data structure validation

**Test Flow**:
1. Connects to NATS server at `nats://nats:4222`
2. Creates a test message with structured data
3. Subscribes to the test subject `test.synthetic.positive`
4. Publishes the test message
5. Validates the received message structure
6. Checks all required fields are present
7. Validates nested data structure

**Expected Result**: Test passes when messages are properly sent and received with correct field validation.

**Test Data Structure**:
```json
{
  "test_id": "nats_positive_test",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "user_id": "test_user_123",
    "action": "test_action",
    "metadata": {
      "source": "synthetic_test",
      "version": "1.0.0"
    }
  }
}
```

**Validation Checks**:
- Required fields: `test_id`, `timestamp`, `data`
- Data fields: `user_id`, `action`, `metadata`
- Metadata fields: `source`, `version`

### 2. NATS Negative Test - Error Handling

**Purpose**: Tests NATS error handling with invalid messages and connection issues.

**What it tests**:
- Invalid JSON message handling
- Missing required fields detection
- Connection timeout scenarios
- Error handling and recovery

**Test Scenarios**:

#### Scenario 1: Invalid JSON Message
- Publishes a non-JSON message
- Tests that the system handles invalid data gracefully

#### Scenario 2: Missing Required Fields
- Publishes a message with missing required fields
- Validates that missing fields are detected
- Ensures proper error handling

#### Scenario 3: Connection Timeout
- Attempts to connect to a non-existent NATS instance
- Tests connection timeout handling
- Validates error recovery

**Expected Result**: Test passes when all error scenarios are properly handled.

**Error Scenarios Tested**:
- Invalid JSON message handling
- Missing required fields detection
- Connection timeout scenarios

## Usage

### Creating NATS Tests

1. **Navigate to StackStorm Tests**:
   - Go to http://localhost:3000
   - Click on "StackStorm Tests" in the navigation

2. **Access Templates**:
   - Click on the "Templates" tab
   - You'll see the NATS Test Templates section

3. **Load Test Template**:
   - Click "Load Positive Test" for the positive test
   - Click "Load Negative Test" for the negative test
   - Or click "Create Both Tests" to create both at once

4. **Review and Customize**:
   - The test code will be loaded into the editor
   - Review the code and modify as needed
   - Adjust test parameters, timeout, and retry settings

5. **Save and Deploy**:
   - Save the test configuration
   - Deploy to StackStorm
   - Execute the test

### API Usage

#### Get Positive Test Template
```bash
curl http://localhost:8004/api/v1/tests/examples/nats/positive
```

#### Get Negative Test Template
```bash
curl http://localhost:8004/api/v1/tests/examples/nats/negative
```

#### Create Both Tests
```bash
curl -X POST http://localhost:8004/api/v1/tests/examples/nats
```

## Test Configuration

### Positive Test Configuration
```json
{
  "name": "NATS Positive Test - Message Validation",
  "description": "Tests NATS message publishing and receiving with field validation",
  "test_type": "action",
  "stackstorm_pack": "synthetic_tests",
  "test_parameters": {
    "subject": "test.synthetic.positive",
    "timeout": 10,
    "expected_fields": ["test_id", "timestamp", "data"]
  },
  "expected_result": {
    "status": "success",
    "message": "NATS message flow test passed"
  },
  "timeout": 30,
  "retry_count": 1,
  "retry_delay": 5,
  "enabled": true,
  "tags": ["nats", "messaging", "positive", "validation"]
}
```

### Negative Test Configuration
```json
{
  "name": "NATS Negative Test - Error Handling",
  "description": "Tests NATS error handling with invalid messages and connection issues",
  "test_type": "action",
  "stackstorm_pack": "synthetic_tests",
  "test_parameters": {
    "subject": "test.synthetic.negative",
    "timeout": 10,
    "error_scenarios": ["invalid_json", "missing_fields", "connection_timeout"]
  },
  "expected_result": {
    "status": "success",
    "message": "NATS negative test scenarios handled correctly"
  },
  "timeout": 30,
  "retry_count": 1,
  "retry_delay": 5,
  "enabled": true,
  "tags": ["nats", "messaging", "negative", "error_handling"]
}
```

## Dependencies

### Required Python Packages
- `nats-py==2.3.0` - NATS Python client
- `asyncio` - Asynchronous I/O support
- `json` - JSON handling
- `datetime` - Timestamp handling

### NATS Server
- NATS server must be running and accessible
- Default connection: `nats://nats:4222`
- Test subjects: `test.synthetic.positive`, `test.synthetic.negative`

## Troubleshooting

### Common Issues

#### NATS Connection Failed
- **Check NATS server**: Ensure NATS is running and accessible
- **Verify connection string**: Check the NATS URL in test code
- **Network connectivity**: Ensure network access to NATS server

#### Message Not Received
- **Check subject**: Verify the subject name matches between publisher and subscriber
- **Timing issues**: Increase wait time in test code
- **NATS configuration**: Check NATS server configuration

#### Field Validation Failed
- **Check message structure**: Verify the message structure matches expected format
- **Required fields**: Ensure all required fields are present
- **Data types**: Check that field values are of expected types

### Debug Tips

1. **Enable Debug Logging**:
   ```bash
   export LOG_LEVEL=DEBUG
   docker-compose restart stackstorm-tests
   ```

2. **Check NATS Server Logs**:
   ```bash
   docker-compose logs nats
   ```

3. **Test NATS Connection**:
   ```bash
   # Test NATS connectivity
   curl http://localhost:8222/varz
   ```

4. **Monitor Test Execution**:
   - Check the "Executions" tab in the web interface
   - Review execution logs and results
   - Check for error messages and stack traces

## Customization

### Modifying Test Data
You can customize the test data by modifying the `test_message` structure in the test code:

```python
test_message = {
    "test_id": "your_custom_test_id",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "data": {
        "user_id": "your_user_id",
        "action": "your_action",
        "metadata": {
            "source": "your_source",
            "version": "your_version"
        }
    }
}
```

### Adding Custom Validation
Add custom validation logic to the test:

```python
# Custom validation
if received_data["data"]["user_id"] != "expected_user_id":
    raise Exception("User ID validation failed")

if received_data["data"]["action"] not in ["allowed_action1", "allowed_action2"]:
    raise Exception("Action validation failed")
```

### Changing Test Subjects
Modify the subject names in the test parameters:

```python
subject = "your.custom.subject.name"
```

## Best Practices

1. **Use Descriptive Test Names**: Make test names clear and descriptive
2. **Include Comprehensive Validation**: Test all important fields and structures
3. **Handle Errors Gracefully**: Include proper error handling and recovery
4. **Use Appropriate Timeouts**: Set reasonable timeouts for test execution
5. **Test Both Positive and Negative Cases**: Include both success and failure scenarios
6. **Document Test Purpose**: Clearly document what each test validates
7. **Use Consistent Data Structures**: Maintain consistent message formats
8. **Monitor Test Results**: Regularly review test execution results and logs

## Integration with Incident Management

When NATS tests fail, incidents are automatically created with the following information:

- **Title**: "Synthetic Test Failed: [Test Name]"
- **Description**: Test failure details and error message
- **Severity**: Medium
- **Incident Type**: synthetic_test_failure
- **Affected Services**: synthetic-testing, nats
- **Tags**: synthetic-test, nats, automated

This ensures that NATS messaging issues are properly tracked and managed through the incident management system.
