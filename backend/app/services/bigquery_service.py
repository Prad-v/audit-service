"""
BigQuery service for cloud-based audit log storage.

This service provides BigQuery integration with fallback to PostgreSQL
for local development and hybrid cloud deployments.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

import structlog
from google.cloud import bigquery
from google.cloud.exceptions import NotFound, GoogleCloudError
from pydantic import BaseModel

from app.core.config import get_settings
from app.db.models import AuditLogCreate, AuditLogResponse
from app.services.audit_service import AuditService

logger = structlog.get_logger(__name__)

settings = get_settings()


class BigQueryConfig(BaseModel):
    """BigQuery configuration."""
    project_id: str
    dataset_id: str
    table_id: str
    location: str = "US"
    enable_streaming: bool = True
    batch_size: int = 1000
    max_retry_attempts: int = 3


class BigQueryService:
    """
    BigQuery service for audit log storage and querying.
    
    Provides high-performance audit log storage using BigQuery with
    automatic fallback to PostgreSQL for local development.
    """
    
    def __init__(
        self,
        config: Optional[BigQueryConfig] = None,
        fallback_service: Optional[AuditService] = None
    ):
        self.config = config or self._get_default_config()
        self.fallback_service = fallback_service
        self.client: Optional[bigquery.Client] = None
        self.table_ref: Optional[bigquery.TableReference] = None
        self._is_available = False
        
        # Initialize BigQuery client if configuration is available
        if self._should_use_bigquery():
            self._initialize_client()
    
    def _get_default_config(self) -> BigQueryConfig:
        """Get default BigQuery configuration from settings."""
        return BigQueryConfig(
            project_id=getattr(settings, 'gcp_project_id', ''),
            dataset_id=getattr(settings, 'bigquery_dataset_id', 'audit_logs'),
            table_id=getattr(settings, 'bigquery_table_id', 'audit_logs'),
            location=getattr(settings, 'bigquery_location', 'US'),
            enable_streaming=getattr(settings, 'bigquery_streaming', True),
            batch_size=getattr(settings, 'bigquery_batch_size', 1000),
            max_retry_attempts=getattr(settings, 'bigquery_retry_attempts', 3)
        )
    
    def _should_use_bigquery(self) -> bool:
        """Check if BigQuery should be used based on configuration."""
        return (
            bool(self.config.project_id) and
            settings.environment in ['staging', 'production'] and
            getattr(settings, 'use_bigquery', False)
        )
    
    def _initialize_client(self) -> None:
        """Initialize BigQuery client and table reference."""
        try:
            self.client = bigquery.Client(project=self.config.project_id)
            
            # Create table reference
            dataset_ref = self.client.dataset(self.config.dataset_id)
            self.table_ref = dataset_ref.table(self.config.table_id)
            
            # Verify table exists
            self._ensure_table_exists()
            self._is_available = True
            
            logger.info(
                "BigQuery client initialized",
                project_id=self.config.project_id,
                dataset_id=self.config.dataset_id,
                table_id=self.config.table_id
            )
            
        except Exception as e:
            logger.warning(
                "Failed to initialize BigQuery client",
                error=str(e),
                fallback_enabled=self.fallback_service is not None
            )
            self._is_available = False
    
    def _ensure_table_exists(self) -> None:
        """Ensure the BigQuery table exists with proper schema."""
        if not self.client or not self.table_ref:
            return
        
        try:
            # Try to get the table
            self.client.get_table(self.table_ref)
            logger.info("BigQuery table exists", table_id=self.config.table_id)
            
        except NotFound:
            # Create the table if it doesn't exist
            logger.info("Creating BigQuery table", table_id=self.config.table_id)
            self._create_table()
    
    def _create_table(self) -> None:
        """Create the BigQuery table with proper schema."""
        if not self.client or not self.table_ref:
            return
        
        # Define table schema
        schema = [
            bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("tenant_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("event_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("user_id", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("resource_id", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("action", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("metadata", "JSON", mode="NULLABLE"),
            bigquery.SchemaField("ip_address", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("user_agent", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("processed_at", "TIMESTAMP", mode="NULLABLE"),
        ]
        
        # Create table with partitioning and clustering
        table = bigquery.Table(self.table_ref, schema=schema)
        
        # Time partitioning by created_at
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="created_at",
            expiration_ms=7776000000  # 90 days
        )
        
        # Clustering for better query performance
        table.clustering_fields = ["tenant_id", "event_type"]
        
        # Create the table
        table = self.client.create_table(table)
        logger.info("BigQuery table created", table_id=table.table_id)
    
    async def create_audit_log(
        self,
        audit_data: AuditLogCreate,
        tenant_id: str,
        user_id: Optional[str] = None
    ) -> AuditLogResponse:
        """
        Create a single audit log entry.
        
        Args:
            audit_data: Audit log data
            tenant_id: Tenant identifier
            user_id: User identifier
            
        Returns:
            Created audit log response
        """
        if self._is_available and self.client:
            try:
                return await self._create_audit_log_bigquery(
                    audit_data, tenant_id, user_id
                )
            except Exception as e:
                logger.error(
                    "Failed to create audit log in BigQuery",
                    error=str(e),
                    tenant_id=tenant_id,
                    event_type=audit_data.event_type
                )
                
                # Fall back to PostgreSQL if available
                if self.fallback_service:
                    logger.info("Falling back to PostgreSQL")
                    return await self.fallback_service.create_audit_log(
                        audit_data, tenant_id, user_id
                    )
                raise
        
        # Use fallback service if BigQuery is not available
        if self.fallback_service:
            return await self.fallback_service.create_audit_log(
                audit_data, tenant_id, user_id
            )
        
        raise RuntimeError("No audit log storage backend available")
    
    async def _create_audit_log_bigquery(
        self,
        audit_data: AuditLogCreate,
        tenant_id: str,
        user_id: Optional[str] = None
    ) -> AuditLogResponse:
        """Create audit log in BigQuery."""
        import uuid
        
        # Generate unique ID
        log_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        # Prepare row data
        row_data = {
            "id": log_id,
            "tenant_id": tenant_id,
            "event_type": audit_data.event_type,
            "user_id": user_id or audit_data.user_id,
            "resource_id": audit_data.resource_id,
            "action": audit_data.action,
            "metadata": json.dumps(audit_data.metadata) if audit_data.metadata else None,
            "ip_address": audit_data.ip_address,
            "user_agent": audit_data.user_agent,
            "created_at": now.isoformat(),
            "processed_at": now.isoformat(),
        }
        
        # Insert row
        if self.config.enable_streaming:
            await self._stream_insert([row_data])
        else:
            await self._batch_insert([row_data])
        
        # Return response
        return AuditLogResponse(
            id=log_id,
            tenant_id=tenant_id,
            event_type=audit_data.event_type,
            user_id=user_id or audit_data.user_id,
            resource_id=audit_data.resource_id,
            action=audit_data.action,
            metadata=audit_data.metadata,
            ip_address=audit_data.ip_address,
            user_agent=audit_data.user_agent,
            created_at=now,
        )
    
    async def create_audit_logs_batch(
        self,
        audit_logs: List[AuditLogCreate],
        tenant_id: str,
        user_id: Optional[str] = None
    ) -> List[AuditLogResponse]:
        """
        Create multiple audit log entries in batch.
        
        Args:
            audit_logs: List of audit log data
            tenant_id: Tenant identifier
            user_id: User identifier
            
        Returns:
            List of created audit log responses
        """
        if self._is_available and self.client:
            try:
                return await self._create_audit_logs_batch_bigquery(
                    audit_logs, tenant_id, user_id
                )
            except Exception as e:
                logger.error(
                    "Failed to create audit logs batch in BigQuery",
                    error=str(e),
                    tenant_id=tenant_id,
                    batch_size=len(audit_logs)
                )
                
                # Fall back to PostgreSQL if available
                if self.fallback_service:
                    logger.info("Falling back to PostgreSQL for batch")
                    return await self.fallback_service.create_audit_logs_batch(
                        audit_logs, tenant_id, user_id
                    )
                raise
        
        # Use fallback service if BigQuery is not available
        if self.fallback_service:
            return await self.fallback_service.create_audit_logs_batch(
                audit_logs, tenant_id, user_id
            )
        
        raise RuntimeError("No audit log storage backend available")
    
    async def _create_audit_logs_batch_bigquery(
        self,
        audit_logs: List[AuditLogCreate],
        tenant_id: str,
        user_id: Optional[str] = None
    ) -> List[AuditLogResponse]:
        """Create audit logs batch in BigQuery."""
        import uuid
        
        now = datetime.now(timezone.utc)
        responses = []
        rows_data = []
        
        # Prepare batch data
        for audit_data in audit_logs:
            log_id = str(uuid.uuid4())
            
            row_data = {
                "id": log_id,
                "tenant_id": tenant_id,
                "event_type": audit_data.event_type,
                "user_id": user_id or audit_data.user_id,
                "resource_id": audit_data.resource_id,
                "action": audit_data.action,
                "metadata": json.dumps(audit_data.metadata) if audit_data.metadata else None,
                "ip_address": audit_data.ip_address,
                "user_agent": audit_data.user_agent,
                "created_at": now.isoformat(),
                "processed_at": now.isoformat(),
            }
            
            rows_data.append(row_data)
            
            responses.append(AuditLogResponse(
                id=log_id,
                tenant_id=tenant_id,
                event_type=audit_data.event_type,
                user_id=user_id or audit_data.user_id,
                resource_id=audit_data.resource_id,
                action=audit_data.action,
                metadata=audit_data.metadata,
                ip_address=audit_data.ip_address,
                user_agent=audit_data.user_agent,
                created_at=now,
            ))
        
        # Insert batch
        if self.config.enable_streaming:
            await self._stream_insert(rows_data)
        else:
            await self._batch_insert(rows_data)
        
        return responses
    
    async def _stream_insert(self, rows_data: List[Dict[str, Any]]) -> None:
        """Insert rows using streaming API."""
        if not self.client or not self.table_ref:
            raise RuntimeError("BigQuery client not initialized")
        
        def _insert():
            errors = self.client.insert_rows_json(self.table_ref, rows_data)
            if errors:
                raise RuntimeError(f"BigQuery insert errors: {errors}")
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _insert)
        
        logger.info(
            "Streamed audit logs to BigQuery",
            count=len(rows_data),
            table_id=self.config.table_id
        )
    
    async def _batch_insert(self, rows_data: List[Dict[str, Any]]) -> None:
        """Insert rows using batch load job."""
        if not self.client or not self.table_ref:
            raise RuntimeError("BigQuery client not initialized")
        
        def _insert():
            job_config = bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            )
            
            # Convert to NDJSON
            ndjson_data = "\n".join(json.dumps(row) for row in rows_data)
            
            job = self.client.load_table_from_json(
                rows_data, self.table_ref, job_config=job_config
            )
            job.result()  # Wait for job to complete
            
            if job.errors:
                raise RuntimeError(f"BigQuery load job errors: {job.errors}")
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _insert)
        
        logger.info(
            "Batch loaded audit logs to BigQuery",
            count=len(rows_data),
            table_id=self.config.table_id
        )
    
    async def query_audit_logs(
        self,
        tenant_id: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLogResponse]:
        """
        Query audit logs with filters.
        
        Args:
            tenant_id: Tenant identifier
            filters: Query filters
            limit: Maximum number of results
            offset: Result offset
            
        Returns:
            List of audit log responses
        """
        if self._is_available and self.client:
            try:
                return await self._query_audit_logs_bigquery(
                    tenant_id, filters, limit, offset
                )
            except Exception as e:
                logger.error(
                    "Failed to query audit logs from BigQuery",
                    error=str(e),
                    tenant_id=tenant_id
                )
                
                # Fall back to PostgreSQL if available
                if self.fallback_service:
                    logger.info("Falling back to PostgreSQL for query")
                    return await self.fallback_service.get_audit_logs(
                        tenant_id, filters, limit, offset
                    )
                raise
        
        # Use fallback service if BigQuery is not available
        if self.fallback_service:
            return await self.fallback_service.get_audit_logs(
                tenant_id, filters, limit, offset
            )
        
        raise RuntimeError("No audit log storage backend available")
    
    async def _query_audit_logs_bigquery(
        self,
        tenant_id: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLogResponse]:
        """Query audit logs from BigQuery."""
        if not self.client:
            raise RuntimeError("BigQuery client not initialized")
        
        # Build query
        query = f"""
        SELECT 
            id,
            tenant_id,
            event_type,
            user_id,
            resource_id,
            action,
            metadata,
            ip_address,
            user_agent,
            created_at
        FROM `{self.config.project_id}.{self.config.dataset_id}.{self.config.table_id}`
        WHERE tenant_id = @tenant_id
        """
        
        query_params = [
            bigquery.ScalarQueryParameter("tenant_id", "STRING", tenant_id)
        ]
        
        # Add filters
        if filters:
            if "event_type" in filters:
                query += " AND event_type = @event_type"
                query_params.append(
                    bigquery.ScalarQueryParameter("event_type", "STRING", filters["event_type"])
                )
            
            if "user_id" in filters:
                query += " AND user_id = @user_id"
                query_params.append(
                    bigquery.ScalarQueryParameter("user_id", "STRING", filters["user_id"])
                )
            
            if "start_date" in filters:
                query += " AND created_at >= @start_date"
                query_params.append(
                    bigquery.ScalarQueryParameter("start_date", "TIMESTAMP", filters["start_date"])
                )
            
            if "end_date" in filters:
                query += " AND created_at <= @end_date"
                query_params.append(
                    bigquery.ScalarQueryParameter("end_date", "TIMESTAMP", filters["end_date"])
                )
        
        # Add ordering and pagination
        query += " ORDER BY created_at DESC"
        query += f" LIMIT {limit} OFFSET {offset}"
        
        def _query():
            job_config = bigquery.QueryJobConfig(query_parameters=query_params)
            query_job = self.client.query(query, job_config=job_config)
            return list(query_job)
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        rows = await loop.run_in_executor(None, _query)
        
        # Convert to response objects
        results = []
        for row in rows:
            metadata = None
            if row.metadata:
                try:
                    metadata = json.loads(row.metadata)
                except (json.JSONDecodeError, TypeError):
                    metadata = row.metadata
            
            results.append(AuditLogResponse(
                id=row.id,
                tenant_id=row.tenant_id,
                event_type=row.event_type,
                user_id=row.user_id,
                resource_id=row.resource_id,
                action=row.action,
                metadata=metadata,
                ip_address=row.ip_address,
                user_agent=row.user_agent,
                created_at=row.created_at,
            ))
        
        logger.info(
            "Queried audit logs from BigQuery",
            tenant_id=tenant_id,
            count=len(results),
            limit=limit,
            offset=offset
        )
        
        return results
    
    async def get_audit_log_count(
        self,
        tenant_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Get count of audit logs matching filters.
        
        Args:
            tenant_id: Tenant identifier
            filters: Query filters
            
        Returns:
            Count of matching audit logs
        """
        if self._is_available and self.client:
            try:
                return await self._get_audit_log_count_bigquery(tenant_id, filters)
            except Exception as e:
                logger.error(
                    "Failed to get audit log count from BigQuery",
                    error=str(e),
                    tenant_id=tenant_id
                )
                
                # Fall back to PostgreSQL if available
                if self.fallback_service:
                    return await self.fallback_service.get_audit_log_count(
                        tenant_id, filters
                    )
                raise
        
        # Use fallback service if BigQuery is not available
        if self.fallback_service:
            return await self.fallback_service.get_audit_log_count(tenant_id, filters)
        
        return 0
    
    async def _get_audit_log_count_bigquery(
        self,
        tenant_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """Get audit log count from BigQuery."""
        if not self.client:
            raise RuntimeError("BigQuery client not initialized")
        
        # Build count query
        query = f"""
        SELECT COUNT(*) as count
        FROM `{self.config.project_id}.{self.config.dataset_id}.{self.config.table_id}`
        WHERE tenant_id = @tenant_id
        """
        
        query_params = [
            bigquery.ScalarQueryParameter("tenant_id", "STRING", tenant_id)
        ]
        
        # Add filters (same logic as query_audit_logs)
        if filters:
            if "event_type" in filters:
                query += " AND event_type = @event_type"
                query_params.append(
                    bigquery.ScalarQueryParameter("event_type", "STRING", filters["event_type"])
                )
            
            if "user_id" in filters:
                query += " AND user_id = @user_id"
                query_params.append(
                    bigquery.ScalarQueryParameter("user_id", "STRING", filters["user_id"])
                )
            
            if "start_date" in filters:
                query += " AND created_at >= @start_date"
                query_params.append(
                    bigquery.ScalarQueryParameter("start_date", "TIMESTAMP", filters["start_date"])
                )
            
            if "end_date" in filters:
                query += " AND created_at <= @end_date"
                query_params.append(
                    bigquery.ScalarQueryParameter("end_date", "TIMESTAMP", filters["end_date"])
                )
        
        def _query():
            job_config = bigquery.QueryJobConfig(query_parameters=query_params)
            query_job = self.client.query(query, job_config=job_config)
            return list(query_job)[0].count
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        count = await loop.run_in_executor(None, _query)
        
        return count
    
    def is_available(self) -> bool:
        """Check if BigQuery service is available."""
        return self._is_available
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status information."""
        return {
            "service": "BigQuery",
            "available": self._is_available,
            "config": {
                "project_id": self.config.project_id,
                "dataset_id": self.config.dataset_id,
                "table_id": self.config.table_id,
                "location": self.config.location,
                "streaming_enabled": self.config.enable_streaming,
            },
            "fallback_enabled": self.fallback_service is not None,
        }


# Global BigQuery service instance
_bigquery_service: Optional[BigQueryService] = None


def get_bigquery_service(fallback_service: Optional[AuditService] = None) -> BigQueryService:
    """Get or create BigQuery service instance."""
    global _bigquery_service
    
    if _bigquery_service is None:
        _bigquery_service = BigQueryService(fallback_service=fallback_service)
    
    return _bigquery_service