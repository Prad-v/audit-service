"""
DAG Execution Engine for Synthetic Tests

This module provides the core execution engine for running synthetic tests
defined as Directed Acyclic Graphs (DAGs).
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum

from ..models.test_models import (
    SyntheticTest, TestExecution, TestResult, TestStatus, NodeType,
    PubSubPublisherConfig, PubSubSubscriberConfig, RestClientConfig,
    WebhookReceiverConfig, AttributeComparatorConfig, IncidentCreatorConfig,
    DelayConfig, ConditionConfig
)
from .pubsub_service import PubSubService
from .rest_client_service import RestClientService
from .webhook_service import WebhookService
from .incident_service import IncidentService

logger = logging.getLogger(__name__)


class ExecutionState(Enum):
    """State of DAG execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class NodeExecutionContext:
    """Context for executing a single node"""
    node_id: str
    node_config: Any
    input_data: Dict[str, Any]
    execution_id: str
    test_id: str


class DAGExecutor:
    """Executes synthetic tests defined as DAGs"""
    
    def __init__(self):
        self.pubsub_service = PubSubService()
        self.rest_client_service = RestClientService()
        self.webhook_service = WebhookService()
        self.incident_service = IncidentService()
        self._running_executions: Dict[str, asyncio.Task] = {}
    
    async def execute_test(self, test: SyntheticTest) -> TestExecution:
        """Execute a synthetic test DAG"""
        execution = TestExecution(
            test_id=test.test_id,
            status=TestStatus.PENDING,
            started_at=datetime.now(timezone.utc)
        )
        
        try:
            execution.status = TestStatus.RUNNING
            
            # Validate DAG structure
            if not self._validate_dag(test):
                raise ValueError("Invalid DAG structure")
            
            # Execute DAG
            node_results = await self._execute_dag(test, execution.execution_id)
            execution.node_results = node_results
            
            # Determine overall test status
            execution.status = self._determine_test_status(node_results)
            
            # Create incident if test failed
            if execution.status == TestStatus.FAILED:
                incident_id = await self._create_incident_on_failure(test, execution)
                execution.created_incident_id = incident_id
            
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            execution.status = TestStatus.FAILED
            execution.error_message = str(e)
        
        finally:
            execution.completed_at = datetime.now(timezone.utc)
        
        return execution
    
    def _validate_dag(self, test: SyntheticTest) -> bool:
        """Validate that the DAG structure is correct"""
        # Check for cycles
        if self._has_cycles(test):
            return False
        
        # Check that all referenced nodes exist
        node_ids = {node.node_id for node in test.nodes}
        for edge in test.edges:
            if edge.source_node_id not in node_ids or edge.target_node_id not in node_ids:
                return False
        
        return True
    
    def _has_cycles(self, test: SyntheticTest) -> bool:
        """Check if the DAG has cycles using DFS"""
        # Build adjacency list
        graph = {node.node_id: [] for node in test.nodes}
        for edge in test.edges:
            graph[edge.source_node_id].append(edge.target_node_id)
        
        # DFS to detect cycles
        visited = set()
        rec_stack = set()
        
        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for neighbor in graph[node_id]:
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node_id in graph:
            if node_id not in visited:
                if dfs(node_id):
                    return True
        
        return False
    
    async def _execute_dag(self, test: SyntheticTest, execution_id: str) -> Dict[str, Dict[str, Any]]:
        """Execute the DAG nodes in topological order"""
        # Build adjacency list and in-degree count
        graph = {node.node_id: [] for node in test.nodes}
        in_degree = {node.node_id: 0 for node in test.nodes}
        
        for edge in test.edges:
            graph[edge.source_node_id].append(edge.target_node_id)
            in_degree[edge.target_node_id] += 1
        
        # Find starting nodes (nodes with no incoming edges)
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        node_results = {}
        execution_context = {}
        
        while queue:
            # Execute nodes in parallel that have no dependencies
            current_batch = []
            for node_id in queue:
                node_config = next(node.node_config for node in test.nodes if node.node_id == node_id)
                context = NodeExecutionContext(
                    node_id=node_id,
                    node_config=node_config,
                    input_data=execution_context.get(node_id, {}),
                    execution_id=execution_id,
                    test_id=test.test_id
                )
                current_batch.append(self._execute_node(context))
            
            # Wait for current batch to complete
            batch_results = await asyncio.gather(*current_batch, return_exceptions=True)
            
            # Process results and update queue
            new_queue = []
            for i, result in enumerate(batch_results):
                node_id = queue[i]
                if isinstance(result, Exception):
                    logger.error(f"Node {node_id} failed: {result}")
                    node_results[node_id] = {
                        "status": TestStatus.FAILED,
                        "error": str(result),
                        "output_data": {}
                    }
                else:
                    node_results[node_id] = result
                    execution_context[node_id] = result.get("output_data", {})
                
                # Add dependent nodes to queue if their dependencies are satisfied
                for dependent_node in graph[node_id]:
                    in_degree[dependent_node] -= 1
                    if in_degree[dependent_node] == 0:
                        new_queue.append(dependent_node)
            
            queue = new_queue
        
        return node_results
    
    async def _execute_node(self, context: NodeExecutionContext) -> Dict[str, Any]:
        """Execute a single node based on its type"""
        start_time = datetime.now(timezone.utc)
        
        try:
            if context.node_config.node_type == NodeType.PUBSUB_PUBLISHER:
                result = await self._execute_pubsub_publisher(context)
            elif context.node_config.node_type == NodeType.PUBSUB_SUBSCRIBER:
                result = await self._execute_pubsub_subscriber(context)
            elif context.node_config.node_type == NodeType.REST_CLIENT:
                result = await self._execute_rest_client(context)
            elif context.node_config.node_type == NodeType.WEBHOOK_RECEIVER:
                result = await self._execute_webhook_receiver(context)
            elif context.node_config.node_type == NodeType.ATTRIBUTE_COMPARATOR:
                result = await self._execute_attribute_comparator(context)
            elif context.node_config.node_type == NodeType.INCIDENT_CREATOR:
                result = await self._execute_incident_creator(context)
            elif context.node_config.node_type == NodeType.DELAY:
                result = await self._execute_delay(context)
            elif context.node_config.node_type == NodeType.CONDITION:
                result = await self._execute_condition(context)
            else:
                raise ValueError(f"Unknown node type: {context.node_config.node_type}")
            
            result.update({
                "start_time": start_time.isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
                "status": TestStatus.PASSED
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Node execution failed: {e}")
            return {
                "start_time": start_time.isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
                "status": TestStatus.FAILED,
                "error": str(e),
                "output_data": {}
            }
    
    async def _execute_pubsub_publisher(self, context: NodeExecutionContext) -> Dict[str, Any]:
        """Execute Pub/Sub publisher node"""
        config = context.node_config
        message_id = await self.pubsub_service.publish_message(
            project_id=config.project_id,
            topic_name=config.topic_name,
            message_data=config.message_data,
            attributes=config.attributes,
            ordering_key=config.ordering_key
        )
        
        return {
            "output_data": {
                "message_id": message_id,
                "published_at": datetime.now(timezone.utc).isoformat()
            }
        }
    
    async def _execute_pubsub_subscriber(self, context: NodeExecutionContext) -> Dict[str, Any]:
        """Execute Pub/Sub subscriber node"""
        config = context.node_config
        message = await self.pubsub_service.receive_message(
            project_id=config.project_id,
            subscription_name=config.subscription_name,
            timeout_seconds=config.timeout_seconds
        )
        
        if not message:
            raise Exception("No message received within timeout")
        
        # Validate expected attributes
        for attr_key, expected_value in config.expected_attributes.items():
            if attr_key not in message.attributes:
                raise Exception(f"Missing expected attribute: {attr_key}")
            if message.attributes[attr_key] != expected_value:
                raise Exception(f"Attribute {attr_key} mismatch: expected {expected_value}, got {message.attributes[attr_key]}")
        
        return {
            "output_data": {
                "message_id": message.message_id,
                "data": message.data,
                "attributes": message.attributes,
                "received_at": datetime.now(timezone.utc).isoformat()
            }
        }
    
    async def _execute_rest_client(self, context: NodeExecutionContext) -> Dict[str, Any]:
        """Execute REST client node"""
        config = context.node_config
        response = await self.rest_client_service.make_request(
            url=config.url,
            method=config.method,
            headers=config.headers,
            body=config.body,
            timeout_seconds=config.timeout_seconds
        )
        
        if response.status_code not in config.expected_status_codes:
            raise Exception(f"Unexpected status code: {response.status_code}")
        
        return {
            "output_data": {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text,
                "requested_at": datetime.now(timezone.utc).isoformat()
            }
        }
    
    async def _execute_webhook_receiver(self, context: NodeExecutionContext) -> Dict[str, Any]:
        """Execute webhook receiver node"""
        config = context.node_config
        webhook_data = await self.webhook_service.wait_for_webhook(
            webhook_url=config.webhook_url,
            expected_headers=config.expected_headers,
            expected_body_schema=config.expected_body_schema,
            timeout_seconds=config.timeout_seconds
        )
        
        return {
            "output_data": {
                "webhook_data": webhook_data,
                "received_at": datetime.now(timezone.utc).isoformat()
            }
        }
    
    async def _execute_attribute_comparator(self, context: NodeExecutionContext) -> Dict[str, Any]:
        """Execute attribute comparison node"""
        config = context.node_config
        
        # Get data from source and target nodes
        source_data = context.input_data.get(config.source_node_id, {})
        target_data = context.input_data.get(config.target_node_id, {})
        
        comparison_results = []
        all_passed = True
        
        for comparison in config.comparisons:
            attr_key = comparison["attribute"]
            operator = comparison["operator"]
            expected_value = comparison["expected_value"]
            
            source_value = source_data.get(attr_key)
            target_value = target_data.get(attr_key)
            
            passed = self._compare_values(source_value, target_value, operator, expected_value)
            comparison_results.append({
                "attribute": attr_key,
                "operator": operator,
                "expected_value": expected_value,
                "source_value": source_value,
                "target_value": target_value,
                "passed": passed
            })
            
            if not passed:
                all_passed = False
        
        if not all_passed:
            raise Exception(f"Attribute comparison failed: {comparison_results}")
        
        return {
            "output_data": {
                "comparison_results": comparison_results,
                "all_passed": all_passed,
                "compared_at": datetime.now(timezone.utc).isoformat()
            }
        }
    
    def _compare_values(self, source_value: Any, target_value: Any, operator: str, expected_value: Any) -> bool:
        """Compare two values using the specified operator"""
        if operator == "equals":
            return source_value == expected_value and target_value == expected_value
        elif operator == "not_equals":
            return source_value != expected_value and target_value != expected_value
        elif operator == "contains":
            return expected_value in str(source_value) and expected_value in str(target_value)
        elif operator == "not_contains":
            return expected_value not in str(source_value) and expected_value not in str(target_value)
        elif operator == "greater_than":
            return source_value > expected_value and target_value > expected_value
        elif operator == "less_than":
            return source_value < expected_value and target_value < expected_value
        elif operator == "regex_match":
            import re
            pattern = re.compile(expected_value)
            return bool(pattern.match(str(source_value))) and bool(pattern.match(str(target_value)))
        else:
            raise ValueError(f"Unknown comparison operator: {operator}")
    
    async def _execute_incident_creator(self, context: NodeExecutionContext) -> Dict[str, Any]:
        """Execute incident creation node"""
        config = context.node_config
        
        if not config.auto_create:
            return {"output_data": {"incident_created": False}}
        
        incident_data = {
            "title": config.incident_title_template.format(
                test_name=context.test_id,
                error_message=context.input_data.get("error_message", "Unknown error")
            ),
            "description": config.incident_description_template.format(
                test_name=context.test_id,
                error_message=context.input_data.get("error_message", "Unknown error")
            ),
            "severity": config.severity,
            "incident_type": "synthetic_test_failure"
        }
        
        incident_id = await self.incident_service.create_incident(incident_data)
        
        return {
            "output_data": {
                "incident_id": incident_id,
                "incident_created": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        }
    
    async def _execute_delay(self, context: NodeExecutionContext) -> Dict[str, Any]:
        """Execute delay node"""
        config = context.node_config
        await asyncio.sleep(config.delay_seconds)
        
        return {
            "output_data": {
                "delay_seconds": config.delay_seconds,
                "delayed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    
    async def _execute_condition(self, context: NodeExecutionContext) -> Dict[str, Any]:
        """Execute conditional node"""
        config = context.node_config
        
        # Simple expression evaluation (in production, use a proper expression evaluator)
        # This is a simplified version - you might want to use a library like `simpleeval`
        try:
            # For now, just return the condition result
            # In a real implementation, you'd evaluate the expression
            condition_result = True  # Placeholder
            
            return {
                "output_data": {
                    "condition_result": condition_result,
                    "next_node_id": config.true_node_id if condition_result else config.false_node_id,
                    "evaluated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        except Exception as e:
            raise Exception(f"Condition evaluation failed: {e}")
    
    def _determine_test_status(self, node_results: Dict[str, Dict[str, Any]]) -> TestStatus:
        """Determine overall test status based on node results"""
        for result in node_results.values():
            if result.get("status") == TestStatus.FAILED:
                return TestStatus.FAILED
        
        return TestStatus.PASSED
    
    async def _create_incident_on_failure(self, test: SyntheticTest, execution: TestExecution) -> Optional[str]:
        """Create an incident when test fails"""
        try:
            incident_data = {
                "title": f"Synthetic Test Failed: {test.name}",
                "description": f"Test {test.test_id} failed with error: {execution.error_message}",
                "severity": "medium",
                "incident_type": "synthetic_test_failure",
                "affected_services": ["synthetic-testing"],
                "tags": ["synthetic-test", "automated"]
            }
            
            return await self.incident_service.create_incident(incident_data)
        except Exception as e:
            logger.error(f"Failed to create incident: {e}")
            return None
