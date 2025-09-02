# Pub/Sub Subscriptions

This document describes how to use the Pub/Sub subscription functionality for Google Cloud Pub/Sub integration with support for service account encryption and workload identity.

## Overview

The Pub/Sub subscription system allows you to create and manage Google Cloud Pub/Sub subscriptions with two authentication methods:

1. **Service Account Key**: Upload and encrypt service account JSON keys
2. **Workload Identity**: Use Kubernetes workload identity for authentication

## Features

- ✅ **Service Account Key Encryption**: All service account keys are encrypted at rest using Fernet encryption
- ✅ **Workload Identity Support**: Native support for Kubernetes workload identity
- ✅ **Advanced Configuration**: Message filtering, dead letter topics, retry policies
- ✅ **Security**: Encrypted storage of sensitive credentials
- ✅ **Testing**: Built-in connection testing for both authentication methods

## Authentication Methods

### 1. Service Account Key

When using service account authentication:

- Upload your service account JSON key file or paste the content
- The key is automatically encrypted before storage
- Supports all standard Pub/Sub operations
- Ideal for development and testing environments

**Security Note**: Service account keys are encrypted using Fernet encryption before being stored in the database.

### 2. Workload Identity

When using workload identity:

- No need to manage service account keys
- Uses the default credentials from the Kubernetes environment
- More secure for production deployments
- Requires proper workload identity configuration in your cluster

## Configuration Options

### Basic Configuration

- **Topic Name**: The Pub/Sub topic to subscribe to
- **Project ID**: Your Google Cloud project ID
- **Subscription ID**: Unique identifier for the subscription
- **Region**: Google Cloud region (default: us-central1)

### Authentication Configuration

#### Service Account
- **Service Account Key**: JSON key content (encrypted when stored)
- **File Upload**: Support for .json file uploads

#### Workload Identity
- **Service Account Email**: The service account email to use
- **Audience**: OIDC audience (default: https://pubsub.googleapis.com/google.pubsub.v1.Publisher)

### Advanced Configuration

- **Ack Deadline**: How long to wait for acknowledgment (10-600 seconds)
- **Message Retention**: How long to keep unacknowledged messages (1d, 3d, 7d, 14d, 30d)
- **Message Ordering**: Enable ordered message delivery
- **Message Filter**: Pub/Sub filter expression for selective message processing
- **Dead Letter Topic**: Topic for failed message processing
- **Max Retry Attempts**: Maximum number of retry attempts (1-10)

## API Endpoints

### Create Subscription
```bash
POST /api/v1/pubsub/subscriptions
```

### List Subscriptions
```bash
GET /api/v1/pubsub/subscriptions?page=1&per_page=10&enabled=true
```

### Get Subscription
```bash
GET /api/v1/pubsub/subscriptions/{subscription_id}
```

### Update Subscription
```bash
PUT /api/v1/pubsub/subscriptions/{subscription_id}
```

### Delete Subscription
```bash
DELETE /api/v1/pubsub/subscriptions/{subscription_id}
```

### Test Connection
```bash
POST /api/v1/pubsub/subscriptions/{subscription_id}/test
```

### Enable/Disable Subscription
```bash
POST /api/v1/pubsub/subscriptions/{subscription_id}/enable
POST /api/v1/pubsub/subscriptions/{subscription_id}/disable
```

## Example Usage

### Creating a Service Account Subscription

```json
{
  "name": "Cloud Events Subscription",
  "description": "Subscription for cloud monitoring events",
  "config": {
    "topic": "cloud-events",
    "project_id": "my-project-123",
    "subscription_id": "cloud-events-sub",
    "authentication_method": "service_account",
    "service_account_key": "{\"type\":\"service_account\",\"project_id\":\"my-project-123\",...}",
    "region": "us-central1",
    "ack_deadline_seconds": 30,
    "message_retention_duration": "7d",
    "enable_message_ordering": false,
    "filter": "attributes.event_type = \"cloud_alert\"",
    "dead_letter_topic": "dead-letter-topic",
    "max_retry_attempts": 3
  },
  "enabled": true,
  "tenant_id": "default",
  "created_by": "admin"
}
```

### Creating a Workload Identity Subscription

```json
{
  "name": "Production Events Subscription",
  "description": "Production subscription using workload identity",
  "config": {
    "topic": "prod-events",
    "project_id": "prod-project-456",
    "subscription_id": "prod-events-sub",
    "authentication_method": "workload_identity",
    "workload_identity": {
      "enabled": true,
      "service_account": "events-processor@prod-project-456.iam.gserviceaccount.com",
      "audience": "https://pubsub.googleapis.com/google.pubsub.v1.Publisher"
    },
    "region": "us-west1",
    "ack_deadline_seconds": 60,
    "message_retention_duration": "14d",
    "enable_message_ordering": true,
    "filter": "attributes.severity = \"high\"",
    "dead_letter_topic": "prod-dead-letter",
    "max_retry_attempts": 5
  },
  "enabled": true,
  "tenant_id": "default",
  "created_by": "admin"
}
```

## Security Considerations

### Service Account Keys
- Keys are encrypted using Fernet encryption before storage
- Encryption key should be managed securely in production
- Consider using workload identity for production deployments

### Workload Identity
- Requires proper Kubernetes configuration
- More secure than service account keys
- Follows security best practices for cloud-native applications

### Access Control
- All endpoints require authentication
- Use proper authorization tokens
- Consider implementing role-based access control

## Troubleshooting

### Common Issues

1. **Service Account Key Invalid**
   - Ensure the JSON key is valid and complete
   - Check that all required fields are present
   - Verify the key hasn't expired

2. **Workload Identity Not Working**
   - Ensure workload identity is enabled in your cluster
   - Verify service account configuration
   - Check IAM bindings and permissions

3. **Connection Test Fails**
   - Verify project ID and topic exist
   - Check authentication credentials
   - Ensure proper IAM permissions

### Testing Connections

Use the test endpoint to verify your configuration:

```bash
curl -X POST "http://localhost:3000/api/v1/pubsub/subscriptions/{subscription_id}/test" \
  -H "Authorization: Bearer your-token"
```

This will validate your authentication method and configuration.

## Integration with Event Pipeline

Pub/Sub subscriptions can be integrated with the Event Pipeline Builder:

1. Create a Pub/Sub subscription as an input source
2. Connect it to event processors for transformation
3. Route processed events to various sinks
4. Build complete event processing workflows

## Best Practices

1. **Use Workload Identity** for production deployments
2. **Rotate Service Account Keys** regularly if using key-based authentication
3. **Implement Dead Letter Topics** for failed message handling
4. **Use Message Filtering** to reduce unnecessary processing
5. **Monitor Subscription Health** using the test endpoints
6. **Set Appropriate Timeouts** based on your processing requirements

## Future Enhancements

- [ ] Support for other Pub/Sub providers (AWS SNS/SQS, Azure Service Bus)
- [ ] Enhanced monitoring and metrics
- [ ] Automatic key rotation
- [ ] Advanced filtering capabilities
- [ ] Integration with external monitoring systems
