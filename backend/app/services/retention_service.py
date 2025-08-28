"""
Data retention and cleanup service.

This service handles automated data retention policies, cleanup procedures,
and archival processes for audit logs to maintain optimal performance
and comply with data governance requirements.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import structlog
from google.cloud import bigquery
from sqlalchemy import and_, delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.database import get_database
from app.models.audit import AuditLog
from app.services.bigquery_service import get_bigquery_service
from app.utils.metrics import metrics

logger = structlog.get_logger(__name__)
settings = get_settings()


class RetentionPolicy:
    """Data retention policy configuration."""
    
    def __init__(
        self,
        name: str,
        retention_days: int,
        archive_days: Optional[int] = None,
        conditions: Optional[Dict[str, Any]] = None,
        enabled: bool = True
    ):
        self.name = name
        self.retention_days = retention_days
        self.archive_days = archive_days or (retention_days // 2)
        self.conditions = conditions or {}
        self.enabled = enabled
    
    def get_retention_cutoff(self) -> datetime:
        """Get the cutoff date for data retention."""
        return datetime.utcnow() - timedelta(days=self.retention_days)
    
    def get_archive_cutoff(self) -> datetime:
        """Get the cutoff date for data archival."""
        return datetime.utcnow() - timedelta(days=self.archive_days)
    
    def should_archive(self) -> bool:
        """Check if archival is enabled for this policy."""
        return self.archive_days < self.retention_days
    
    def __str__(self) -> str:
        return f"RetentionPolicy({self.name}, {self.retention_days}d)"


class RetentionService:
    """
    Data retention and cleanup service.
    
    Manages automated data retention policies, cleanup procedures,
    and archival processes for audit logs.
    """
    
    def __init__(self):
        self.db = get_database()
        self.bigquery_service = get_bigquery_service()
        self.policies = self._load_retention_policies()
        self._cleanup_stats = {
            'last_run': None,
            'total_deleted': 0,
            'total_archived': 0,
            'errors': 0
        }
    
    def _load_retention_policies(self) -> List[RetentionPolicy]:
        """Load retention policies from configuration."""
        policies = []
        
        # Default policy for all audit logs
        policies.append(RetentionPolicy(
            name="default",
            retention_days=getattr(settings, 'default_retention_days', 365),
            archive_days=getattr(settings, 'default_archive_days', 90),
            enabled=True
        ))
        
        # Policy for high-volume events (shorter retention)
        policies.append(RetentionPolicy(
            name="high_volume",
            retention_days=getattr(settings, 'high_volume_retention_days', 90),
            archive_days=getattr(settings, 'high_volume_archive_days', 30),
            conditions={'event_type': ['api_request', 'page_view', 'click']},
            enabled=getattr(settings, 'enable_high_volume_policy', True)
        ))
        
        # Policy for security events (longer retention)
        policies.append(RetentionPolicy(
            name="security",
            retention_days=getattr(settings, 'security_retention_days', 2555),  # 7 years
            archive_days=getattr(settings, 'security_archive_days', 365),
            conditions={'event_type': ['login', 'logout', 'permission_change', 'security_alert']},
            enabled=getattr(settings, 'enable_security_policy', True)
        ))
        
        # Policy for compliance events (extended retention)
        policies.append(RetentionPolicy(
            name="compliance",
            retention_days=getattr(settings, 'compliance_retention_days', 3650),  # 10 years
            archive_days=getattr(settings, 'compliance_archive_days', 730),  # 2 years
            conditions={'event_type': ['financial_transaction', 'data_export', 'compliance_report']},
            enabled=getattr(settings, 'enable_compliance_policy', True)
        ))
        
        # Filter enabled policies
        return [policy for policy in policies if policy.enabled]
    
    async def run_cleanup(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Run data cleanup based on retention policies.
        
        Args:
            dry_run: If True, only simulate cleanup without actual deletion
            
        Returns:
            Cleanup statistics and results
        """
        logger.info("Starting data cleanup", dry_run=dry_run, policies_count=len(self.policies))
        
        cleanup_results = {
            'start_time': datetime.utcnow(),
            'dry_run': dry_run,
            'policies_processed': 0,
            'total_deleted': 0,
            'total_archived': 0,
            'errors': [],
            'policy_results': {}
        }
        
        try:
            for policy in self.policies:
                if not policy.enabled:
                    continue
                
                logger.info("Processing retention policy", policy=policy.name)
                
                try:
                    policy_result = await self._process_policy(policy, dry_run)
                    cleanup_results['policy_results'][policy.name] = policy_result
                    cleanup_results['total_deleted'] += policy_result['deleted_count']
                    cleanup_results['total_archived'] += policy_result['archived_count']
                    cleanup_results['policies_processed'] += 1
                    
                except Exception as e:
                    error_msg = f"Error processing policy {policy.name}: {str(e)}"
                    logger.error("Policy processing failed", policy=policy.name, error=str(e))
                    cleanup_results['errors'].append(error_msg)
                    self._cleanup_stats['errors'] += 1
            
            # Update statistics
            if not dry_run:
                self._cleanup_stats['last_run'] = datetime.utcnow()
                self._cleanup_stats['total_deleted'] += cleanup_results['total_deleted']
                self._cleanup_stats['total_archived'] += cleanup_results['total_archived']
            
            cleanup_results['end_time'] = datetime.utcnow()
            cleanup_results['duration'] = (
                cleanup_results['end_time'] - cleanup_results['start_time']
            ).total_seconds()
            
            # Record metrics
            metrics.record_cleanup_run(
                deleted=cleanup_results['total_deleted'],
                archived=cleanup_results['total_archived'],
                duration=cleanup_results['duration'],
                errors=len(cleanup_results['errors'])
            )
            
            logger.info(
                "Data cleanup completed",
                dry_run=dry_run,
                deleted=cleanup_results['total_deleted'],
                archived=cleanup_results['total_archived'],
                duration=cleanup_results['duration'],
                errors=len(cleanup_results['errors'])
            )
            
            return cleanup_results
            
        except Exception as e:
            logger.error("Data cleanup failed", error=str(e))
            cleanup_results['errors'].append(f"Cleanup failed: {str(e)}")
            raise
    
    async def _process_policy(self, policy: RetentionPolicy, dry_run: bool) -> Dict[str, Any]:
        """Process a single retention policy."""
        result = {
            'policy_name': policy.name,
            'retention_cutoff': policy.get_retention_cutoff(),
            'archive_cutoff': policy.get_archive_cutoff(),
            'deleted_count': 0,
            'archived_count': 0,
            'errors': []
        }
        
        try:
            # Archive old data if archival is enabled
            if policy.should_archive():
                result['archived_count'] = await self._archive_data(policy, dry_run)
            
            # Delete expired data
            result['deleted_count'] = await self._delete_expired_data(policy, dry_run)
            
            # Clean up BigQuery if using cloud storage
            if self.bigquery_service.is_available():
                await self._cleanup_bigquery_data(policy, dry_run)
            
        except Exception as e:
            error_msg = f"Policy {policy.name} processing error: {str(e)}"
            result['errors'].append(error_msg)
            logger.error("Policy processing error", policy=policy.name, error=str(e))
        
        return result
    
    async def _archive_data(self, policy: RetentionPolicy, dry_run: bool) -> int:
        """Archive data based on policy."""
        archive_cutoff = policy.get_archive_cutoff()
        retention_cutoff = policy.get_retention_cutoff()
        
        logger.info(
            "Archiving data",
            policy=policy.name,
            archive_cutoff=archive_cutoff,
            retention_cutoff=retention_cutoff
        )
        
        archived_count = 0
        
        async with self.db.get_session() as session:
            # Build query based on policy conditions
            query = select(AuditLog).where(
                and_(
                    AuditLog.created_at >= retention_cutoff,
                    AuditLog.created_at < archive_cutoff
                )
            )
            
            # Apply policy conditions
            if policy.conditions:
                for field, values in policy.conditions.items():
                    if hasattr(AuditLog, field):
                        column = getattr(AuditLog, field)
                        if isinstance(values, list):
                            query = query.where(column.in_(values))
                        else:
                            query = query.where(column == values)
            
            # Get count for logging
            count_query = select(func.count()).select_from(query.subquery())
            result = await session.execute(count_query)
            total_count = result.scalar()
            
            if total_count == 0:
                logger.info("No data to archive", policy=policy.name)
                return 0
            
            logger.info("Found data to archive", policy=policy.name, count=total_count)
            
            if not dry_run:
                # Process in batches to avoid memory issues
                batch_size = getattr(settings, 'archive_batch_size', 1000)
                offset = 0
                
                while offset < total_count:
                    batch_query = query.offset(offset).limit(batch_size)
                    batch_result = await session.execute(batch_query)
                    batch_records = batch_result.scalars().all()
                    
                    if not batch_records:
                        break
                    
                    # Archive to external storage (e.g., Cloud Storage)
                    await self._archive_batch_to_storage(batch_records, policy)
                    
                    archived_count += len(batch_records)
                    offset += batch_size
                    
                    logger.debug(
                        "Archived batch",
                        policy=policy.name,
                        batch_size=len(batch_records),
                        total_archived=archived_count
                    )
            else:
                archived_count = total_count
        
        logger.info("Data archival completed", policy=policy.name, archived_count=archived_count)
        return archived_count
    
    async def _archive_batch_to_storage(self, records: List[AuditLog], policy: RetentionPolicy) -> None:
        """Archive a batch of records to external storage."""
        # This would typically involve:
        # 1. Serializing records to JSON/Parquet
        # 2. Compressing the data
        # 3. Uploading to Cloud Storage/S3
        # 4. Recording archive metadata
        
        # For now, we'll implement a simple JSON export
        import json
        from pathlib import Path
        
        archive_dir = Path(getattr(settings, 'archive_directory', '/tmp/audit_archive'))
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"{policy.name}_{timestamp}_{len(records)}.json"
        filepath = archive_dir / filename
        
        # Convert records to JSON
        archive_data = []
        for record in records:
            record_dict = {
                'id': str(record.id),
                'tenant_id': record.tenant_id,
                'user_id': record.user_id,
                'event_type': record.event_type,
                'resource_type': record.resource_type,
                'resource_id': record.resource_id,
                'action': record.action,
                'timestamp': record.timestamp.isoformat(),
                'ip_address': record.ip_address,
                'user_agent': record.user_agent,
                'metadata': record.event_metadata,
                'created_at': record.created_at.isoformat()
            }
            archive_data.append(record_dict)
        
        # Write to file
        with open(filepath, 'w') as f:
            json.dump(archive_data, f, indent=2)
        
        logger.info(
            "Batch archived to storage",
            policy=policy.name,
            filename=filename,
            record_count=len(records)
        )
    
    async def _delete_expired_data(self, policy: RetentionPolicy, dry_run: bool) -> int:
        """Delete expired data based on policy."""
        retention_cutoff = policy.get_retention_cutoff()
        
        logger.info("Deleting expired data", policy=policy.name, cutoff=retention_cutoff)
        
        async with self.db.get_session() as session:
            # Build delete query based on policy conditions
            delete_query = delete(AuditLog).where(AuditLog.created_at < retention_cutoff)
            
            # Apply policy conditions
            if policy.conditions:
                for field, values in policy.conditions.items():
                    if hasattr(AuditLog, field):
                        column = getattr(AuditLog, field)
                        if isinstance(values, list):
                            delete_query = delete_query.where(column.in_(values))
                        else:
                            delete_query = delete_query.where(column == values)
            
            if dry_run:
                # Count records that would be deleted
                count_query = select(func.count()).select_from(
                    select(AuditLog).where(delete_query.whereclause).subquery()
                )
                result = await session.execute(count_query)
                deleted_count = result.scalar()
            else:
                # Execute deletion
                result = await session.execute(delete_query)
                deleted_count = result.rowcount
                await session.commit()
        
        logger.info("Data deletion completed", policy=policy.name, deleted_count=deleted_count)
        return deleted_count
    
    async def _cleanup_bigquery_data(self, policy: RetentionPolicy, dry_run: bool) -> None:
        """Clean up BigQuery data based on retention policy."""
        if not self.bigquery_service.is_available():
            return
        
        try:
            retention_cutoff = policy.get_retention_cutoff()
            
            # Build BigQuery DELETE query
            table_id = f"{settings.gcp_project_id}.{settings.bigquery_dataset}.{settings.bigquery_table}"
            
            conditions = [f"timestamp < '{retention_cutoff.isoformat()}'"]
            
            # Apply policy conditions
            if policy.conditions:
                for field, values in policy.conditions.items():
                    if isinstance(values, list):
                        value_list = "', '".join(values)
                        conditions.append(f"{field} IN ('{value_list}')")
                    else:
                        conditions.append(f"{field} = '{values}'")
            
            where_clause = " AND ".join(conditions)
            delete_sql = f"DELETE FROM `{table_id}` WHERE {where_clause}"
            
            if dry_run:
                # Count records that would be deleted
                count_sql = f"SELECT COUNT(*) FROM `{table_id}` WHERE {where_clause}"
                logger.info("BigQuery cleanup (dry run)", policy=policy.name, query=count_sql)
            else:
                logger.info("Executing BigQuery cleanup", policy=policy.name, query=delete_sql)
                # Execute the delete query
                # Note: This would require BigQuery client implementation
                # await self.bigquery_service.execute_query(delete_sql)
        
        except Exception as e:
            logger.error("BigQuery cleanup failed", policy=policy.name, error=str(e))
    
    async def get_retention_stats(self) -> Dict[str, Any]:
        """Get retention and cleanup statistics."""
        stats = {
            'cleanup_stats': self._cleanup_stats.copy(),
            'policies': [],
            'data_distribution': {}
        }
        
        # Add policy information
        for policy in self.policies:
            policy_info = {
                'name': policy.name,
                'retention_days': policy.retention_days,
                'archive_days': policy.archive_days,
                'enabled': policy.enabled,
                'conditions': policy.conditions,
                'retention_cutoff': policy.get_retention_cutoff().isoformat(),
                'archive_cutoff': policy.get_archive_cutoff().isoformat()
            }
            stats['policies'].append(policy_info)
        
        # Get data distribution statistics
        async with self.db.get_session() as session:
            # Total record count
            total_query = select(func.count()).select_from(AuditLog)
            result = await session.execute(total_query)
            stats['data_distribution']['total_records'] = result.scalar()
            
            # Records by age
            now = datetime.utcnow()
            age_ranges = [
                ('last_24h', 1),
                ('last_week', 7),
                ('last_month', 30),
                ('last_quarter', 90),
                ('last_year', 365)
            ]
            
            for range_name, days in age_ranges:
                cutoff = now - timedelta(days=days)
                age_query = select(func.count()).select_from(AuditLog).where(
                    AuditLog.created_at >= cutoff
                )
                result = await session.execute(age_query)
                stats['data_distribution'][range_name] = result.scalar()
        
        return stats
    
    async def estimate_cleanup_impact(self) -> Dict[str, Any]:
        """Estimate the impact of running cleanup policies."""
        impact = {
            'policies': {},
            'total_to_delete': 0,
            'total_to_archive': 0,
            'storage_savings_estimate': 0
        }
        
        for policy in self.policies:
            if not policy.enabled:
                continue
            
            policy_impact = await self._estimate_policy_impact(policy)
            impact['policies'][policy.name] = policy_impact
            impact['total_to_delete'] += policy_impact['records_to_delete']
            impact['total_to_archive'] += policy_impact['records_to_archive']
        
        # Estimate storage savings (rough calculation)
        avg_record_size = getattr(settings, 'avg_audit_record_size_bytes', 1024)
        impact['storage_savings_estimate'] = (
            impact['total_to_delete'] * avg_record_size
        )
        
        return impact
    
    async def _estimate_policy_impact(self, policy: RetentionPolicy) -> Dict[str, Any]:
        """Estimate the impact of a single policy."""
        retention_cutoff = policy.get_retention_cutoff()
        archive_cutoff = policy.get_archive_cutoff()
        
        impact = {
            'policy_name': policy.name,
            'records_to_delete': 0,
            'records_to_archive': 0,
            'oldest_record': None,
            'newest_record': None
        }
        
        async with self.db.get_session() as session:
            # Base query with policy conditions
            base_query = select(AuditLog)
            
            if policy.conditions:
                for field, values in policy.conditions.items():
                    if hasattr(AuditLog, field):
                        column = getattr(AuditLog, field)
                        if isinstance(values, list):
                            base_query = base_query.where(column.in_(values))
                        else:
                            base_query = base_query.where(column == values)
            
            # Count records to delete
            delete_query = select(func.count()).select_from(
                base_query.where(AuditLog.created_at < retention_cutoff).subquery()
            )
            result = await session.execute(delete_query)
            impact['records_to_delete'] = result.scalar()
            
            # Count records to archive
            if policy.should_archive():
                archive_query = select(func.count()).select_from(
                    base_query.where(
                        and_(
                            AuditLog.created_at >= retention_cutoff,
                            AuditLog.created_at < archive_cutoff
                        )
                    ).subquery()
                )
                result = await session.execute(archive_query)
                impact['records_to_archive'] = result.scalar()
            
            # Get date range for affected records
            date_query = select(
                func.min(AuditLog.created_at),
                func.max(AuditLog.created_at)
            ).select_from(base_query.subquery())
            result = await session.execute(date_query)
            min_date, max_date = result.first()
            
            if min_date:
                impact['oldest_record'] = min_date.isoformat()
            if max_date:
                impact['newest_record'] = max_date.isoformat()
        
        return impact


# Global retention service instance
_retention_service: Optional[RetentionService] = None


def get_retention_service() -> RetentionService:
    """Get or create retention service instance."""
    global _retention_service
    
    if _retention_service is None:
        _retention_service = RetentionService()
    
    return _retention_service