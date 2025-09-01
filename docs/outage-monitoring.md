# Multi-Cloud Outage Monitoring

## Overview

The Multi-Cloud Outage Monitoring system provides comprehensive monitoring of cloud provider status pages, RSS feeds, and APIs to detect outages and stream them to the normalized event framework. This system automatically monitors GCP, AWS, and Azure for service disruptions and integrates with the existing alerting and subscription systems.

## Features

### 🔍 **Multi-Cloud Support**
- **Google Cloud Platform (GCP)**: Monitors status.cloud.google.com RSS feed and API
- **Amazon Web Services (AWS)**: Monitors status.aws.amazon.com RSS feed and API
- **Microsoft Azure**: Monitors azure.microsoft.com status feed and API
- **Extensible**: Easy to add support for additional cloud providers

### ⏰ **Scheduled Monitoring**
- **Automatic Checks**: Runs every 5 minutes by default (configurable)
- **Background Processing**: Non-blocking async monitoring
- **Deduplication**: Prevents duplicate outage events
- **Retry Logic**: Handles temporary network issues gracefully

### 📡 **Multiple Data Sources**
- **RSS Feeds**: Real-time status updates from provider RSS feeds
- **Status APIs**: Direct API calls to provider status endpoints
- **Webhook Integration**: Receives outage notifications via webhooks
- **Custom Sources**: Extensible for custom outage sources

### 🎯 **Smart Filtering**
- **Service-Specific**: Filter by specific cloud services
- **Region-Based**: Focus on specific geographic regions
- **Severity Levels**: Filter by critical, high, medium, low, info
- **Custom Filters**: Advanced filtering with custom criteria

### 🔔 **Event Integration**
- **Normalized Events**: Converts outages to standardized event format
- **Subscription Matching**: Routes outages to relevant subscriptions
- **Webhook Delivery**: Sends outage notifications to configured webhooks
- **Alert Integration**: Triggers alerts based on outage policies

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GCP Status    │    │   AWS Status    │    │  Azure Status   │
│   Page/RSS      │    │   Page/RSS      │    │   Page/RSS      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │  Outage Monitoring        │
                    │  Service                  │
                    │  ┌─────────────────────┐  │
                    │  │  Provider Monitors  │  │
                    │  └─────────────────────┘  │
                    │  ┌─────────────────────┐  │
                    │  │  RSS Parser         │  │
                    │  └─────────────────────┘  │
                    │  ┌─────────────────────┐  │
                    │  │  API Client         │  │
                    │  └─────────────────────┘  │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │  Event Processing         │
                    │  ┌─────────────────────┐  │
                    │  │  Event Creation     │  │
                    │  └─────────────────────┘  │
                    │  ┌─────────────────────┐  │
                    │  │  Subscription       │  │
                    │  │  Matching           │  │
                    │  └─────────────────────┘  │
                    │  ┌─────────────────────┐  │
                    │  │  Webhook Delivery   │  │
                    │  └─────────────────────┘  │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │  Alerting System          │
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

## API Endpoints

### Outage Monitoring Management

#### Get Monitoring Status
```http
GET /api/v1/outages/status
```

**Response:**
```json
{
  "service_status": "running",
  "check_interval_seconds": 300,
  "monitored_providers": [
    {
      "provider": "gcp",
      "last_check": "2023-12-01T10:00:00Z",
      "known_outages_count": 2
    },
    {
      "provider": "aws",
      "last_check": "2023-12-01T10:05:00Z",
      "known_outages_count": 0
    }
  ]
}
```

#### Start Monitoring
```http
POST /api/v1/outages/start
```

#### Stop Monitoring
```http
POST /api/v1/outages/stop
```

#### Update Configuration
```http
PUT /api/v1/outages/config?check_interval=600
```

### Manual Outage Checks

#### Check Specific Provider
```http
POST /api/v1/outages/check/{provider}
```

**Parameters:**
- `provider`: `gcp`, `aws`, `azure`

#### Check All Providers
```http
POST /api/v1/outages/check/all
```

### Outage History

#### Get Outage History
```http
GET /api/v1/outages/history?provider=gcp&limit=50
```

**Parameters:**
- `provider` (optional): Filter by cloud provider
- `limit` (optional): Number of outages to return (default: 50)

**Response:**
```json
{
  "outages": [
    {
      "event_id": "outage-gcp-20231201100000",
      "provider": "gcp",
      "service": "compute engine",
      "region": "us-central1",
      "severity": "high",
      "status": "active",
      "title": "GCP Compute Engine Service Disruption",
      "description": "We are investigating reports of an issue with Compute Engine...",
      "event_time": "2023-12-01T10:00:00Z",
      "resolved_at": null,
      "outage_status": "investigating",
      "affected_services": ["compute engine", "load balancing"],
      "affected_regions": ["us-central1", "us-east1"]
    }
  ],
  "total_count": 1
}
```

### Webhook Testing

#### Test Webhook Delivery
```http
POST /api/v1/outages/webhook/test?webhook_url=https://example.com/webhook&provider=gcp
```

## Configuration

### Environment Variables

```bash
# Outage Monitoring Configuration
OUTAGE_CHECK_INTERVAL=300  # Check interval in seconds (default: 300)
OUTAGE_ENABLED=true        # Enable/disable outage monitoring
OUTAGE_LOG_LEVEL=INFO      # Logging level for outage monitoring
```

### Provider-Specific Configuration

Each cloud provider monitor can be configured with custom settings:

```python
# GCP Monitor Configuration
GCP_STATUS_PAGE_URL = "https://status.cloud.google.com/feed"
GCP_API_URL = "https://status.cloud.google.com/api/v1/status"

# AWS Monitor Configuration
AWS_STATUS_PAGE_URL = "https://status.aws.amazon.com/rss/all.rss"
AWS_API_URL = "https://status.aws.amazon.com/data.json"

# Azure Monitor Configuration
AZURE_STATUS_PAGE_URL = "https://azure.microsoft.com/en-us/status/feed/"
AZURE_API_URL = "https://azure.microsoft.com/en-us/status/api/status"
```

## Usage Examples

### 1. Start Outage Monitoring

```bash
# Start the monitoring service
curl -X POST http://localhost:8003/api/v1/outages/start

# Check status
curl http://localhost:8003/api/v1/outages/status
```

### 2. Create Outage Subscription

```bash
curl -X POST http://localhost:8003/api/v1/subscriptions/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Critical Outages",
    "project_id": "my-project",
    "event_types": ["outage_status"],
    "services": ["compute.googleapis.com", "storage.googleapis.com"],
    "regions": ["us-central1"],
    "severity_levels": ["critical", "high"],
    "enabled": true,
    "webhook_url": "https://my-webhook.com/outages"
  }'
```

### 3. Manual Outage Check

```bash
# Check GCP for outages
curl -X POST http://localhost:8003/api/v1/outages/check/gcp

# Check all providers
curl -X POST http://localhost:8003/api/v1/outages/check/all
```

### 4. View Outage History

```bash
# Get recent outages
curl http://localhost:8003/api/v1/outages/history

# Filter by provider
curl "http://localhost:8003/api/v1/outages/history?provider=gcp&limit=10"
```

## Frontend Integration

### Outage Monitoring Page

The frontend includes a dedicated outage monitoring page at `/outage-monitoring` with:

- **Service Status**: Start/stop monitoring and view current status
- **Provider Status**: Individual provider monitoring status
- **Manual Checks**: Trigger manual outage checks
- **Outage History**: View detected outages with filtering
- **Configuration**: Update monitoring settings

### Key Features

- **Real-time Status**: Live updates of monitoring service status
- **Provider Cards**: Individual status for each cloud provider
- **Outage Timeline**: Chronological view of detected outages
- **Severity Filtering**: Filter outages by severity level
- **Service Filtering**: Filter by affected services
- **Region Filtering**: Filter by affected regions

## Monitoring and Alerting

### Outage Event Structure

When an outage is detected, it creates a standardized event:

```json
{
  "event_id": "outage-gcp-20231201100000",
  "event_type": "outage_status",
  "severity": "high",
  "status": "active",
  "cloud_provider": "gcp",
  "title": "GCP Compute Engine Service Disruption",
  "description": "We are investigating reports of an issue with Compute Engine...",
  "service_name": "compute engine",
  "region": "us-central1",
  "event_time": "2023-12-01T10:00:00Z",
  "raw_data": {
    "outage_status": "investigating",
    "affected_services": ["compute engine", "load balancing"],
    "affected_regions": ["us-central1", "us-east1"],
    "source": "rss_feed",
    "raw_outage_data": { ... }
  }
}
```

### Webhook Payload

When an outage matches a subscription, a webhook is sent:

```json
{
  "event_type": "outage_detected",
  "subscription_id": "sub-001",
  "subscription_name": "Critical Outages",
  "outage": {
    "event_id": "outage-gcp-20231201100000",
    "provider": "gcp",
    "service": "compute engine",
    "region": "us-central1",
    "severity": "high",
    "status": "investigating",
    "title": "GCP Compute Engine Service Disruption",
    "description": "We are investigating reports of an issue...",
    "start_time": "2023-12-01T10:00:00Z",
    "affected_services": ["compute engine", "load balancing"],
    "affected_regions": ["us-central1", "us-east1"]
  },
  "timestamp": "2023-12-01T10:00:00Z"
}
```

## Testing

### Run Outage Monitoring Tests

```bash
# Run the comprehensive test suite
python tests/integration/test_outage_monitoring.py
```

### Test Individual Components

```bash
# Test RSS feed parsing
curl https://status.cloud.google.com/feed

# Test webhook delivery
curl -X POST "http://localhost:8003/api/v1/outages/webhook/test?webhook_url=https://webhook.site/your-url&provider=gcp"

# Test manual outage check
curl -X POST http://localhost:8003/api/v1/outages/check/gcp
```

## Troubleshooting

### Common Issues

1. **RSS Feed Unavailable**
   - Check network connectivity
   - Verify RSS feed URLs are correct
   - Check if provider has changed their feed structure

2. **API Rate Limiting**
   - Implement exponential backoff
   - Reduce check frequency
   - Use API keys if available

3. **Duplicate Outages**
   - Check deduplication logic
   - Verify external_id handling
   - Review known_outages tracking

4. **Webhook Delivery Failures**
   - Verify webhook URLs are accessible
   - Check webhook authentication
   - Review webhook payload format

### Logs and Monitoring

```bash
# View outage monitoring logs
docker-compose logs events-service | grep outage

# Check monitoring service status
curl http://localhost:8003/api/v1/outages/status

# Monitor background task status
docker-compose logs events-service | grep "background task"
```

## Extending the System

### Adding New Cloud Providers

1. **Create Provider Monitor**
   ```python
   class NewProviderMonitor(CloudProviderMonitor):
       def __init__(self, session: AsyncSession):
           super().__init__(CloudProvider.NEW_PROVIDER, session)
           self.status_page_url = "https://status.newprovider.com/feed"
           self.api_url = "https://status.newprovider.com/api/status"
   ```

2. **Add to Monitoring Service**
   ```python
   self.monitors = {
       CloudProvider.GCP: GCPMonitor(session),
       CloudProvider.AWS: AWSMonitor(session),
       CloudProvider.AZURE: AzureMonitor(session),
       CloudProvider.NEW_PROVIDER: NewProviderMonitor(session),
   }
   ```

3. **Update Models**
   ```python
   class CloudProvider(str, Enum):
       GCP = "gcp"
       AWS = "aws"
       AZURE = "azure"
       NEW_PROVIDER = "new_provider"
   ```

### Custom Outage Sources

You can add custom outage sources by extending the monitoring system:

```python
class CustomOutageSource:
    async def check_outages(self) -> List[OutageEvent]:
        # Custom outage detection logic
        pass

# Register with monitoring service
outage_service.add_custom_monitor(CloudProvider.CUSTOM, CustomOutageSource())
```

## Best Practices

1. **Monitoring Frequency**
   - Use 5-minute intervals for production
   - Increase frequency during known issues
   - Respect provider rate limits

2. **Error Handling**
   - Implement retry logic with exponential backoff
   - Log all errors for debugging
   - Graceful degradation when sources are unavailable

3. **Performance**
   - Use async/await for all I/O operations
   - Implement connection pooling
   - Cache provider responses when appropriate

4. **Security**
   - Validate all incoming data
   - Sanitize webhook URLs
   - Use HTTPS for all external communications

5. **Reliability**
   - Implement health checks
   - Monitor background task status
   - Set up alerts for monitoring failures
