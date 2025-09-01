# Event Processor Playground Documentation

## Overview

The **Event Processor Playground** is an interactive testing environment that allows users to test their configured event processors with sample data in real-time. This feature provides a fast and efficient way to validate event processing logic before deploying to production.

## Features

### 🎯 **Real-time Testing**
- Test configured event processors with sample data
- See immediate transformation results
- Validate processor configurations before production use

### 📚 **Sample Test Events**
- **Log Event**: Standard log entries with severity and metadata
- **Alert Event**: Monitoring alerts with thresholds and values
- **Security Event**: Security incidents with IP addresses and attempt counts
- **Audit Event**: User actions and authentication events

### 🔄 **Test Management**
- Export test results as JSON files
- Clear test history and results
- Track processor performance and success rates

### 📊 **Test History**
- View recent test results
- Compare input vs output field counts
- Track processor performance over time

## Getting Started

### Accessing the Playground

1. Navigate to the **Event Framework** page
2. Click on the **Processor Playground** tab
3. Select an event processor to test

### Basic Usage

1. **Select Processor**: Choose from your configured event processors
2. **Load Sample Event**: Use predefined sample events or create custom JSON
3. **Run Test**: Click "Test Processor" to see the transformed output
4. **Review Results**: Check the output panel for results or errors

## Event Processor Types

### 🔄 **Transformer**
- **Purpose**: Transform and modify event data
- **Functions**: Field mapping, data conversion, string operations
- **Example**: Convert severity levels, format timestamps, normalize fields

### 📈 **Enricher**
- **Purpose**: Add additional data to events
- **Functions**: Static values, timestamps, UUIDs, environment variables
- **Example**: Add correlation IDs, environment tags, processing metadata

### 🔍 **Filter**
- **Purpose**: Filter events based on conditions
- **Functions**: Field comparisons, pattern matching, logical operators
- **Example**: Filter by severity, event type, or custom conditions

### 🛣️ **Router**
- **Purpose**: Route events to different destinations
- **Functions**: Conditional routing, priority-based selection
- **Example**: Route security events to security queue, errors to error queue

## Sample Test Events

### 1. Log Event
```json
{
  "event_type": "log",
  "severity": "error",
  "message": "database connection failed",
  "source": "app-server-01",
  "user_id": "user123",
  "session_id": "sess456",
  "timestamp": "2024-01-15T10:30:45Z",
  "metadata": {
    "service": "auth-service",
    "region": "us-west-1",
    "environment": "production"
  }
}
```

### 2. Alert Event
```json
{
  "event_type": "alert",
  "severity": "warning",
  "message": "High CPU usage detected",
  "source": "monitoring-system",
  "component": "web-server",
  "value": 85.5,
  "threshold": 80.0,
  "timestamp": "2024-01-15T10:30:45Z"
}
```

### 3. Security Event
```json
{
  "event_type": "security",
  "severity": "critical",
  "message": "Failed login attempt",
  "source": "auth-service",
  "user_id": "unknown",
  "ip_address": "192.168.1.100",
  "attempt_count": 5,
  "timestamp": "2024-01-15T10:30:45Z"
}
```

### 4. Audit Event
```json
{
  "event_type": "audit",
  "severity": "info",
  "message": "User login successful",
  "source": "auth-service",
  "user_id": "admin",
  "action": "login",
  "ip_address": "192.168.1.50",
  "timestamp": "2024-01-15T10:30:45Z"
}
```

## Testing Workflow

### 1. **Create Event Processors**
First, create event processors in the **Event Processors** tab:
- Configure transformation rules
- Set up enrichment fields
- Define filter conditions
- Configure routing rules

### 2. **Test in Playground**
- Select the processor you want to test
- Choose a sample event or create custom JSON
- Run the test and review results

### 3. **Validate Results**
- Check that transformations are applied correctly
- Verify enrichment data is added
- Ensure filtering works as expected
- Confirm routing decisions are correct

### 4. **Iterate and Improve**
- Modify processor configuration based on test results
- Test with different event types
- Export successful configurations

## Best Practices

### 1. **Test Coverage**
- Test with various event types and severities
- Include edge cases and boundary conditions
- Test with missing or malformed data

### 2. **Validation**
- Verify output format and structure
- Check that required fields are present
- Ensure data types are correct

### 3. **Performance**
- Monitor processing time for complex transformations
- Test with large event volumes
- Optimize processor configurations

### 4. **Documentation**
- Document test scenarios and expected results
- Keep track of successful configurations
- Share test results with team members

## API Integration

### Backend Endpoint
The playground uses the existing processor test endpoint:

```
POST /api/v1/processors/{processor_id}/test
```

**Request Body:**
```json
{
  "event_type": "log",
  "severity": "error",
  "message": "test message",
  "source": "test-source"
}
```

**Response:**
```json
{
  "result": {
    "transformed_event_data": "..."
  },
  "timestamp": "2024-01-15T10:30:45Z"
}
```

## Troubleshooting

### Common Issues

1. **No Processors Available**
   - Create event processors in the Event Processors tab first
   - Ensure processors are enabled and properly configured

2. **Test Failures**
   - Check processor configuration for errors
   - Verify input event format is valid JSON
   - Review processor logs for detailed error messages

3. **Unexpected Results**
   - Verify processor configuration matches test scenario
   - Check field mappings and transformation rules
   - Test with simpler configurations first

### Debugging Tips

1. **Start Simple**: Test with basic transformations first
2. **Incremental Testing**: Add complexity step by step
3. **Use Sample Events**: Leverage provided sample events
4. **Check Configuration**: Verify processor settings
5. **Review Logs**: Check backend logs for detailed errors

## Advanced Features

### Test History
- Track all test runs with timestamps
- Compare input and output field counts
- Monitor processor performance over time

### Export Results
- Export test results as JSON files
- Include processor configuration and test data
- Share results with team members

### Processor Information
- View detailed processor configuration
- See transformation rules and settings
- Monitor processor statistics

## Integration with Event Framework

The Event Processor Playground is designed to work seamlessly with the Event Framework:

1. **Create Processors**: Configure processors in the Event Processors tab
2. **Test in Playground**: Validate configurations with sample data
3. **Deploy to Production**: Use tested processors in live environments
4. **Monitor Performance**: Track processor performance and success rates

## Future Enhancements

Planned improvements for the Event Processor Playground:

- **Batch Testing**: Test multiple events simultaneously
- **Performance Metrics**: Execution time and resource usage
- **Visual Comparisons**: Side-by-side input/output comparison
- **Test Suites**: Save and run predefined test scenarios
- **Integration Testing**: Test processor chains and workflows
- **Real-time Monitoring**: Live processor performance tracking

## Support

For issues or questions about the Event Processor Playground:

1. Check the troubleshooting section above
2. Review processor configuration in the Event Processors tab
3. Test with provided sample events
4. Contact the development team for complex issues

---

*This playground provides a safe environment to test and validate event processor configurations before deploying to production environments.*
