# StackStorm Synthetic Test Framework

## Overview

The StackStorm Synthetic Test Framework is a comprehensive solution for creating, deploying, and executing synthetic tests using StackStorm. It provides a web-based interface for writing tests in Python and automatically deploys them to StackStorm for execution. When tests fail, incidents are automatically created in the incident management system.

## Features

### 🧪 Test Creation & Management
- **Web-based Test Editor**: Write StackStorm tests directly in the browser with syntax highlighting
- **Multiple Test Types**: Support for Actions, Workflows, Rules, and Sensors
- **Test Configuration**: Configure timeouts, retry logic, parameters, and expected results
- **Test Organization**: Organize tests into packs and suites

### 🚀 StackStorm Integration
- **Automatic Deployment**: Deploy tests to StackStorm with a single click
- **Real-time Execution**: Execute tests and monitor results in real-time
- **StackStorm API Integration**: Full integration with StackStorm's REST API
- **Execution History**: Track all test executions and their results

### 🚨 Incident Management
- **Automatic Incident Creation**: Failed tests automatically create incidents
- **Rich Incident Data**: Include test details, error messages, and execution context
- **Incident Tracking**: Link test executions to created incidents

### 📊 Monitoring & Analytics
- **Execution Status**: Real-time status of test executions
- **Performance Metrics**: Track test duration and success rates
- **Historical Data**: View execution history and trends

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend UI   │    │  StackStorm      │    │   StackStorm    │
│                 │    │  Test Framework  │    │                 │
│  - Test Editor  │◄──►│                  │◄──►│  - Actions      │
│  - Test List    │    │  - API Client    │    │  - Workflows    │
│  - Executions   │    │  - Test Executor │    │  - Rules        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌──────────────────┐             │
         │              │   PostgreSQL     │             │
         │              │                  │             │
         │              │  - Test Configs  │             │
         │              │  - Executions    │             │
         │              │  - Results       │             │
         │              └──────────────────┘             │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Incident      │    │     Redis        │    │   Monitoring    │
│   Management    │    │                  │    │                 │
│                 │    │  - Caching       │    │  - Health       │
│  - Auto Create  │    │  - Sessions      │    │  - Metrics      │
│  - Track        │    │  - Queues        │    │  - Alerts       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- StackStorm instance (or use the included StackStorm container)
- PostgreSQL database
- Redis for caching

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd audit-service
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your StackStorm configuration
   ```

3. **Start the services**:
   ```bash
   docker-compose up -d
   ```

4. **Access the application**:
   - Frontend: http://localhost:3000
   - StackStorm Tests API: http://localhost:8004
   - StackStorm Web UI: http://localhost:9102 (if using included StackStorm)

### Environment Variables

```bash
# StackStorm Configuration
STACKSTORM_API_URL=http://stackstorm:9101
STACKSTORM_AUTH_URL=http://stackstorm:9100
STACKSTORM_USERNAME=st2admin
STACKSTORM_PASSWORD=st2admin
STACKSTORM_API_KEY=your-api-key

# Database
DATABASE_URL=postgresql://user:password@postgres:5432/stackstorm_tests

# Incident Management
INCIDENT_API_URL=http://api:8000/api/v1/incidents

# Redis
REDIS_URL=redis://redis:6379

# Logging
LOG_LEVEL=INFO
```

## Usage

### Creating a Test

1. **Navigate to StackStorm Tests**:
   - Go to http://localhost:3000
   - Click on "StackStorm Tests" in the navigation

2. **Create a New Test**:
   - Click "New Test" button
   - Fill in test details:
     - **Name**: Descriptive name for your test
     - **Description**: What the test does
     - **Test Type**: Action, Workflow, Rule, or Sensor
     - **StackStorm Pack**: The pack name (default: synthetic_tests)

3. **Write Test Code**:
   ```python
   #!/usr/bin/env python3
   """
   Synthetic test action
   """
   
   import json
   import sys
   from datetime import datetime, timezone
   
   def main():
       """
       Main function for synthetic test
       """
       try:
           # Your test logic here
           # Example: Check if a service is responding
           
           # Simulate test logic
           result = {
               "status": "success",
               "message": "Test passed successfully",
               "timestamp": datetime.now(timezone.utc).isoformat(),
               "data": {
                   "response_time": 0.5,
                   "status_code": 200
               }
           }
           
           print(json.dumps(result))
           return result
           
       except Exception as e:
           # Test failed
           result = {
               "status": "failed",
               "message": str(e),
               "timestamp": datetime.now(timezone.utc).isoformat()
           }
           
           print(json.dumps(result))
           return result
   
   if __name__ == "__main__":
       main()
   ```

4. **Configure Test Parameters**:
   - **Timeout**: Maximum execution time (seconds)
   - **Retry Count**: Number of retries on failure
   - **Retry Delay**: Delay between retries (seconds)
   - **Test Parameters**: JSON object with test parameters
   - **Expected Result**: JSON object with expected output

5. **Save the Test**:
   - Click "Save" to save the test configuration

### Deploying a Test

1. **Deploy to StackStorm**:
   - Click "Deploy to StackStorm" button
   - The test will be packaged and deployed to StackStorm
   - You'll see a "Deployed" status indicator

2. **Verify Deployment**:
   - Check StackStorm Web UI at http://localhost:9102
   - Look for your test in the Actions or Workflows section

### Executing a Test

1. **Run a Test**:
   - Click "Execute" button on any deployed test
   - Monitor the execution in real-time

2. **View Results**:
   - Execution results are displayed in a modal
   - Check the "Executions" tab for historical results
   - Failed tests automatically create incidents

### Test Types

#### Actions
- **Purpose**: Single-purpose test functions
- **Use Case**: API health checks, service validation
- **Code**: Python functions that return success/failure

#### Workflows
- **Purpose**: Multi-step test processes
- **Use Case**: End-to-end testing, complex validation
- **Code**: YAML workflow definitions

#### Rules
- **Purpose**: Event-driven tests
- **Use Case**: Monitoring triggers, scheduled tests
- **Code**: YAML rule definitions with triggers and actions

#### Sensors
- **Purpose**: Continuous monitoring
- **Use Case**: Real-time monitoring, event detection
- **Code**: Python sensor classes

## API Reference

### Test Management

#### Create Test
```http
POST /api/v1/tests/
Content-Type: application/json

{
  "name": "My Test",
  "description": "Test description",
  "test_type": "action",
  "stackstorm_pack": "synthetic_tests",
  "test_code": "#!/usr/bin/env python3\n...",
  "test_parameters": {},
  "timeout": 300,
  "retry_count": 0,
  "retry_delay": 5,
  "enabled": true,
  "tags": ["monitoring", "api"]
}
```

#### List Tests
```http
GET /api/v1/tests/
```

#### Get Test
```http
GET /api/v1/tests/{test_id}
```

#### Update Test
```http
PUT /api/v1/tests/{test_id}
Content-Type: application/json

{
  "name": "Updated Test Name",
  "description": "Updated description"
}
```

#### Delete Test
```http
DELETE /api/v1/tests/{test_id}
```

### Test Execution

#### Deploy Test
```http
POST /api/v1/tests/{test_id}/deploy
```

#### Execute Test
```http
POST /api/v1/tests/{test_id}/execute
```

#### List Executions
```http
GET /api/v1/tests/{test_id}/executions
```

#### Get Execution
```http
GET /api/v1/executions/{execution_id}
```

### StackStorm Integration

#### Check StackStorm Status
```http
GET /api/v1/tests/stackstorm/status
```

#### List StackStorm Executions
```http
GET /api/v1/tests/stackstorm/executions
```

#### Get StackStorm Execution
```http
GET /api/v1/tests/stackstorm/executions/{execution_id}
```

## Best Practices

### Test Design

1. **Keep Tests Focused**: Each test should validate one specific aspect
2. **Use Descriptive Names**: Make test names clear and descriptive
3. **Handle Errors Gracefully**: Always include proper error handling
4. **Return Structured Data**: Use consistent JSON output format
5. **Set Appropriate Timeouts**: Don't set timeouts too high or too low

### Test Code

1. **Use Standard Libraries**: Prefer standard Python libraries when possible
2. **Include Documentation**: Add docstrings and comments
3. **Validate Inputs**: Check input parameters before processing
4. **Log Appropriately**: Use proper logging levels
5. **Clean Up Resources**: Always clean up resources (connections, files, etc.)

### Deployment

1. **Test Locally First**: Test your code before deploying
2. **Use Version Control**: Keep test code in version control
3. **Deploy Incrementally**: Deploy one test at a time
4. **Monitor Deployments**: Watch for deployment errors
5. **Rollback on Issues**: Have a rollback plan for failed deployments

### Monitoring

1. **Set Up Alerts**: Configure alerts for test failures
2. **Monitor Performance**: Track test execution times
3. **Review Logs**: Regularly review test execution logs
4. **Update Tests**: Keep tests updated with system changes
5. **Archive Old Tests**: Remove or archive obsolete tests

## Troubleshooting

### Common Issues

#### Test Deployment Fails
- **Check StackStorm Connection**: Verify StackStorm is running and accessible
- **Validate Test Code**: Ensure Python syntax is correct
- **Check Permissions**: Verify StackStorm user has deployment permissions
- **Review Logs**: Check StackStorm logs for detailed error messages

#### Test Execution Fails
- **Check Test Code**: Look for runtime errors in test code
- **Verify Dependencies**: Ensure all required libraries are available
- **Check Parameters**: Validate test parameters are correct
- **Review Timeout**: Ensure timeout is sufficient for test execution

#### StackStorm Connection Issues
- **Verify Configuration**: Check StackStorm URL and credentials
- **Test Connectivity**: Use curl to test StackStorm API endpoints
- **Check Firewall**: Ensure network connectivity to StackStorm
- **Review Authentication**: Verify authentication credentials are correct

### Debugging

#### Enable Debug Logging
```bash
export LOG_LEVEL=DEBUG
docker-compose restart stackstorm-tests
```

#### Check Service Logs
```bash
# StackStorm Tests service
docker-compose logs stackstorm-tests

# StackStorm service
docker-compose logs stackstorm

# All services
docker-compose logs
```

#### Test API Endpoints
```bash
# Health check
curl http://localhost:8004/health

# StackStorm status
curl http://localhost:8004/api/v1/tests/stackstorm/status

# List tests
curl http://localhost:8004/api/v1/tests/
```

## Security Considerations

### Authentication
- Use strong passwords for StackStorm
- Consider using API keys instead of username/password
- Implement proper access controls
- Regularly rotate credentials

### Network Security
- Use HTTPS in production
- Implement proper firewall rules
- Consider VPN access for sensitive environments
- Monitor network traffic

### Data Protection
- Encrypt sensitive data in transit and at rest
- Implement proper backup procedures
- Use secure database connections
- Regular security audits

## Performance Optimization

### Database
- Use connection pooling
- Implement proper indexing
- Regular database maintenance
- Monitor query performance

### Caching
- Use Redis for caching frequently accessed data
- Implement cache invalidation strategies
- Monitor cache hit rates
- Use appropriate cache TTLs

### StackStorm
- Optimize test execution times
- Use appropriate resource limits
- Monitor StackStorm performance
- Scale StackStorm as needed

## Contributing

### Development Setup

1. **Clone the repository**
2. **Install dependencies**:
   ```bash
   cd backend/services/stackstorm-tests
   pip install -r requirements.txt
   ```
3. **Run tests**:
   ```bash
   pytest
   ```
4. **Start development server**:
   ```bash
   uvicorn app.main:app --reload
   ```

### Code Style

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Include docstrings for functions and classes
- Write unit tests for new features
- Update documentation for changes

### Pull Request Process

1. Create a feature branch
2. Make your changes
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request
6. Address review feedback

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation
- Contact the development team
