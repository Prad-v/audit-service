# Event Pipeline Builder - DAG-Based Event Processing

## Overview

The Event Pipeline Builder is a **Directed Acyclic Graph (DAG)** interface for building event processing pipelines using our **Event Management System**, inspired by Vector's pipeline design pattern. It provides a visual, drag-and-drop interface for creating complex event processing workflows with real-time validation and execution control.

## Key Features

### 🎯 **DAG-Based Architecture**
- **Directed Acyclic Graph**: Ensures no circular dependencies in event flow
- **Visual Pipeline Design**: Intuitive canvas-based interface
- **Real-time Validation**: Immediate feedback on pipeline structure
- **Cycle Detection**: Prevents circular references automatically

### 🔧 **Node Types (Our Event Management System)**

#### **Event Subscription Nodes (Sources)**
- **Webhook**: HTTP endpoint for receiving events
- **File Watcher**: File system monitoring and ingestion
- **Syslog**: System log collection
- **Kafka Consumer**: Apache Kafka message consumption
- **HTTP Client**: HTTP-based event collection
- **Pub/Sub**: Google Cloud Pub/Sub consumer
- **Kinesis**: AWS Kinesis stream consumer
- **NATS**: NATS messaging system consumer

#### **Event Processor Nodes (Transforms)**
- **Transformer**: Field mappings and data modifications
- **Filter**: Conditional event filtering
- **Enricher**: Add metadata and context
- **Aggregator**: Time-window based aggregations
- **Sampler**: Event sampling and throttling
- **Deduplicator**: Duplicate event removal

#### **Event Sink Nodes (Destinations)**
- **HTTP Endpoint**: HTTP-based event delivery
- **Elasticsearch**: Search and analytics storage
- **Kafka Producer**: Apache Kafka message production
- **S3 Storage**: AWS S3 object storage
- **Database**: PostgreSQL, MySQL, MongoDB, Redis
- **File Output**: Local file system output
- **Console Output**: Development and debugging output

### 🎨 **Visual Interface**

#### **Canvas Features**
- **Drag & Drop**: Move nodes freely on the canvas
- **Connection Management**: Visual connection lines between nodes
- **Zoom & Pan**: Navigate large pipelines easily
- **Node Selection**: Click to select and configure nodes
- **Connection Points**: Visual indicators for input/output connections

#### **Pipeline Templates**
- **Webhook to Event Processor Pipeline**: Multi-source event processing
- **Multi-Source Event Processing Pipeline**: Complex event routing and enrichment
- **Custom Templates**: Save and reuse pipeline designs

### ⚡ **Pipeline Execution**

#### **Execution Modes**
- **Streaming**: Real-time event processing
- **Batch**: Batch-based processing with configurable windows

#### **Control Operations**
- **Start**: Begin pipeline execution
- **Pause**: Temporarily halt processing
- **Stop**: Complete pipeline shutdown
- **Resume**: Continue from paused state

#### **Monitoring & Metrics**
- **Real-time Metrics**: Events per second, total counts
- **Status Indicators**: Node health and execution status
- **Error Tracking**: Validation and runtime error display
- **Performance Monitoring**: Processing latency and throughput

## Architecture

### **DAG Structure**
```
Event Subscription → Event Processor → Event Sink
        ↓                ↓              ↓
   [Webhook] → [Transformer] → [Elasticsearch]
        ↓                ↓              ↓
   [File Log] → [Filter] → [Kafka]
```

### **Data Flow**
1. **Event Ingestion**: Event subscription nodes collect events from various inputs
2. **Event Processing**: Event processor nodes modify, filter, and enrich events
3. **Event Routing**: Events flow through the DAG based on connections
4. **Event Output**: Event sink nodes deliver processed events to destinations

### **Validation Rules**
- **No Cycles**: Prevents infinite loops in event processing
- **Connected Nodes**: All nodes must be part of the event flow
- **Source Requirements**: At least one event subscription node required
- **Sink Requirements**: At least one event sink node required
- **Type Compatibility**: Ensures compatible data flow between nodes

## Usage Guide

### **Creating a New Pipeline**

1. **Navigate** to the Event Pipeline Builder
2. **Click** "Create New Pipeline"
3. **Add Nodes** using the toolbar buttons:
   - **Event Subscription**: For event sources
   - **Event Processor**: For event transformations
   - **Event Sink**: For event destinations
4. **Configure** each node with appropriate settings
5. **Connect** nodes to establish event flow
6. **Validate** the pipeline structure
7. **Save** the pipeline configuration

### **Adding Nodes**

#### **Event Subscription Node**
```typescript
// Example: Webhook Event Subscription
{
  type: 'event_subscription',
  name: 'Webhook Events',
  config: {
    type: 'webhook',
    endpoint: '/api/webhook/audit',
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  },
  eventSubscriptionId: 'webhook-001'
}
```

#### **Event Processor Node**
```typescript
// Example: Event Transformer
{
  type: 'event_processor',
  name: 'Audit Event Processor',
  config: {
    type: 'transformer',
    rules: [
      {
        type: 'field_mapping',
        source: 'message',
        target: 'processed_message'
      },
      {
        type: 'field_transformation',
        field: 'level',
        operation: 'uppercase'
      }
    ]
  },
  eventProcessorId: 'processor-001'
}
```

#### **Event Sink Node**
```typescript
// Example: Elasticsearch Sink
{
  type: 'event_sink',
  name: 'Elasticsearch Sink',
  config: {
    type: 'elasticsearch',
    endpoint: 'http://es:9200',
    index: 'audit-events',
    batchSize: 1000
  },
  eventSinkId: 'sink-001'
}
```

### **Connecting Nodes**

1. **Click** the connection button (→) on a source node
2. **Drag** to the target node
3. **Release** to create the connection
4. **Verify** the connection appears as a line
5. **Click** connection lines to delete if needed

### **Configuring Nodes**

1. **Click** the settings icon (⚙️) on any node
2. **Fill** in the required configuration fields
3. **Set** advanced options if needed
4. **Test** the configuration (if available)
5. **Save** the configuration

### **Pipeline Validation**

#### **Real-time Validation**
- **Automatic**: Continuous validation as you build
- **Visual Indicators**: Red borders for invalid nodes
- **Error Messages**: Detailed validation feedback

#### **Manual Validation**
- **Click** "Validate" button
- **Review** validation results
- **Fix** any identified issues
- **Re-validate** until successful

### **Pipeline Execution**

#### **Starting a Pipeline**
1. **Ensure** pipeline validation passes
2. **Click** "Start Pipeline" button
3. **Monitor** execution status
4. **Watch** real-time metrics

#### **Managing Execution**
- **Pause**: Temporarily stop processing
- **Resume**: Continue from paused state
- **Stop**: Complete shutdown
- **Monitor**: Track performance metrics

## Configuration Examples

### **Webhook to Event Processor Pipeline**

```yaml
name: "Webhook to Event Processor Pipeline"
description: "Receive webhook events, process through event processor, and route to multiple sinks"

nodes:
  - id: "webhook-subscription-1"
    type: "event_subscription"
    name: "Webhook Events"
    config:
      type: "webhook"
      endpoint: "/api/webhook/audit"
      method: "POST"
      headers: { "Content-Type": "application/json" }
    eventSubscriptionId: "webhook-001"

  - id: "event-processor-1"
    type: "event_processor"
    name: "Audit Event Processor"
    config:
      type: "transformer"
      rules: [
        {
          type: "field_mapping",
          source: "message",
          target: "processed_message"
        },
        {
          type: "field_transformation",
          field: "level",
          operation: "uppercase"
        }
      ]
    eventProcessorId: "processor-001"

  - id: "event-sink-1"
    type: "event_sink"
    name: "Elasticsearch Sink"
    config:
      type: "elasticsearch"
      endpoint: "http://es:9200"
      index: "audit-events"
      batchSize: 1000
    eventSinkId: "sink-001"

  - id: "event-sink-2"
    type: "event_sink"
    name: "Kafka Sink"
    config:
      type: "kafka"
      bootstrapServers: "kafka:9092"
      topic: "audit-events"
      batchSize: 500
    eventSinkId: "sink-002"

connections:
  - sourceId: "webhook-subscription-1"
    targetId: "event-processor-1"
    type: "event_flow"
    routingRules:
      conditions: []
      transformations: []

  - sourceId: "event-processor-1"
    targetId: "event-sink-1"
    type: "event_flow"
    routingRules:
      conditions: [{ field: "level", operator: "equals", value: "error" }]
      transformations: []

  - sourceId: "event-processor-1"
    targetId: "event-sink-2"
    type: "event_flow"
    routingRules:
      conditions: [{ field: "level", operator: "equals", value: "info" }]
      transformations: []
```

### **Multi-Source Event Processing Pipeline**

```yaml
name: "Multi-Source Event Processing Pipeline"
description: "Collect events from multiple sources, process through enrichment, and route based on business rules"

nodes:
  - id: "webhook-subscription-1"
    type: "event_subscription"
    name: "API Webhook"
    config:
      type: "webhook"
      endpoint: "/api/events"
      method: "POST"
    eventSubscriptionId: "webhook-002"

  - id: "webhook-subscription-2"
    type: "event_subscription"
    name: "File Watcher"
    config:
      type: "file"
      path: "/var/log/events/*.log"
      format: "json"
    eventSubscriptionId: "webhook-003"

  - id: "event-processor-1"
    type: "event_processor"
    name: "Event Enricher"
    config:
      type: "enricher"
      rules: [
        {
          type: "field_addition",
          field: "timestamp",
          value: "now()"
        },
        {
          type: "field_addition",
          field: "host",
          value: "env.HOSTNAME"
        }
      ]
    eventProcessorId: "processor-002"

  - id: "event-processor-2"
    type: "event_processor"
    name: "Event Filter"
    config:
      type: "filter"
      rules: [
        {
          type: "condition",
          field: "severity",
          operator: "in",
          value: ["high", "critical"]
        }
      ]
    eventProcessorId: "processor-003"

  - id: "event-sink-1"
    type: "event_sink"
    name: "Alert System"
    config:
      type: "http"
      endpoint: "https://alerts.example.com/webhook"
      method: "POST"
    eventSinkId: "sink-003"

  - id: "event-sink-2"
    type: "event_sink"
    name: "Data Warehouse"
    config:
      databaseType: "postgresql"
      connectionString: "postgresql://user:pass@db:5432/events"
    eventSinkId: "sink-004"

connections:
  - sourceId: "webhook-subscription-1"
    targetId: "event-processor-1"
    type: "event_flow"
    routingRules:
      conditions: []
      transformations: []

  - sourceId: "webhook-subscription-2"
    targetId: "event-processor-1"
    type: "event_flow"
    routingRules:
      conditions: []
      transformations: []

  - sourceId: "event-processor-1"
    targetId: "event-processor-2"
    type: "event_flow"
    routingRules:
      conditions: []
      transformations: []

  - sourceId: "event-processor-2"
    targetId: "event-sink-1"
    type: "event_flow"
    routingRules:
      conditions: [{ field: "severity", operator: "equals", value: "critical" }]
      transformations: []

  - sourceId: "event-processor-2"
    targetId: "event-sink-2"
    type: "event_flow"
    routingRules:
      conditions: [{ field: "severity", operator: "equals", value: "high" }]
      transformations: []
```

## Advanced Features

### **Event Routing Rules**

Each connection can have routing rules that determine how events flow:

```yaml
routingRules:
  conditions:
    - field: "severity"
      operator: "equals"
      value: "error"
    - field: "service"
      operator: "in"
      value: ["audit-service", "auth-service"]
  transformations:
    - type: "field_add"
      field: "priority"
      value: "high"
    - type: "field_modify"
      field: "timestamp"
      operation: "format"
      format: "iso8601"
```

### **Advanced Configuration**

#### **Batch Processing**
```yaml
config:
  batchSize: 1000          # Events per batch
  batchTimeout: 1000       # Milliseconds to wait
  retryAttempts: 3         # Retry on failure
  bufferSize: 10000        # In-memory buffer
```

#### **Error Handling**
```yaml
config:
  onError: "drop"          # drop, retry, or dead_letter
  deadLetterQueue: "dlq"   # Dead letter queue name
  maxRetries: 5            # Maximum retry attempts
```

#### **Performance Tuning**
```yaml
config:
  parallelism: 4           # Concurrent processing threads
  bufferTimeout: 500       # Buffer flush timeout
  compression: "gzip"      # Data compression
```

## Best Practices

### **Pipeline Design**

1. **Keep it Simple**: Start with basic pipelines and add complexity gradually
2. **Use Templates**: Leverage pre-built templates for common patterns
3. **Validate Early**: Use real-time validation to catch issues early
4. **Test Thoroughly**: Test with sample data before production deployment
5. **Monitor Performance**: Watch metrics and adjust configuration as needed

### **Node Configuration**

1. **Event Subscription Nodes**: Ensure reliable data ingestion with proper error handling
2. **Event Processor Nodes**: Use clear, simple transformation rules
3. **Event Sink Nodes**: Configure appropriate batch sizes and timeouts
4. **Error Handling**: Implement proper error handling and dead letter queues

### **Performance Optimization**

1. **Batch Processing**: Use appropriate batch sizes for your use case
2. **Parallelism**: Increase parallelism for high-throughput scenarios
3. **Buffering**: Configure buffers to handle traffic spikes
4. **Monitoring**: Track metrics to identify bottlenecks

## Troubleshooting

### **Common Issues**

#### **Validation Errors**
- **Cycles Detected**: Check for circular connections between nodes
- **Orphaned Nodes**: Ensure all nodes are connected in the flow
- **Missing Sources/Sinks**: Add required event subscription and event sink nodes

#### **Execution Issues**
- **Pipeline Won't Start**: Verify validation passes and all nodes configured
- **High Error Rates**: Check node configurations and error handling
- **Performance Issues**: Monitor metrics and adjust batch sizes/timeouts

#### **Configuration Problems**
- **Invalid Settings**: Review node configuration requirements
- **Connection Issues**: Verify network connectivity for external services
- **Authentication**: Check credentials and permissions for external systems

### **Debugging Tips**

1. **Use Console Sink**: Add console output for debugging
2. **Check Logs**: Review application logs for error details
3. **Test Incrementally**: Test individual nodes before full pipeline
4. **Monitor Metrics**: Watch real-time metrics for performance issues

## Future Enhancements

### **Planned Features**
- **Pipeline Versioning**: Version control for pipeline configurations
- **A/B Testing**: Compare different pipeline configurations
- **Advanced Analytics**: Detailed performance and error analytics
- **Template Marketplace**: Community-shared pipeline templates
- **CI/CD Integration**: Automated pipeline deployment

### **Integration Opportunities**
- **Kubernetes**: Native Kubernetes deployment
- **Monitoring**: Integration with Prometheus, Grafana
- **Alerting**: Automated alerting on pipeline failures
- **Backup/Restore**: Pipeline configuration backup and recovery

## Related Resources

- [Event Subscriptions Documentation](event-subscriptions.md)
- [Event Processors Documentation](event-processors.md)
- [Event Framework Documentation](event-framework.md)
- [Vector Pipeline Design Inspiration](https://vector.dev/docs/architecture/pipeline-model/)

---

*This documentation covers the DAG-based Event Pipeline Builder, which uses our Event Management System to provide a visual, Vector-inspired interface for building event processing pipelines with real-time validation and execution control.*
