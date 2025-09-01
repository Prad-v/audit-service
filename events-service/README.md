# Events Service

Cloud service provider events and monitoring service that ingests events from various sources (Grafana, GCP, AWS, Azure, OCI) and provides alerting capabilities.

## Features

- **Multi-Cloud Support**: GCP, AWS, Azure, OCI integration
- **Multi-Cloud Outage Monitoring**: Automated monitoring of cloud provider status pages, RSS feeds, and APIs
- **Grafana Integration**: Process Grafana alert webhooks
- **Event Subscriptions**: Subscribe to specific event types and services
- **Cloud Project Management**: Register and manage cloud provider projects
- **Alerting Integration**: Reuse existing alerting capabilities
- **Webhook Processing**: Handle incoming webhooks from various sources
- **Real-time Processing**: Async event processing and alerting

## Quick Start

```bash
# Start the service
cd events-service
docker-compose up -d

# Test the service
python test_events.py

# API Documentation
# http://localhost:8003/docs
```

## API Endpoints

### Cloud Projects
- `POST /api/v1/providers/projects` - Register cloud project
- `GET /api/v1/providers/projects` - List cloud projects
- `GET /api/v1/providers/projects/{id}/test-connection` - Test connection
- `GET /api/v1/providers/projects/{id}/services` - Get available services
- `GET /api/v1/providers/projects/{id}/regions` - Get available regions

### Event Subscriptions
- `POST /api/v1/subscriptions` - Create event subscription
- `GET /api/v1/subscriptions` - List subscriptions
- `GET /api/v1/subscriptions/{id}/test` - Test subscription
- `GET /api/v1/subscriptions/{id}/events` - Get subscription events

### Events
- `POST /api/v1/events` - Create cloud event
- `GET /api/v1/events` - List events
- `POST /api/v1/events/webhook/grafana` - Grafana webhook
- `POST /api/v1/events/webhook/gcp` - GCP webhook
- `POST /api/v1/events/webhook/aws` - AWS webhook
- `POST /api/v1/events/webhook/azure` - Azure webhook
- `POST /api/v1/events/webhook/oci` - OCI webhook

### Outage Monitoring
- `GET /api/v1/outages/status` - Get outage monitoring status
- `POST /api/v1/outages/start` - Start outage monitoring
- `POST /api/v1/outages/stop` - Stop outage monitoring
- `PUT /api/v1/outages/config` - Update monitoring configuration
- `POST /api/v1/outages/check/{provider}` - Check specific provider for outages
- `POST /api/v1/outages/check/all` - Check all providers for outages
- `GET /api/v1/outages/history` - Get outage history
- `POST /api/v1/outages/webhook/test` - Test webhook delivery

### Alerting
- `POST /api/v1/alerts/policies` - Create alert policy
- `GET /api/v1/alerts/policies` - List alert policies
- `POST /api/v1/alerts/providers` - Create alert provider
- `GET /api/v1/alerts/providers` - List alert providers
- `GET /api/v1/alerts/alerts` - List alerts

## Cloud Provider Configuration

### GCP
```json
{
  "project_id": "your-project-id",
  "service_account_key": {
    "type": "service_account",
    "project_id": "your-project-id",
    "private_key_id": "...",
    "private_key": "...",
    "client_email": "...",
    "client_id": "..."
  }
}
```

### AWS
```json
{
  "access_key_id": "your-access-key",
  "secret_access_key": "your-secret-key",
  "region": "us-east-1"
}
```

### Azure
```json
{
  "subscription_id": "your-subscription-id",
  "tenant_id": "your-tenant-id",
  "client_id": "your-client-id",
  "client_secret": "your-client-secret"
}
```

### OCI
```json
{
  "tenancy_id": "your-tenancy-id",
  "user_id": "your-user-id",
  "fingerprint": "your-fingerprint",
  "private_key": "your-private-key",
  "region": "us-ashburn-1"
}
```

## Event Subscription Example

```json
{
  "name": "Production Alerts",
  "project_id": "gcp-project-001",
  "event_types": ["grafana_alert", "cloud_alert"],
  "services": ["compute.googleapis.com", "storage.googleapis.com"],
  "regions": ["us-central1", "us-east1"],
  "severity_levels": ["critical", "high"],
  "custom_filters": {
    "environment": "production"
  },
  "enabled": true,
  "auto_resolve": true,
  "resolve_after_hours": 24
}
```

## Webhook Integration

### Grafana Webhook
```bash
curl -X POST http://localhost:8003/api/v1/events/webhook/grafana \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "alerts": [
      {
        "status": "firing",
        "labels": {
          "alertname": "High CPU Usage",
          "severity": "critical",
          "service": "compute.googleapis.com"
        },
        "annotations": {
          "summary": "CPU usage is above 90%",
          "description": "Instance cpu-usage is experiencing high load"
        },
        "startsAt": "2023-12-01T10:00:00Z"
      }
    ]
  }'
```

### GCP Webhook
```bash
curl -X POST http://localhost:8003/api/v1/events/webhook/gcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "incident": {
      "incident_id": "incident-123",
      "severity": "high",
      "state": "open",
      "summary": "GCP Service Outage",
      "started_at": "2023-12-01T10:00:00Z"
    }
  }'
```

## Environment Variables

- `EVENTS_DATABASE_URL`: PostgreSQL connection string
- `EVENTS_API_KEY`: API key for authentication
- `EVENTS_LOG_LEVEL`: Logging level (default: INFO)

## Integration with Alerting Service

The Events Service integrates with the existing Alerting Service to provide comprehensive alerting capabilities:

1. **Event Processing**: Events are processed and matched against subscriptions
2. **Alert Triggering**: Matching events trigger alerts based on policies
3. **Provider Delivery**: Alerts are delivered via configured providers (PagerDuty, Slack, etc.)

## Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8003

# Run tests
pytest tests/
```

### Docker Development
```bash
# Build and run
docker build -t events-service .
docker run -p 8003:8003 events-service
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Grafana       │    │   GCP/AWS/      │    │   Custom        │
│   Webhooks      │    │   Azure/OCI     │    │   Webhooks      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │    Events Service         │
                    │  ┌─────────────────────┐  │
                    │  │  Webhook Handlers   │  │
                    │  └─────────────────────┘  │
                    │  ┌─────────────────────┐  │
                    │  │  Event Processor    │  │
                    │  └─────────────────────┘  │
                    │  ┌─────────────────────┐  │
                    │  │  Cloud Providers    │  │
                    │  └─────────────────────┘  │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │   Alerting Service        │
                    │  ┌─────────────────────┐  │
                    │  │  Alert Policies     │  │
                    │  └─────────────────────┘  │
                    │  ┌─────────────────────┐  │
                    │  │  Alert Providers    │  │
                    │  └─────────────────────┘  │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │  PagerDuty/Slack/Email   │
                    └───────────────────────────┘
```

## Monitoring and Observability

- **Health Checks**: `/health` endpoint for service health
- **Metrics**: Prometheus metrics for event processing
- **Logging**: Structured logging with correlation IDs
- **Tracing**: Distributed tracing for event flows

## Security

- **Authentication**: Bearer token authentication
- **Authorization**: Role-based access control
- **Data Encryption**: Encrypted storage for sensitive data
- **Network Security**: Secure communication between services
