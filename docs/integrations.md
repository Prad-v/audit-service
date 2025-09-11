# Integrations Guide

This document provides comprehensive information about the available integrations in the audit service, including configuration, usage, and troubleshooting.

## Overview

The audit service supports multiple third-party integrations to enhance workflow automation and incident management:

- **Jira Integration**: Create tickets for incidents
- **StackStorm Integration**: Trigger automated workflows
- **PagerDuty Integration**: Incident escalation and on-call management
- **Webhook Integration**: Send data to external systems

## Jira Integration

### Overview
The Jira integration allows you to automatically create tickets for incidents, enabling seamless incident tracking and management.

### Configuration

#### Required Settings
- **Instance Type**: Choose between Jira Cloud or On-Premise
- **Base URL**: Your Jira instance URL
- **Username/Email**: Your Jira account credentials
- **API Token**: Authentication token for API access
- **Project Key**: Target Jira project for ticket creation
- **Issue Type**: Type of issue to create (Bug, Task, Story, Incident, Problem)

#### Priority Mapping
Map incident severity levels to Jira priority levels:
- Critical → Highest
- High → High
- Medium → Medium
- Low → Low

#### API Token Setup
1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Give it a descriptive label
4. Copy the generated token
5. For on-premise installations, use your password or personal access token

### API Endpoints

#### Get Configuration
```http
GET /api/v1/integrations/jira/config
```

#### Save Configuration
```http
POST /api/v1/integrations/jira/config
Content-Type: application/json

{
  "enabled": true,
  "instance_type": "cloud",
  "base_url": "https://your-domain.atlassian.net",
  "username": "your-email@company.com",
  "api_token": "your-api-token",
  "project_key": "PROJ",
  "issue_type": "Bug",
  "priority_mapping": {
    "critical": "Highest",
    "high": "High",
    "medium": "Medium",
    "low": "Low"
  }
}
```

#### Test Connection
```http
POST /api/v1/integrations/jira/test
Content-Type: application/json

{
  "base_url": "https://your-domain.atlassian.net",
  "username": "your-email@company.com",
  "api_token": "your-api-token"
}
```

#### Create Ticket
```http
POST /api/v1/integrations/jira/create-ticket
Content-Type: application/json

{
  "incident_id": "inc-123",
  "incident_data": {
    "title": "Database connection failed",
    "severity": "high",
    "description": "Unable to connect to primary database"
  }
}
```

## StackStorm Integration

### Overview
StackStorm integration enables triggering automated incident response workflows, allowing for sophisticated automation and orchestration. The integration works as a client endpoint, allowing you to specify pack names and action names dynamically when making requests, making it flexible for use as an alert provider.

### Configuration

#### Required Settings
- **Base URL**: Your StackStorm instance URL
- **API Key**: Authentication key for StackStorm API
- **Timeout**: Request timeout in seconds (default: 30)
- **Retry Count**: Number of retry attempts (default: 3)
- **Ignore SSL**: Skip SSL certificate validation (not recommended for production)

### API Endpoints

#### Get Configuration
```http
GET /api/v1/integrations/stackstorm/config
```

#### Save Configuration
```http
POST /api/v1/integrations/stackstorm/config
Content-Type: application/json

{
  "enabled": true,
  "base_url": "https://stackstorm.your-company.com",
  "api_key": "your-api-key",
  "timeout": 30,
  "retry_count": 3,
  "ignore_ssl": false
}
```

#### Test Connection
```http
POST /api/v1/integrations/stackstorm/test
Content-Type: application/json

{
  "base_url": "https://stackstorm.your-company.com",
  "api_key": "your-api-key"
}
```

#### Execute Action
```http
POST /api/v1/integrations/stackstorm/execute-action
Content-Type: application/json

{
  "incident_id": "inc-123",
  "incident_data": {
    "title": "Service outage detected",
    "severity": "critical",
    "affected_services": ["api", "database"]
  },
  "pack_name": "incident_response",
  "action_name": "create_incident",
  "action_parameters": {
    "escalation_level": "immediate",
    "notification_channels": ["slack", "email"]
  }
}
```

#### Send Alert (Alert Provider)
```http
POST /api/v1/integrations/stackstorm/send-alert
Content-Type: application/json

{
  "alert_id": "alert-456",
  "alert_data": {
    "title": "High CPU usage detected",
    "severity": "warning",
    "affected_services": ["web-server"]
  },
  "pack_name": "monitoring",
  "action_name": "handle_alert",
  "action_parameters": {
    "threshold": 80,
    "notification_channels": ["slack"]
  }
}
```

#### List Available Actions
```http
GET /api/v1/integrations/stackstorm/actions
```

## PagerDuty Integration

### Overview
PagerDuty integration provides incident escalation and on-call management capabilities, ensuring critical incidents reach the right people at the right time.

### Configuration

#### Required Settings
- **Integration Key**: PagerDuty Events API integration key
- **Service ID**: Target PagerDuty service ID
- **Escalation Policy ID**: Escalation policy for incident routing
- **Severity Mapping**: Map incident severity to PagerDuty severity levels

#### Severity Mapping Options
- Critical → critical
- High → error
- Medium → warning
- Low → info

### API Endpoints

#### Get Configuration
```http
GET /api/v1/integrations/pagerduty/config
```

#### Save Configuration
```http
POST /api/v1/integrations/pagerduty/config
Content-Type: application/json

{
  "enabled": true,
  "integration_key": "your-integration-key",
  "service_id": "PXXXXXXXX",
  "escalation_policy_id": "PXXXXXXXX",
  "severity_mapping": {
    "critical": "critical",
    "high": "error",
    "medium": "warning",
    "low": "info"
  }
}
```

#### Test Connection
```http
POST /api/v1/integrations/pagerduty/test
Content-Type: application/json

{
  "integration_key": "your-integration-key"
}
```

#### Create Incident
```http
POST /api/v1/integrations/pagerduty/create-incident
Content-Type: application/json

{
  "incident_id": "inc-123",
  "incident_data": {
    "title": "Critical service failure",
    "component": "payment-service",
    "group": "production"
  },
  "severity": "critical",
  "summary": "Payment processing service is down",
  "source": "audit-service"
}
```

#### Resolve Incident
```http
POST /api/v1/integrations/pagerduty/resolve-incident?incident_id=inc-123
```

## Webhook Integration

### Overview
Webhook integration allows sending incident data to external systems via HTTP requests, providing maximum flexibility for custom integrations.

### Configuration

#### Required Settings
- **URL**: Target webhook endpoint URL
- **HTTP Method**: Request method (POST, PUT, PATCH)
- **Headers**: Custom HTTP headers (JSON format)
- **Timeout**: Request timeout in seconds (default: 30)
- **Retry Count**: Number of retry attempts (default: 3)
- **Verify SSL**: Enable/disable SSL certificate verification

#### Example Headers
```json
{
  "Authorization": "Bearer your-token",
  "X-Custom-Header": "value",
  "Content-Type": "application/json"
}
```

### API Endpoints

#### Get Configuration
```http
GET /api/v1/integrations/webhook/config
```

#### Save Configuration
```http
POST /api/v1/integrations/webhook/config
Content-Type: application/json

{
  "enabled": true,
  "url": "https://your-system.com/webhook",
  "method": "POST",
  "headers": {
    "Authorization": "Bearer your-token",
    "Content-Type": "application/json"
  },
  "timeout": 30,
  "retry_count": 3,
  "verify_ssl": true
}
```

#### Test Connection
```http
POST /api/v1/integrations/webhook/test
Content-Type: application/json

{
  "url": "https://your-system.com/webhook",
  "method": "POST",
  "headers": {
    "Authorization": "Bearer your-token"
  },
  "timeout": 30,
  "verify_ssl": true
}
```

#### Send Webhook
```http
POST /api/v1/integrations/webhook/send
Content-Type: application/json

{
  "incident_id": "inc-123",
  "incident_data": {
    "title": "Service degradation",
    "severity": "medium",
    "affected_services": ["api"]
  },
  "event_type": "incident",
  "custom_payload": {
    "custom_field": "custom_value"
  }
}
```

#### Convenience Endpoints
```http
# Send incident data
POST /api/v1/integrations/webhook/send-incident

# Send alert data
POST /api/v1/integrations/webhook/send-alert
```

#### Validate URL
```http
POST /api/v1/integrations/webhook/validate-url?url=https://your-system.com/webhook
```

## Webhook Payload Format

All webhook integrations send data in the following format:

```json
{
  "event_type": "incident",
  "timestamp": "2024-01-15T10:30:00Z",
  "incident_id": "inc-123",
  "incident_data": {
    "title": "Service outage",
    "severity": "critical",
    "description": "Database connection failed",
    "affected_services": ["api", "database"],
    "component": "payment-service",
    "group": "production"
  },
  "source": "audit-service",
  "custom_details": {
    "additional_field": "value"
  }
}
```

## Troubleshooting

### Common Issues

#### Connection Timeouts
- **Symptom**: Integration tests fail with timeout errors
- **Solution**: Increase timeout values in configuration
- **Check**: Network connectivity and firewall rules

#### Authentication Failures
- **Symptom**: 401/403 errors when testing connections
- **Solution**: Verify API keys, tokens, and credentials
- **Check**: Token expiration and permissions

#### SSL Certificate Errors
- **Symptom**: SSL verification failures for webhooks
- **Solution**: Disable SSL verification or update certificates
- **Check**: Certificate validity and chain

#### Rate Limiting
- **Symptom**: 429 errors from external services
- **Solution**: Implement retry logic with exponential backoff
- **Check**: API rate limits and quotas

### Debugging Tips

1. **Enable Debug Logging**: Set log level to DEBUG for detailed integration logs
2. **Test Connections**: Use the test endpoints before enabling integrations
3. **Monitor Logs**: Check application logs for integration errors
4. **Validate Payloads**: Ensure webhook payloads match expected format
5. **Check Network**: Verify network connectivity and DNS resolution

### Log Messages

Integration activities are logged with the following patterns:
- Configuration changes: `{integration}_configuration_updated`
- Connection tests: `{integration}_connection_test`
- Action executions: `{integration}_action_executed`
- Webhook sends: `webhook_sent`

## Security Considerations

### API Keys and Tokens
- Store credentials securely (use environment variables or secret management)
- Rotate API keys regularly
- Use least-privilege access principles
- Monitor API key usage

### Webhook Security
- Use HTTPS endpoints only
- Implement webhook signature verification
- Validate incoming data
- Use authentication headers

### Network Security
- Restrict network access to integration endpoints
- Use VPN or private networks when possible
- Monitor network traffic
- Implement rate limiting

## Best Practices

### Configuration Management
- Use environment-specific configurations
- Document all integration settings
- Version control configuration templates
- Regular configuration audits

### Monitoring and Alerting
- Monitor integration health
- Set up alerts for integration failures
- Track integration usage metrics
- Regular integration testing

### Error Handling
- Implement comprehensive retry logic
- Use circuit breakers for failing integrations
- Provide fallback mechanisms
- Log all integration errors

### Performance
- Optimize webhook payload sizes
- Use async processing where possible
- Implement connection pooling
- Monitor integration performance metrics

## Migration Guide

### Upgrading Integrations
1. Backup current configurations
2. Test new integration versions in staging
3. Update configurations gradually
4. Monitor for issues during migration
5. Rollback plan ready

### Adding New Integrations
1. Follow the established integration pattern
2. Implement comprehensive error handling
3. Add configuration validation
4. Create test endpoints
5. Update documentation

## Support

For integration-related issues:
1. Check the troubleshooting section above
2. Review application logs
3. Test individual integration components
4. Contact support with detailed error information

## Changelog

### Version 1.0.0
- Initial release with Jira, StackStorm, PagerDuty, and Webhook integrations
- Basic configuration management
- Connection testing capabilities
- Comprehensive API documentation
