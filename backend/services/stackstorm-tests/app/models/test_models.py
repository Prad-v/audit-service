"""
StackStorm Synthetic Test Framework Models

This module defines the data models for the StackStorm-based synthetic test framework.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class TestStatus(str, Enum):
    """Status of test execution"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class TestType(str, Enum):
    """Types of StackStorm tests"""
    WORKFLOW = "workflow"
    ACTION = "action"
    RULE = "rule"
    SENSOR = "sensor"


class StackStormTest(BaseModel):
    """StackStorm test definition"""
    test_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    test_type: TestType
    stackstorm_pack: str = "synthetic_tests"
    stackstorm_action: Optional[str] = None
    stackstorm_workflow: Optional[str] = None
    stackstorm_rule: Optional[str] = None
    stackstorm_sensor: Optional[str] = None
    
    # Test content
    test_code: str  # YAML or Python code
    test_parameters: Dict[str, Any] = Field(default_factory=dict)
    expected_result: Optional[Dict[str, Any]] = None
    
    # Configuration
    timeout: int = 300  # seconds
    retry_count: int = 0
    retry_delay: int = 5  # seconds
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    enabled: bool = True
    
    # StackStorm integration
    stackstorm_execution_id: Optional[str] = None
    stackstorm_pack_version: Optional[str] = None
    deployed: bool = False


class TestExecution(BaseModel):
    """Represents a single execution of a StackStorm test"""
    execution_id: str = Field(default_factory=lambda: str(uuid4()))
    test_id: str
    stackstorm_execution_id: Optional[str] = None
    status: TestStatus = TestStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    output_data: Dict[str, Any] = Field(default_factory=dict)
    created_incident_id: Optional[str] = None
    execution_context: Dict[str, Any] = Field(default_factory=dict)


class StackStormPack(BaseModel):
    """StackStorm pack definition for synthetic tests"""
    name: str = "synthetic_tests"
    description: str = "Synthetic tests for monitoring and validation"
    version: str = "1.0.0"
    author: str = "Synthetic Test Framework"
    email: str = "admin@example.com"
    keywords: List[str] = Field(default_factory=lambda: ["synthetic", "testing", "monitoring"])
    python_versions: List[str] = Field(default_factory=lambda: ["3.6", "3.7", "3.8", "3.9", "3.10", "3.11"])
    dependencies: Dict[str, str] = Field(default_factory=dict)
    config_schema: Dict[str, Any] = Field(default_factory=dict)


class StackStormAction(BaseModel):
    """StackStorm action definition"""
    name: str
    description: str
    runner_type: str = "python-script"  # or "action-chain", "mistral-v2", etc.
    entry_point: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    enabled: bool = True


class StackStormWorkflow(BaseModel):
    """StackStorm workflow definition"""
    name: str
    description: str
    runner_type: str = "action-chain"  # or "mistral-v2", "orquesta"
    entry_point: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    enabled: bool = True


class StackStormRule(BaseModel):
    """StackStorm rule definition"""
    name: str
    description: str
    trigger: Dict[str, Any]
    criteria: Dict[str, Any]
    action: Dict[str, Any]
    enabled: bool = True
    tags: List[str] = Field(default_factory=list)


class TestSuite(BaseModel):
    """Collection of related StackStorm tests"""
    suite_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    test_ids: List[str] = Field(default_factory=list)
    stackstorm_pack: str = "synthetic_tests"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    enabled: bool = True
    schedule: Optional[str] = None  # Cron expression


class StackStormConfig(BaseModel):
    """StackStorm configuration"""
    api_url: str = "http://stackstorm:9101"
    auth_url: str = "http://stackstorm:9100"
    username: str = "st2admin"
    password: str = "st2admin"
    api_key: Optional[str] = None
    verify_ssl: bool = False
    timeout: int = 30
