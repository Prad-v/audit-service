"""
API endpoints for StackStorm synthetic test management
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...models.test_models import (
    StackStormTest, TestExecution, TestSuite, TestStatus, TestType,
    StackStormAction, StackStormWorkflow, StackStormRule, StackStormPack
)
from ...models.database_models import StackStormTestDB, TestExecutionDB
from ...services.test_executor import StackStormTestExecutor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tests", tags=["stackstorm-tests"])


@router.post("/", response_model=StackStormTest)
async def create_test(
    test: StackStormTest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new StackStorm synthetic test"""
    try:
        # Validate test structure
        if not test.name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Test name is required"
            )
        
        if not test.test_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Test code is required"
            )
        
        # Set timestamps
        test.created_at = datetime.now(timezone.utc)
        test.updated_at = datetime.now(timezone.utc)
        
        # TODO: Save to database
        # For now, just return the test
        logger.info(f"Created StackStorm synthetic test: {test.name}")
        return test
        
    except Exception as e:
        logger.error(f"Failed to create test: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create test: {str(e)}"
        )


@router.get("/", response_model=List[StackStormTest])
async def list_tests(
    skip: int = 0,
    limit: int = 100,
    enabled_only: bool = True,
    test_type: Optional[TestType] = None,
    db: AsyncSession = Depends(get_db)
):
    """List StackStorm synthetic tests"""
    try:
        from sqlalchemy import select
        
        # Build query
        query = select(StackStormTestDB)
        
        # Apply filters
        if enabled_only:
            query = query.where(StackStormTestDB.enabled == True)
        
        if test_type:
            query = query.where(StackStormTestDB.test_type == test_type)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        tests = result.scalars().all()
        
        return tests
        
    except Exception as e:
        logger.error(f"Failed to list tests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tests: {str(e)}"
        )


@router.get("/{test_id}", response_model=StackStormTest)
async def get_test(
    test_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific StackStorm synthetic test"""
    try:
        # TODO: Implement database query
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get test: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get test: {str(e)}"
        )


@router.put("/{test_id}", response_model=StackStormTest)
async def update_test(
    test_id: str,
    test: StackStormTest,
    db: AsyncSession = Depends(get_db)
):
    """Update a StackStorm synthetic test"""
    try:
        # TODO: Implement database update
        test.updated_at = datetime.now(timezone.utc)
        return test
        
    except Exception as e:
        logger.error(f"Failed to update test: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update test: {str(e)}"
        )


@router.delete("/{test_id}")
async def delete_test(
    test_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a StackStorm synthetic test"""
    try:
        # TODO: Implement database deletion and StackStorm cleanup
        return {"message": "Test deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete test: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete test: {str(e)}"
        )


@router.post("/{test_id}/deploy")
async def deploy_test(
    test_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Deploy a test to StackStorm"""
    try:
        from sqlalchemy import select
        
        # Get test from database
        result = await db.execute(select(StackStormTestDB).where(StackStormTestDB.test_id == test_id))
        test = result.scalar_one_or_none()
        
        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test {test_id} not found"
            )
        
        # Deploy test
        executor = StackStormTestExecutor()
        success = await executor.deploy_test(test)
        
        if success:
            # Update test status in database
            test.deployed = True
            test.updated_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(test)
            
            return {"message": "Test deployed successfully to StackStorm"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to deploy test to StackStorm"
            )
        
    except Exception as e:
        logger.error(f"Failed to deploy test: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deploy test: {str(e)}"
        )


@router.post("/{test_id}/execute", response_model=TestExecution)
async def execute_test(
    test_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Execute a StackStorm synthetic test"""
    try:
        from sqlalchemy import select
        
        # Get test from database
        result = await db.execute(select(StackStormTestDB).where(StackStormTestDB.test_id == test_id))
        test = result.scalar_one_or_none()
        
        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test {test_id} not found"
            )
        
        # Execute test
        executor = StackStormTestExecutor()
        execution = await executor.execute_test(test)
        
        # Save execution to database
        db.add(execution)
        await db.commit()
        await db.refresh(execution)
        
        logger.info(f"Executed test {test_id}: {execution.status}")
        return execution
        
    except Exception as e:
        logger.error(f"Failed to execute test: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute test: {str(e)}"
        )


@router.get("/executions/", response_model=List[TestExecution])
async def list_executions(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """List all test executions"""
    try:
        from sqlalchemy import select
        
        query = select(TestExecutionDB).offset(skip).limit(limit).order_by(TestExecutionDB.started_at.desc())
        result = await db.execute(query)
        executions = result.scalars().all()
        
        return executions
        
    except Exception as e:
        logger.error(f"Failed to list executions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list executions: {str(e)}"
        )


@router.get("/{test_id}/executions", response_model=List[TestExecution])
async def list_test_executions(
    test_id: str,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """List executions for a specific test"""
    try:
        from sqlalchemy import select
        
        query = select(TestExecutionDB).where(TestExecutionDB.test_id == test_id).offset(skip).limit(limit).order_by(TestExecutionDB.started_at.desc())
        result = await db.execute(query)
        executions = result.scalars().all()
        
        return executions
        
    except Exception as e:
        logger.error(f"Failed to list test executions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list test executions: {str(e)}"
        )


@router.get("/executions/{execution_id}", response_model=TestExecution)
async def get_test_execution(
    execution_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific test execution"""
    try:
        # TODO: Implement database query
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test execution not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get test execution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get test execution: {str(e)}"
        )


@router.post("/suites/", response_model=TestSuite)
async def create_test_suite(
    suite: TestSuite,
    db: AsyncSession = Depends(get_db)
):
    """Create a new test suite"""
    try:
        suite.created_at = datetime.now(timezone.utc)
        suite.updated_at = datetime.now(timezone.utc)
        
        # TODO: Save to database
        logger.info(f"Created test suite: {suite.name}")
        return suite
        
    except Exception as e:
        logger.error(f"Failed to create test suite: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create test suite: {str(e)}"
        )


@router.get("/suites/", response_model=List[TestSuite])
async def list_test_suites(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List test suites"""
    try:
        # TODO: Implement database query
        return []
        
    except Exception as e:
        logger.error(f"Failed to list test suites: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list test suites: {str(e)}"
        )


@router.post("/suites/{suite_id}/execute")
async def execute_test_suite(
    suite_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Execute all tests in a suite"""
    try:
        # TODO: Get suite from database and execute all tests
        return {"message": f"Test suite {suite_id} execution started"}
        
    except Exception as e:
        logger.error(f"Failed to execute test suite: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute test suite: {str(e)}"
        )


# StackStorm integration endpoints
@router.get("/stackstorm/status")
async def get_stackstorm_status():
    """Get StackStorm connection status"""
    try:
        executor = StackStormTestExecutor()
        success = await executor.stackstorm_client.authenticate()
        
        return {
            "connected": success,
            "api_url": executor.stackstorm_client.api_url,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to check StackStorm status: {e}")
        return {
            "connected": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.get("/stackstorm/executions")
async def list_stackstorm_executions(
    limit: int = 50,
    status: Optional[str] = None
):
    """List StackStorm executions"""
    try:
        executor = StackStormTestExecutor()
        if not await executor.stackstorm_client.authenticate():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cannot connect to StackStorm"
            )
        
        executions = await executor.stackstorm_client.list_executions(limit, status)
        return {"executions": executions}
        
    except Exception as e:
        logger.error(f"Failed to list StackStorm executions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list StackStorm executions: {str(e)}"
        )


@router.get("/stackstorm/executions/{execution_id}")
async def get_stackstorm_execution(execution_id: str):
    """Get StackStorm execution details"""
    try:
        executor = StackStormTestExecutor()
        if not await executor.stackstorm_client.authenticate():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cannot connect to StackStorm"
            )
        
        execution = await executor.stackstorm_client.get_execution(execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution not found"
            )
        
        return execution
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get StackStorm execution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get StackStorm execution: {str(e)}"
        )


@router.post("/examples/nats")
async def create_nats_example_tests(db: AsyncSession = Depends(get_db)):
    """Create example NATS tests (positive and negative)"""
    try:
        from ...services.nats_test_examples import (
            NATS_POSITIVE_TEST_CONFIG, 
            NATS_NEGATIVE_TEST_CONFIG
        )
        
        # Create positive test
        positive_test = StackStormTestDB(
            test_id=f"nats_positive_{int(datetime.now().timestamp())}",
            name=NATS_POSITIVE_TEST_CONFIG["name"],
            description=NATS_POSITIVE_TEST_CONFIG["description"],
            test_type=NATS_POSITIVE_TEST_CONFIG["test_type"],
            stackstorm_pack=NATS_POSITIVE_TEST_CONFIG["stackstorm_pack"],
            test_code=NATS_POSITIVE_TEST_CONFIG["test_code"],
            test_parameters=NATS_POSITIVE_TEST_CONFIG["test_parameters"],
            expected_result=NATS_POSITIVE_TEST_CONFIG["expected_result"],
            timeout=NATS_POSITIVE_TEST_CONFIG["timeout"],
            tags=NATS_POSITIVE_TEST_CONFIG["tags"],
            enabled=NATS_POSITIVE_TEST_CONFIG["enabled"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Create negative test
        negative_test = StackStormTestDB(
            test_id=f"nats_negative_{int(datetime.now().timestamp())}",
            name=NATS_NEGATIVE_TEST_CONFIG["name"],
            description=NATS_NEGATIVE_TEST_CONFIG["description"],
            test_type=NATS_NEGATIVE_TEST_CONFIG["test_type"],
            stackstorm_pack=NATS_NEGATIVE_TEST_CONFIG["stackstorm_pack"],
            test_code=NATS_NEGATIVE_TEST_CONFIG["test_code"],
            test_parameters=NATS_NEGATIVE_TEST_CONFIG["test_parameters"],
            expected_result=NATS_NEGATIVE_TEST_CONFIG["expected_result"],
            timeout=NATS_NEGATIVE_TEST_CONFIG["timeout"],
            tags=NATS_NEGATIVE_TEST_CONFIG["tags"],
            enabled=NATS_NEGATIVE_TEST_CONFIG["enabled"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Save to database
        db.add(positive_test)
        db.add(negative_test)
        await db.commit()
        await db.refresh(positive_test)
        await db.refresh(negative_test)
        
        return {
            "message": "NATS example tests created successfully",
            "tests": [
                {
                    "test_id": positive_test.test_id,
                    "name": positive_test.name,
                    "description": positive_test.description,
                    "type": positive_test.test_type,
                    "tags": positive_test.tags
                },
                {
                    "test_id": negative_test.test_id,
                    "name": negative_test.name,
                    "description": negative_test.description,
                    "type": negative_test.test_type,
                    "tags": negative_test.tags
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to create NATS example tests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create NATS example tests: {str(e)}"
        )


@router.get("/examples/nats/positive")
async def get_nats_positive_test():
    """Get NATS positive test template"""
    try:
        from ...services.nats_test_examples import NATS_POSITIVE_TEST_CONFIG
        
        return {
            "test_config": NATS_POSITIVE_TEST_CONFIG,
            "instructions": {
                "description": "This test validates NATS message publishing and receiving",
                "what_it_tests": [
                    "NATS connection and messaging",
                    "Message publishing to a subject",
                    "Message subscription and receiving",
                    "Field validation in received messages",
                    "Nested data structure validation"
                ],
                "expected_behavior": "Test should pass when messages are properly sent and received with correct field validation",
                "failure_scenarios": [
                    "NATS connection failure",
                    "Message not received",
                    "Missing required fields in received message",
                    "Invalid data structure"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get NATS positive test: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get NATS positive test: {str(e)}"
        )


@router.get("/examples/nats/negative")
async def get_nats_negative_test():
    """Get NATS negative test template"""
    try:
        from ...services.nats_test_examples import NATS_NEGATIVE_TEST_CONFIG
        
        return {
            "test_config": NATS_NEGATIVE_TEST_CONFIG,
            "instructions": {
                "description": "This test validates NATS error handling and edge cases",
                "what_it_tests": [
                    "Invalid JSON message handling",
                    "Missing required fields detection",
                    "Connection timeout scenarios",
                    "Error handling and recovery"
                ],
                "expected_behavior": "Test should pass when all error scenarios are properly handled",
                "failure_scenarios": [
                    "Unexpected successful connection to invalid endpoint",
                    "Missing fields not detected",
                    "Invalid JSON not handled properly"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get NATS negative test: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get NATS negative test: {str(e)}"
        )
