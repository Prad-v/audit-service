# Product Status - Incident Management

## Overview

The Product Status system provides comprehensive incident management capabilities for tracking and communicating product outages, service disruptions, and maintenance activities. It integrates with our events framework and uses CloudEvent schema for real-time updates and integrations.

## Features

### 🚨 Incident Management
- **Create Incidents**: Report new outages, degraded performance, or maintenance activities
- **Status Tracking**: Monitor incident lifecycle from investigation to resolution
- **Real-time Updates**: Add incremental updates with status changes and progress
- **Timeline View**: Complete audit trail of all incident activities

### 📊 Status Dashboard
- **Summary Cards**: Quick overview of active, resolved, and investigating incidents
- **Filtering**: Filter incidents by status, severity, type, service, and region
- **Pagination**: Navigate through large numbers of incidents efficiently
- **Real-time Refresh**: Get latest incident status updates

### 🔗 RSS Feed Support
- **Public RSS**: Subscribe to incident updates via RSS feed
- **Configurable**: Include/exclude resolved incidents, control feed size
- **Standard Format**: Compatible with all RSS readers and aggregators
- **Multiple Feeds**: General status feed and incident-specific feeds

### ⚡ CloudEvent Integration
- **Event-Driven**: All incident activities generate CloudEvents
- **Real-time**: Instant notifications for incident lifecycle changes
- **Standard Schema**: Uses CloudEvents 1.0 specification
- **Integration Ready**: Connect with external monitoring and alerting systems

## Incident Lifecycle

### 1. **Investigating** 🔍
- Initial incident report created
- Team begins investigation
- Status updates as findings emerge

### 2. **Identified** 🎯
- Root cause determined
- Impact assessment completed
- Resolution plan developed

### 3. **Monitoring** 👀
- Resolution in progress
- Regular status updates
- Progress tracking

### 4. **Resolved** ✅
- Issue fixed
- Services restored
- Post-incident review initiated

### 5. **Post Incident** 📋
- Lessons learned documented
- Process improvements identified
- Incident report finalized

## Incident Severity Levels

| Level | Description | Response Time | Example |
|-------|-------------|---------------|---------|
| **Critical** | Complete service outage affecting all users | Immediate | Database down, authentication failure |
| **High** | Significant service degradation | 1 hour | Slow response times, partial outages |
| **Medium** | Moderate impact on some users | 4 hours | Feature unavailable, performance issues |
| **Low** | Minor impact or cosmetic issues | 24 hours | UI glitches, non-critical features |
| **Minor** | Minimal impact, maintenance | 48 hours | Scheduled maintenance, updates |

## Incident Types

- **Outage**: Complete service unavailability
- **Degraded Performance**: Service available but slow/unreliable
- **Maintenance**: Planned service interruptions
- **Security**: Security-related incidents
- **Feature Disabled**: Specific features temporarily unavailable
- **Other**: Miscellaneous incidents

## API Endpoints

### Incident Management
```http
POST   /api/v1/incidents                    # Create new incident
GET    /api/v1/incidents                    # List incidents with filtering
GET    /api/v1/incidents/{id}              # Get specific incident
PUT    /api/v1/incidents/{id}              # Update incident
DELETE /api/v1/incidents/{id}              # Delete incident (soft delete)
```

### Incident Updates
```http
POST   /api/v1/incidents/{id}/updates      # Add status update
```

### Status and RSS
```http
GET    /api/v1/incidents/status/summary    # Get incident summary
GET    /api/v1/incidents/rss/feed         # Get RSS feed
```

## CloudEvent Types

### Incident Events
- `com.example.incident.created` - New incident created
- `com.example.incident.updated` - Incident details updated
- `com.example.incident.update_added` - Status update added
- `com.example.incident.resolved` - Incident resolved
- `com.example.incident.deleted` - Incident deleted

### Event Schema
```json
{
  "type": "com.example.incident.created",
  "source": "/incident-management",
  "id": "uuid",
  "time": "2024-01-01T12:00:00Z",
  "subject": "incident-abc123",
  "data": {
    "incident_id": "incident-abc123",
    "title": "Database Connection Issues",
    "status": "investigating",
    "severity": "high",
    "affected_services": ["database", "api"],
    "start_time": "2024-01-01T12:00:00Z"
  }
}
```

## RSS Feed Configuration

### Feed Options
- **Include Resolved**: Show/hide resolved incidents
- **Max Items**: Control feed size (1-100 items)
- **Update Frequency**: TTL settings for feed caching

### RSS Format
```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Product Status - Incident Updates</title>
    <description>Real-time updates on product outages and incidents</description>
    <link>https://status.example.com</link>
    <language>en-US</language>
    <lastBuildDate>Mon, 01 Jan 2024 12:00:00 GMT</lastBuildDate>
    <ttl>300</ttl>
    <item>
      <title>Database Connection Issues - Investigating</title>
      <description>We are investigating database connection issues</description>
      <link>https://status.example.com/incidents/incident-abc123</link>
      <guid>https://status.example.com/incidents/incident-abc123</guid>
      <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
      <category>outage</category>
      <severity>high</severity>
      <status>investigating</status>
    </item>
  </channel>
</rss>
```

## Usage Examples

### Creating an Incident
```typescript
const incident = await eventsApi.createIncident({
  title: "API Response Time Degradation",
  description: "Users experiencing slow API response times",
  severity: "medium",
  incident_type: "degraded_performance",
  affected_services: ["api-gateway", "user-service"],
  affected_regions: ["us-east-1", "us-west-2"],
  start_time: new Date().toISOString(),
  public_message: "We are investigating increased API response times",
  internal_notes: "Monitoring shows 95th percentile latency increased by 200ms"
})
```

### Adding an Update
```typescript
const update = await eventsApi.addIncidentUpdate(incidentId, {
  status: "identified",
  message: "Root cause identified: database connection pool exhaustion",
  public_message: "We have identified the issue and are working on a fix",
  update_type: "status_update"
})
```

### Getting RSS Feed
```typescript
const rssFeed = await eventsApi.getIncidentRSS(false, 20)
// Returns RSS XML content for active incidents only, max 20 items
```

## Integration Points

### External Monitoring
- **PagerDuty**: Incident creation triggers PagerDuty alerts
- **Slack**: Real-time notifications to Slack channels
- **Email**: Automated email notifications to stakeholders
- **Webhooks**: Custom webhook integrations

### Internal Systems
- **Event Pipeline**: Connect with event processing workflows
- **Alert Management**: Integrate with alert rules and policies
- **Audit Logs**: All activities logged for compliance
- **Dashboard**: Real-time status display

## Best Practices

### Incident Communication
1. **Be Transparent**: Provide clear, honest updates
2. **Regular Updates**: Update status every 30 minutes during active incidents
3. **User Impact**: Focus on how incidents affect users
4. **Resolution Timeline**: Provide realistic estimates when possible

### Incident Management
1. **Quick Response**: Acknowledge incidents within 5 minutes
2. **Status Updates**: Update status as investigation progresses
3. **Documentation**: Record all actions and decisions
4. **Post-Mortem**: Conduct thorough post-incident reviews

### RSS Feed Usage
1. **Public Access**: Make RSS feeds publicly accessible
2. **Regular Updates**: Ensure feeds are updated in real-time
3. **Clear Titles**: Use descriptive incident titles
4. **Consistent Format**: Maintain consistent RSS structure

## Troubleshooting

### Common Issues

**Incident Not Appearing in RSS Feed**
- Check if `rss_enabled` is set to `true`
- Verify incident is marked as `is_public`
- Ensure incident status is not `resolved` (if configured to exclude)

**CloudEvents Not Generated**
- Verify CloudEvent service is running
- Check database connectivity
- Review incident creation logs

**RSS Feed Format Issues**
- Validate XML structure
- Check content encoding
- Verify RSS reader compatibility

### Debug Commands
```bash
# Check incident status
curl -H "Authorization: Bearer token" \
  "http://localhost:8003/api/v1/incidents/status/summary"

# Test RSS feed
curl "http://localhost:8003/api/v1/incidents/rss/feed"

# Verify CloudEvents
curl -H "Authorization: Bearer token" \
  "http://localhost:8003/api/v1/events"
```

## Configuration

### Environment Variables
```bash
# Incident Management
INCIDENT_RSS_ENABLED=true
INCIDENT_MAX_UPDATES=100
INCIDENT_AUTO_RESOLVE_HOURS=72

# CloudEvent Integration
CLOUDEVENT_BROKER_URL=nats://localhost:4222
CLOUDEVENT_TOPIC=incidents
```

### Database Schema
The system uses PostgreSQL with the following key tables:
- `incidents`: Main incident records
- `incident_updates`: Status update history
- `cloud_events`: Event audit trail

## Support

For questions or issues with the Product Status system:
- **Documentation**: Check this guide and API docs
- **Logs**: Review application logs for errors
- **Metrics**: Monitor incident response times and resolution rates
- **Team**: Contact the platform team for assistance
