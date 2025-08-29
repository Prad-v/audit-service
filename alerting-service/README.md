# Alerting Service

Policy-based alerting service for audit events with support for PagerDuty, Slack, Webhook, and Email providers.

## Features

- **Policy-Based Alerting**: Define alert policies with flexible rule matching
- **Multiple Providers**: PagerDuty, Slack, Webhook, Email
- **Advanced Matching**: Various operators (eq, ne, gt, lt, contains, regex)
- **Time Windows**: Active during specific time periods
- **Throttling**: Prevent alert spam
- **Scalable**: Horizontal scaling support

## Quick Start

```bash
# Start the service
cd alerting-service
docker-compose up -d

# Test the service
python test_alerting.py

# API Documentation
# http://localhost:8001/docs
```

## API Endpoints

- `POST /api/v1/alerts/policies` - Create alert policy
- `POST /api/v1/alerts/providers` - Create alert provider  
- `POST /api/v1/alerts/process-event` - Process event and trigger alerts
- `GET /api/v1/alerts/alerts` - List alerts
- `GET /health` - Health check

## Example Policy

```json
{
  "name": "Failed Login Alerts",
  "rules": [
    {"field": "event_type", "operator": "eq", "value": "user_login"},
    {"field": "status", "operator": "eq", "value": "failed"}
  ],
  "severity": "high",
  "message_template": "Failed login by {user_id} from {ip_address}",
  "providers": ["pagerduty-001", "slack-001"]
}
```

## Integration

Send events from your audit service:

```python
import httpx

async def send_event_to_alerting(event_data):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://alerting-service:8001/api/v1/alerts/process-event",
            headers={"Authorization": "Bearer your-api-key"},
            json=event_data
        )
        return response.json()
```

## Environment Variables

- `ALERTING_DATABASE_URL`: PostgreSQL connection string
- `ALERTING_API_KEY`: API key for authentication
