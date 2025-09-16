"""
SQLAlchemy database models for StackStorm Synthetic Test Framework
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


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


class StackStormTestDB(Base):
    """SQLAlchemy model for StackStorm test definition"""
    __tablename__ = "stackstorm_tests"
    
    test_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text)
    test_type = Column(String, nullable=False)
    stackstorm_pack = Column(String, default="synthetic_tests")
    stackstorm_action = Column(String)
    stackstorm_workflow = Column(String)
    stackstorm_rule = Column(String)
    stackstorm_sensor = Column(String)
    
    # Test content
    test_code = Column(Text, nullable=False)
    test_parameters = Column(JSON, default=dict)
    expected_result = Column(JSON)
    
    # Configuration
    timeout = Column(Integer, default=300)
    retry_count = Column(Integer, default=0)
    retry_delay = Column(Integer, default=5)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_by = Column(String)
    tags = Column(JSON, default=list)
    enabled = Column(Boolean, default=True)
    
    # StackStorm integration
    stackstorm_execution_id = Column(String)
    stackstorm_pack_version = Column(String)
    deployed = Column(Boolean, default=False)


class TestExecutionDB(Base):
    """SQLAlchemy model for test execution"""
    __tablename__ = "test_executions"
    
    execution_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    test_id = Column(String, nullable=False)
    stackstorm_execution_id = Column(String)
    status = Column(String, default="pending")
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    error_message = Column(Text)
    output_data = Column(JSON, default=dict)
    created_incident_id = Column(String)
    execution_context = Column(JSON, default=dict)
    node_results = Column(JSON, default=dict)  # For compatibility with frontend
