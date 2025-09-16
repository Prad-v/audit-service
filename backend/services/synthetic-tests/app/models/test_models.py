"""
Synthetic Test Framework Models

This module defines the data models for the synthetic test framework,
including DAG nodes, test definitions, and execution results.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class NodeType(str, Enum):
    """Types of nodes that can be used in synthetic tests"""
    PUBSUB_PUBLISHER = "pubsub_publisher"
    PUBSUB_SUBSCRIBER = "pubsub_subscriber"
    REST_CLIENT = "rest_client"
    WEBHOOK_RECEIVER = "webhook_receiver"
    ATTRIBUTE_COMPARATOR = "attribute_comparator"
    INCIDENT_CREATOR = "incident_creator"
    DELAY = "delay"
    CONDITION = "condition"


class TestStatus(str, Enum):
    """Status of test execution"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ComparisonOperator(str, Enum):
    """Operators for attribute comparison"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    REGEX_MATCH = "regex_match"


class NodeConfig(BaseModel):
    """Base configuration for a DAG node"""
    node_id: str = Field(default_factory=lambda: str(uuid4()))
    node_type: NodeType
    name: str
    description: Optional[str] = None
    position: Dict[str, float] = Field(default_factory=lambda: {"x": 0, "y": 0})
    config: Dict[str, Any] = Field(default_factory=dict)


class PubSubPublisherConfig(NodeConfig):
    """Configuration for Pub/Sub publisher node"""
    node_type: NodeType = NodeType.PUBSUB_PUBLISHER
    project_id: str
    topic_name: str
    message_data: str
    attributes: Dict[str, str] = Field(default_factory=dict)
    ordering_key: Optional[str] = None


class PubSubSubscriberConfig(NodeConfig):
    """Configuration for Pub/Sub subscriber node"""
    node_type: NodeType = NodeType.PUBSUB_SUBSCRIBER
    project_id: str
    subscription_name: str
    timeout_seconds: int = 30
    expected_attributes: Dict[str, str] = Field(default_factory=dict)


class RestClientConfig(NodeConfig):
    """Configuration for REST client node"""
    node_type: NodeType = NodeType.REST_CLIENT
    url: str
    method: str = "POST"
    headers: Dict[str, str] = Field(default_factory=dict)
    body: Optional[str] = None
    timeout_seconds: int = 30
    expected_status_codes: List[int] = Field(default_factory=lambda: [200, 201, 202])


class WebhookReceiverConfig(NodeConfig):
    """Configuration for webhook receiver node"""
    node_type: NodeType = NodeType.WEBHOOK_RECEIVER
    webhook_url: str
    expected_headers: Dict[str, str] = Field(default_factory=dict)
    expected_body_schema: Optional[Dict[str, Any]] = None
    timeout_seconds: int = 30


class AttributeComparatorConfig(NodeConfig):
    """Configuration for attribute comparison node"""
    node_type: NodeType = NodeType.ATTRIBUTE_COMPARATOR
    source_node_id: str
    target_node_id: str
    comparisons: List[Dict[str, Any]] = Field(default_factory=list)
    # Each comparison: {"attribute": "key", "operator": "equals", "expected_value": "value"}


class IncidentCreatorConfig(NodeConfig):
    """Configuration for incident creation node"""
    node_type: NodeType = NodeType.INCIDENT_CREATOR
    incident_title_template: str = "Synthetic Test Failed: {test_name}"
    incident_description_template: str = "Test failed with error: {error_message}"
    severity: str = "medium"
    auto_create: bool = True


class DelayConfig(NodeConfig):
    """Configuration for delay node"""
    node_type: NodeType = NodeType.DELAY
    delay_seconds: int = 1


class ConditionConfig(NodeConfig):
    """Configuration for conditional node"""
    node_type: NodeType = NodeType.CONDITION
    condition_expression: str  # JavaScript-like expression
    true_node_id: Optional[str] = None
    false_node_id: Optional[str] = None


class DAGEdge(BaseModel):
    """Represents a connection between two nodes in the DAG"""
    source_node_id: str
    target_node_id: str
    condition: Optional[str] = None  # Optional condition for the edge


class SyntheticTest(BaseModel):
    """Complete synthetic test definition"""
    test_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    nodes: List[Union[
        PubSubPublisherConfig,
        PubSubSubscriberConfig,
        RestClientConfig,
        WebhookReceiverConfig,
        AttributeComparatorConfig,
        IncidentCreatorConfig,
        DelayConfig,
        ConditionConfig
    ]] = Field(default_factory=list)
    edges: List[DAGEdge] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    enabled: bool = True
    schedule: Optional[str] = None  # Cron expression for scheduled execution


class TestExecution(BaseModel):
    """Represents a single execution of a synthetic test"""
    execution_id: str = Field(default_factory=lambda: str(uuid4()))
    test_id: str
    status: TestStatus = TestStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    node_results: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    created_incident_id: Optional[str] = None
    execution_context: Dict[str, Any] = Field(default_factory=dict)


class TestResult(BaseModel):
    """Result of a node execution"""
    node_id: str
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    output_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)


class TestSuite(BaseModel):
    """Collection of related synthetic tests"""
    suite_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    test_ids: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    enabled: bool = True
