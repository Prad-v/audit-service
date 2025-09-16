# Synthetic Test Framework

## Overview

The Synthetic Test Framework is a comprehensive testing solution that allows you to create and execute synthetic tests using a visual DAG (Directed Acyclic Graph) builder. It supports testing message flows between Pub/Sub topics, webhook endpoints, and REST APIs with automatic incident creation on test failures.

## Features

### 🎯 Core Capabilities
- **Visual DAG Builder**: Drag-and-drop interface for creating test workflows
- **Pub/Sub Testing**: Publish and subscribe to Google Cloud Pub/Sub topics
- **REST API Testing**: Make HTTP requests to webhooks and APIs
- **Webhook Testing**: Receive and validate webhook calls
- **Attribute Comparison**: Compare message attributes between nodes
- **Automatic Incident Creation**: Create incidents when tests fail
- **Real-time Execution**: Execute tests and view results in real-time

### 🔧 Supported Node Types

#### 1. Pub/Sub Publisher
- **Purpose**: Publish messages to a Pub/Sub topic
- **Configuration**:
  - Project ID
  - Topic Name
  - Message Data (JSON)
  - Attributes (key-value pairs)
  - Ordering Key (optional)

#### 2. Pub/Sub Subscriber
- **Purpose**: Subscribe to messages from a Pub/Sub topic
- **Configuration**:
  - Project ID
  - Subscription Name
  - Timeout (seconds)
  - Expected Attributes for validation

#### 3. REST Client
- **Purpose**: Make HTTP requests to webhooks or APIs
- **Configuration**:
  - URL
  - HTTP Method (GET, POST, PUT, DELETE, PATCH)
  - Headers
  - Request Body
  - Expected Status Codes

#### 4. Webhook Receiver
- **Purpose**: Receive and validate webhook calls
- **Configuration**:
  - Webhook URL
  - Expected Headers
  - Expected Body Schema
  - Timeout (seconds)

#### 5. Attribute Comparator
- **Purpose**: Compare attributes between messages from different nodes
- **Configuration**:
  - Source Node ID
  - Target Node ID
  - Comparison Rules (attribute, operator, expected value)

#### 6. Incident Creator
- **Purpose**: Create incidents when tests fail
- **Configuration**:
  - Title Template
  - Description Template
  - Severity Level
  - Auto-create flag

#### 7. Delay
- **Purpose**: Add delays between operations
- **Configuration**:
  - Delay Duration (seconds)

#### 8. Condition
- **Purpose**: Conditional branching based on data
- **Configuration**:
  - Condition Expression
  - True Node ID
  - False Node ID

## Use Cases

### Use Case 1: Pub/Sub Message Flow Testing
**Scenario**: Test that messages published to one Pub/Sub topic are received on another topic with matching attributes.

**Workflow**:
1. **Pub/Sub Publisher** → Publish test message to `input-topic`
2. **Delay** → Wait 5 seconds for processing
3. **Pub/Sub Subscriber** → Subscribe to `output-topic`
4. **Attribute Comparator** → Compare message attributes
5. **Incident Creator** → Create incident if comparison fails

### Use Case 2: Webhook to Pub/Sub Integration Testing
**Scenario**: Test that webhook calls trigger Pub/Sub message publishing.

**Workflow**:
1. **REST Client** → POST to webhook endpoint
2. **Webhook Receiver** → Wait for webhook call
3. **Pub/Sub Subscriber** → Subscribe to expected topic
4. **Attribute Comparator** → Compare webhook data with Pub/Sub message
5. **Incident Creator** → Create incident if test fails

## Getting Started

### 1. Access the Framework
Navigate to **Synthetic Tests** in the main navigation menu.

### 2. Create a New Test
1. Click **"New Test"** button
2. Configure test metadata (name, description, tags)
3. Add nodes from the palette
4. Connect nodes to create your workflow
5. Configure each node's properties
6. Save the test

### 3. Execute Tests
1. Select a test from the **Tests** tab
2. Click **"Run"** to execute
3. Monitor execution in the **Executions** tab
4. View detailed results and any created incidents

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/synthetic_tests

# Google Cloud Pub/Sub
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Incident Management
INCIDENT_API_URL=http://localhost:8000/api/v1/incidents

# Webhook Configuration
WEBHOOK_BASE_URL=http://localhost:8002/webhooks

# Redis Cache
REDIS_URL=redis://localhost:6379

# Test Execution
MAX_CONCURRENT_TESTS=10
DEFAULT_TEST_TIMEOUT=300
MAX_TEST_DURATION=1800
```

### Docker Compose Setup

The synthetic test framework is included in the main docker-compose.yml:

```yaml
synthetic-tests:
  build:
    context: ./backend/services/synthetic-tests
    dockerfile: Dockerfile
  ports:
    - "8002:8002"
  environment:
    - DATABASE_URL=postgresql://audit_user:audit_password@postgres:5432/audit_logs
    - GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT:-}
    - INCIDENT_API_URL=http://api:8000/api/v1/incidents
    - WEBHOOK_BASE_URL=http://localhost:8002/webhooks
    - REDIS_URL=redis://redis:6379
  depends_on:
    - postgres
    - redis
    - api
```

## API Reference

### Test Management

#### Create Test
```http
POST /api/v1/synthetic-tests/tests/
Content-Type: application/json

{
  "name": "My Test",
  "description": "Test description",
  "nodes": [...],
  "edges": [...],
  "enabled": true,
  "tags": ["integration", "pubsub"]
}
```

#### Execute Test
```http
POST /api/v1/synthetic-tests/tests/{test_id}/execute
```

#### List Tests
```http
GET /api/v1/synthetic-tests/tests/
```

### Node Configuration Examples

#### Pub/Sub Publisher Node
```json
{
  "node_type": "pubsub_publisher",
  "name": "Publish Test Message",
  "config": {
    "project_id": "my-gcp-project",
    "topic_name": "test-topic",
    "message_data": "{\"test\": \"message\", \"timestamp\": \"2024-01-01T00:00:00Z\"}",
    "attributes": {
      "source": "synthetic-test",
      "test_id": "test-123"
    }
  }
}
```

#### REST Client Node
```json
{
  "node_type": "rest_client",
  "name": "Call Webhook",
  "config": {
    "url": "https://api.example.com/webhook",
    "method": "POST",
    "headers": {
      "Content-Type": "application/json",
      "Authorization": "Bearer token"
    },
    "body": "{\"event\": \"test\", \"data\": \"payload\"}",
    "expected_status_codes": [200, 201, 202]
  }
}
```

#### Attribute Comparator Node
```json
{
  "node_type": "attribute_comparator",
  "name": "Compare Messages",
  "config": {
    "source_node_id": "publisher-node",
    "target_node_id": "subscriber-node",
    "comparisons": [
      {
        "attribute": "message_id",
        "operator": "equals",
        "expected_value": "{{source.message_id}}"
      },
      {
        "attribute": "timestamp",
        "operator": "regex_match",
        "expected_value": "\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z"
      }
    ]
  }
}
```

## Best Practices

### 1. Test Design
- **Keep tests focused**: Each test should verify one specific flow
- **Use meaningful names**: Clear node and test names improve maintainability
- **Add delays appropriately**: Use delay nodes to account for processing time
- **Validate thoroughly**: Use attribute comparators to verify data integrity

### 2. Error Handling
- **Set appropriate timeouts**: Configure realistic timeouts for each operation
- **Handle failures gracefully**: Use incident creators to alert on failures
- **Test error scenarios**: Create tests for both success and failure cases

### 3. Performance
- **Limit concurrent tests**: Use the MAX_CONCURRENT_TESTS setting
- **Optimize test duration**: Set reasonable timeouts and delays
- **Monitor resource usage**: Watch for memory and CPU usage during execution

### 4. Security
- **Secure credentials**: Use environment variables for sensitive data
- **Validate inputs**: Ensure webhook receivers validate incoming data
- **Use HTTPS**: Always use secure connections for external APIs

## Troubleshooting

### Common Issues

#### 1. Pub/Sub Connection Errors
- Verify `GOOGLE_CLOUD_PROJECT` is set correctly
- Check that `GOOGLE_APPLICATION_CREDENTIALS` points to valid credentials
- Ensure topics and subscriptions exist in the project

#### 2. Webhook Timeout Issues
- Increase timeout values for slow-responding endpoints
- Check network connectivity between services
- Verify webhook URLs are accessible

#### 3. Test Execution Failures
- Check node configurations for required fields
- Verify that all referenced nodes exist
- Ensure DAG has no cycles (circular dependencies)

#### 4. Database Connection Issues
- Verify `DATABASE_URL` is correct
- Check that PostgreSQL is running and accessible
- Ensure database user has proper permissions

### Debug Mode

Enable debug logging by setting:
```bash
LOG_LEVEL=DEBUG
```

This will provide detailed information about test execution, node processing, and error conditions.

## Monitoring and Alerting

### Test Execution Monitoring
- View execution history in the **Executions** tab
- Monitor test success/failure rates
- Track execution duration and performance

### Incident Integration
- Failed tests automatically create incidents
- Incidents include test details and error messages
- Integration with existing incident management workflow

### Health Checks
The framework provides health check endpoints:
- `/health` - Overall service health
- `/api/v1/synthetic-tests/health` - Framework-specific health

## Future Enhancements

### Planned Features
- **Scheduled Tests**: Cron-based test scheduling
- **Test Suites**: Group related tests for batch execution
- **Advanced Conditions**: More sophisticated conditional logic
- **Data Generators**: Generate test data dynamically
- **Performance Testing**: Load testing capabilities
- **Test Templates**: Pre-built test templates for common scenarios

### Integration Roadmap
- **CI/CD Integration**: Run tests as part of deployment pipelines
- **Slack/Teams Notifications**: Direct notifications for test failures
- **Metrics Export**: Export test metrics to monitoring systems
- **API Testing**: Enhanced REST API testing capabilities

## Support

For issues, questions, or feature requests:
1. Check the troubleshooting section above
2. Review the API documentation
3. Check service logs for detailed error information
4. Contact the development team for assistance

---

*This framework is designed to provide comprehensive testing capabilities for complex message flows and integrations. Regular updates and improvements are made based on user feedback and requirements.*
