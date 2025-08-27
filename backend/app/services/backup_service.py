
"""
Backup and disaster recovery service.

This service handles automated backups, disaster recovery procedures,
and data restoration capabilities for the audit logging system.
"""

import asyncio
import gzip
import json
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import structlog
from google.cloud import storage
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.database import get_database
from app.models.audit import AuditLog
from app.services.bigquery_service import get_bigquery_service
from app.utils.metrics import metrics

logger = structlog.get_logger(__name__)
settings = get_settings()


class BackupConfig:
    """Backup configuration settings."""
    
    def __init__(
        self,
        name: str,
        backup_type: str,
        schedule: str,
        retention_days: int,
        compression: bool = True,
        encryption: bool = True,
        storage_location: str = "local",
        enabled: bool = True
    ):
        self.name = name
        self.backup_type = backup_type  # full, incremental, differential
        self.schedule = schedule  # cron expression
        self.retention_days = retention_days
        self.compression = compression
        self.encryption = encryption
        self.storage_location = storage_location  # local, gcs, s3
        self.enabled = enabled
    
    def get_retention_cutoff(self) -> datetime:
        """Get the cutoff date for backup retention."""
        return datetime.utcnow() - timedelta(days=self.retention_days)
    
    def __str__(self) -> str:
        return f"BackupConfig({self.name}, {self.backup_type}, {self.schedule})"


class BackupMetadata:
    """Backup metadata information."""
    
    def __init__(
        self,
        backup_id: str,
        config_name: str,
        backup_type: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        status: str = "running",
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        record_count: Optional[int] = None,
        checksum: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        self.backup_id = backup_id
        self.config_name = config_name
        self.backup_type = backup_type
        self.start_time = start_time
        self.end_time = end_time
        self.status = status
        self.file_path = file_path
        self.file_size = file_size
        self.record_count = record_count
        self.checksum = checksum
        self.error_message = error_message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'backup_id': self.backup_id,
            'config_name': self.config_name,
            'backup_type': self.backup_type,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'record_count': self.record_count,
            'checksum': self.checksum,
            'error_message': self.error_message
        }


class BackupService:
    """
    Backup and disaster recovery service.
    
    Handles automated backups, disaster recovery procedures,
    and data restoration capabilities.
    """
    
    def __init__(self):
        self.db = get_database()
        self.bigquery_service = get_bigquery_service()
        self.backup_configs = self._load_backup_configs()
        self.backup_history: List[BackupMetadata] = []
        self.storage_client = None
        
        # Initialize cloud storage client if configured
        if getattr(settings, 'backup_storage_type', 'local') == 'gcs':
            try:
                self.storage_client = storage.Client()
            except Exception as e:
                logger.warning("Failed to initialize GCS client", error=str(e))
    
    def _load_backup_configs(self) -> List[BackupConfig]:
        """Load backup configurations."""
        configs = []
        
        # Daily full backup
        configs.append(BackupConfig(
            name="daily_full",
            backup_type="full",
            schedule="0 2 * * *",  # Daily at 2 AM
            retention_days=getattr(settings, 'daily_backup_retention', 30),
            compression=True,
            encryption=True,
            storage_location=getattr(settings, 'backup_storage_type', 'local'),
            enabled=getattr(settings, 'enable_daily_backup', True)
        ))
        
        # Weekly full backup
        configs.append(BackupConfig(
            name="weekly_full",
            backup_type="full",
            schedule="0 1 * * 0",  # Weekly on Sunday at 1 AM
            retention_days=getattr(settings, 'weekly_backup_retention', 90),
            compression=True,
            encryption=True,
            storage_location=getattr(settings, 'backup_storage_type', 'local'),
            enabled=getattr(settings, 'enable_weekly_backup', True)
        ))
        
        # Monthly full backup
        configs.append(BackupConfig(
            name="monthly_full",
            backup_type="full",
            schedule="0 0 1 * *",  # Monthly on 1st at midnight
            retention_days=getattr(settings, 'monthly_backup_retention', 365),
            compression=True,
            encryption=True,
            storage_location=getattr(settings, 'backup_storage_type', 'local'),
            enabled=getattr(settings, 'enable_monthly_backup', True)
        ))
        
        # Hourly incremental backup (for high-frequency environments)
        configs.append(BackupConfig(
            name="hourly_incremental",
            backup_type="incremental",
            schedule="0 * * * *",  # Every hour
            retention_days=getattr(settings, 'incremental_backup_retention', 7),
            compression=True,
            encryption=False,  # Faster for frequent backups
            storage_location=getattr(settings, 'backup_storage_type', 'local'),
            enabled=getattr(settings, 'enable_incremental_backup', False)
        ))
        
        return [config for config in configs if config.enabled]
    
    async def create_backup(
        self,
        config_name: str,
        backup_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> BackupMetadata:
        """
        Create a backup based on configuration.
        
        Args:
            config_name: Name of backup configuration to use
            backup_type: Override backup type (full, incremental, differential)
            start_date: Start date for data range (for incremental backups)
            end_date: End date for data range
            
        Returns:
            Backup metadata
        """
        # Find backup configuration
        config = next((c for c in self.backup_configs if c.name == config_name), None)
        if not config:
            raise ValueError(f"Backup configuration '{config_name}' not found")
        
        # Generate backup ID
        backup_id = f"{config_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Create backup metadata
        metadata = BackupMetadata(
            backup_id=backup_id,
            config_name=config_name,
            backup_type=backup_type or config.backup_type,
            start_time=datetime.utcnow()
        )
        
        logger.info(
            "Starting backup",
            backup_id=backup_id,
            config_name=config_name,
            backup_type=metadata.backup_type
        )
        
        try:
            # Determine date range for backup
            if metadata.backup_type == "incremental":
                if not start_date:
                    # Get last backup time for incremental
                    start_date = await self._get_last_backup_time(config_name)
                end_date = end_date or datetime.utcnow()
            elif metadata.backup_type == "differential":
                if not start_date:
                    # Get last full backup time for differential
                    start_date = await self._get_last_full_backup_time(config_name)
                end_date = end_date or datetime.utcnow()
            else:  # full backup
                start_date = None
                end_date = None
            
            # Create backup file
            backup_file_path = await self._create_backup_file(
                metadata, config, start_date, end_date
            )
            
            metadata.file_path = str(backup_file_path)
            metadata.file_size = backup_file_path.stat().st_size
            
            # Calculate checksum
            metadata.checksum = await self._calculate_checksum(backup_file_path)
            
            # Upload to cloud storage if configured
            if config.storage_location != "local":
                await self._upload_to_cloud_storage(backup_file_path, metadata, config)
            
            # Update metadata
            metadata.end_time = datetime.utcnow()
            metadata.status = "completed"
            
            # Add to history
            self.backup_history.append(metadata)
            
            # Record metrics
            duration = (metadata.end_time - metadata.start_time).total_seconds()
            metrics.record_backup_created(
                config_name=config_name,
                backup_type=metadata.backup_type,
                file_size=metadata.file_size,
                record_count=metadata.record_count,
                duration=duration
            )
            
            logger.info(
                "Backup completed successfully",
                backup_id=backup_id,
                file_size=metadata.file_size,
                record_count=metadata.record_count,
                duration=duration
            )
            
            return metadata
            
        except Exception as e:
            metadata.end_time = datetime.utcnow()
            metadata.status = "failed"
            metadata.error_message = str(e)
            self.backup_history.append(metadata)
            
            logger.error("Backup failed", backup_id=backup_id, error=str(e))
            raise
    
    async def _create_backup_file(
        self,
        metadata: BackupMetadata,
        config: BackupConfig,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Path:
        """Create backup file with audit log data."""
        # Create backup directory
        backup_dir = Path(getattr(settings, 'backup_directory', '/tmp/audit_backups'))
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = metadata.start_time.strftime('%Y%m%d_%H%M%S')
        filename = f"{metadata.backup_id}.json"
        if config.compression:
            filename += ".gz"
        
        backup_file_path = backup_dir / filename
        
        # Query data based on backup type and date range
        async with self.db.get_session() as session:
            query = select(AuditLog)
            
            if start_date:
                query = query.where(AuditLog.created_at >= start_date)
            if end_date:
                query = query.where(AuditLog.created_at <= end_date)
            
            # Order by creation time for consistent backups
            query = query.order_by(AuditLog.created_at)
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            result = await session.execute(count_query)
            total_count = result.scalar()
            metadata.record_count = total_count
            
            logger.info(
                "Creating backup file",
                backup_id=metadata.backup_id,
                record_count=total_count,
                start_date=start_date,
                end_date=end_date
            )
            
            # Write data to file
            if config.compression:
                file_handle = gzip.open(backup_file_path, 'wt', encoding='utf-8')
            else:
                file_handle = open(backup_file_path, 'w', encoding='utf-8')
            
            try:
                # Write backup metadata header
                backup_header = {
                    'backup_metadata': metadata.to_dict(),
                    'backup_config': {
                        'name': config.name,
                        'backup_type': config.backup_type,
                        'compression': config.compression,
                        'encryption': config.encryption
                    },
                    'data_range': {
                        'start_date': start_date.isoformat() if start_date else None,
                        'end_date': end_date.isoformat() if end_date else None,
                        'total_records': total_count
                    }
                }
                
                file_handle.write(json.dumps(backup_header) + '\n')
                
                # Write data in batches
                batch_size = getattr(settings, 'backup_batch_size', 1000)
                offset = 0
                
                while offset < total_count:
                    batch_query = query.offset(offset).limit(batch_size)
                    result = await session.execute(batch_query)
                    batch_records = result.scalars().all()
                    
                    if not batch_records:
                        break
                    
                    # Convert records to JSON
                    for record in batch_records:
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
                            'metadata': record.metadata,
                            'created_at': record.created_at.isoformat()
                        }
                        file_handle.write(json.dumps(record_dict) + '\n')
                    
                    offset += len(batch_records)
                    
                    logger.debug(
                        "Backup progress",
                        backup_id=metadata.backup_id,
                        processed=offset,
                        total=total_count,
                        progress=f"{(offset/total_count)*100:.1f}%"
                    )
            
            finally:
                file_handle.close()
        
        return backup_file_path
    
    async def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of backup file."""
        import hashlib
        
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    async def _upload_to_cloud_storage(
        self,
        file_path: Path,
        metadata: BackupMetadata,
        config: BackupConfig
    ) -> None:
        """Upload backup file to cloud storage."""
        if config.storage_location == "gcs" and self.storage_client:
            try:
                bucket_name = getattr(settings, 'backup_gcs_bucket', 'audit-service-backups')
                bucket = self.storage_client.bucket(bucket_name)
                
                # Create blob path
                blob_path = f"backups/{config.name}/{file_path.name}"
                blob = bucket.blob(blob_path)
                
                # Upload file
                blob.upload_from_filename(str(file_path))
                
                # Set metadata
                blob.metadata = {
                    'backup_id': metadata.backup_id,
                    'config_name': config.name,
                    'backup_type': metadata.backup_type,
                    'record_count': str(metadata.record_count),
                    'checksum': metadata.checksum
                }
                blob.patch()
                
                logger.info(
                    "Backup uploaded to GCS",
                    backup_id=metadata.backup_id,
                    bucket=bucket_name,
                    blob_path=blob_path
                )
                
            except Exception as e:
                logger.error("Failed to upload backup to GCS", error=str(e))
                raise
    
    async def _get_last_backup_time(self, config_name: str) -> datetime:
        """Get the timestamp of the last backup for incremental backups."""
        # Find the most recent successful backup
        recent_backups = [
            b for b in self.backup_history
            if b.config_name == config_name and b.status == "completed"
        ]
        
        if recent_backups:
            latest_backup = max(recent_backups, key=lambda b: b.start_time)
            return latest_backup.start_time
        
        # If no previous backup, start from 24 hours ago
        return datetime.utcnow() - timedelta(hours=24)
    
    async def _get_last_full_backup_time(self, config_name: str) -> datetime:
        """Get the timestamp of the last full backup for differential backups."""
        # Find the most recent successful full backup
        full_backups = [
            b for b in self.backup_history
            if b.config_name == config_name and b.backup_type == "full" and b.status == "completed"
        ]
        
        if full_backups:
            latest_backup = max(full_backups, key=lambda b: b.start_time)
            return latest_backup.start_time
        
        # If no previous full backup, start from 7 days ago
        return datetime.utcnow() - timedelta(days=7)
    
    async def restore_from_backup(
        self,
        backup_id: str,
        target_table: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Restore data from a backup.
        
        Args:
            backup_id: ID of backup to restore from
            target_table: Target table name (default: main audit table)
            dry_run: If True, only validate backup without restoring
            
        Returns:
            Restoration results
        """
        # Find backup metadata
        backup_metadata = next(
            (b for b in self.backup_history if b.backup_id == backup_id), None
        )
        
        if not backup_metadata:
            raise ValueError(f"Backup '{backup_id}' not found")
        
        if backup_metadata.status != "completed":
            raise ValueError(f"Backup '{backup_id}' is not in completed state")
        
        logger.info(
            "Starting restore from backup",
            backup_id=backup_id,
            dry_run=dry_run,
            target_table=target_table
        )
        
        restore_results = {
            'backup_id': backup_id,
            'start_time': datetime.utcnow(),
            'dry_run': dry_run,
            'records_processed': 0,
            'records_restored': 0,
            'errors': [],
            'validation_results': {}
        }
        
        try:
            # Validate backup file
            backup_file_path = Path(backup_metadata.file_path)
            if not backup_file_path.exists():
                # Try to download from cloud storage
                await self._download_from_cloud_storage(backup_metadata)
            
            # Verify checksum
            current_checksum = await self._calculate_checksum(backup_file_path)
            if current_checksum != backup_metadata.checksum:
                raise ValueError("Backup file checksum mismatch - file may be corrupted")
            
            restore_results['validation_results']['checksum_valid'] = True
            
            # Process backup file
            if backup_file_path.suffix == '.gz':
                file_handle = gzip.open(backup_file_path, 'rt', encoding='utf-8')
            else:
                file_handle = open(backup_file_path, 'r', encoding='utf-8')
            
            try:
                # Read backup header
                header_line = file_handle.readline().strip()
                backup_header = json.loads(header_line)
                
                restore_results['validation_results']['header_valid'] = True
                restore_results['validation_results']['expected_records'] = (
                    backup_header['data_range']['total_records']
                )
                
                if not dry_run:
                    # Begin database transaction
                    async with self.db.get_session() as session:
                        # Process data records
                        batch_records = []
                        batch_size = getattr(settings, 'restore_batch_size', 100)
                        
                        for line in file_handle:
                            line = line.strip()
                            if not line:
                                continue
                            
                            try:
                                record_data = json.loads(line)
                                batch_records.append(record_data)
                                restore_results['records_processed'] += 1
                                
                                if len(batch_records) >= batch_size:
                                    # Process batch
                                    restored_count = await self._restore_batch(
                                        session, batch_records, target_table
                                    )
                                    restore_results['records_restored'] += restored_count
                                    batch_records = []
                                
                            except json.JSONDecodeError as e:
                                error_msg = f"Invalid JSON at record {restore_results['records_processed']}: {str(e)}"
                                restore_results['errors'].append(error_msg)
                                logger.warning("Restore JSON error", error=error_msg)
                        
                        # Process remaining records
                        if batch_records:
                            restored_count = await self._restore_batch(
                                session, batch_records, target_table
                            )
                            restore_results['records_restored'] += restored_count
                        
                        # Commit transaction
                        await session.commit()
                
                else:
                    # Dry run - just count records
                    for line in file_handle:
                        if line.strip():
                            restore_results['records_processed'] += 1
            
            finally:
                file_handle.close()
            
            restore_results['end_time'] = datetime.utcnow()
            restore_results['duration'] = (
                restore_results['end_time'] - restore_results['start_time']
            ).total_seconds()
            
            logger.info(
                "Restore completed",
                backup_id=backup_id,
                dry_run=dry_run,
                records_processed=restore_results['records_processed'],
                records_restored=restore_results['records_restored'],
                duration=restore_results['duration'],
                errors=len(restore_results['errors'])
            )
            
            return restore_results
            
        except Exception as e:
            restore_results['end_time'] = datetime.utcnow()
            restore_results['error'] = str(e)
            logger.error("Restore failed", backup_id=backup_id, error=str(e))
            raise
    
    async def _download_from_cloud_storage(self, metadata: BackupMetadata) -> None:
        """Download backup file from cloud storage."""
        if not self.storage_client:
            raise ValueError("Cloud storage client not available")
        
        try:
            bucket_name = getattr(settings, 'backup_gcs_bucket', 'audit-service-backups')
            bucket = self.storage_client.bucket(bucket_name)
            
            # Find backup config
            config = next(
                (c for c in self.backup_configs if c.name == metadata.config_name), None
            )
            if not config:
                raise ValueError(f"Backup config '{metadata.config_name}' not found")
            
            # Download file
            blob_path = f"backups/{config.name}/{Path(metadata.file_path).name}"
            blob = bucket.blob(blob_path)
            
            blob.download_to_filename(metadata.file_path)
            
            logger.info(
                "Downloaded backup from GCS",
                backup_id=metadata.backup_id,
                blob_path=blob_path
            )
            
        except Exception as e:
            logger.error("Failed to download backup from GCS", error=str(e))
            raise
    
    async def _restore_batch(
        self,
        session: AsyncSession,
        batch_records: List[Dict[str, Any]],
        target_table: Optional[str]
    ) -> int:
        """Restore a batch of records to the database."""
        restored_count = 0
        
        for record_data in batch_records:
            try:
                # Create AuditLog instance
                audit_log = AuditLog(
                    id=record_data.get('id'),
                    tenant_id=record_data['tenant_id'],
                    user_id=record_data.get('user_id'),
                    event_type=record_data['event_type'],
                    resource_type=record_data.get('resource_type'),
                    resource_id=record_data.get('resource_id'),
                    action=record_data['action'],
                    timestamp=datetime.fromisoformat(record_data['timestamp']),
                    ip_address=record_data.get('ip_address'),
                    user_agent=record_data.get('user_agent'),
                    metadata=record_data.get('metadata', {}),
                    created_at=datetime.fromisoformat(record_data['created_at'])
                )
                
                session.add(audit_log)
                restored_count += 1
                
            except Exception as e:
                logger.warning(
                    "Failed to restore record",
                    record_id=record_data.get('id'),
                    error=str(e)
                )
        
        return restored_count
    
    async def cleanup_old_backups(self) -> Dict[str, Any]:
        """Clean up old backups based on retention policies."""
        cleanup_results = {
            'start_time': datetime.utcnow(),
            'configs_processed': 0,
            'backups_deleted': 0,
            'storage_freed': 0,
            'errors': []
        }
        
        logger.info("Starting backup cleanup")
        
        for config in self.backup_configs:
            try:
                retention_cutoff = config.get_retention_cutoff()
                
                # Find old backups for this config
                old_backups = [
                    b for b in self.backup_history
                    if (b.config_name == config.name and 
                        b.start_time < retention_cutoff and
                        b.status == "completed")
                ]
                
                for backup in old_backups:
                    try:
                        # Delete local file
                        if backup.file_path and Path(backup.file_path).exists():
                            file_size = Path(backup.file_path).stat().st_size
                            Path(backup.file_path).unlink()
                            cleanup_results['storage_freed'] += file_size
                        
                        # Delete from cloud storage
                        if config.storage_location != "local":
                            await self._delete_from_cloud_storage(backup, config)
                        
                        # Remove from history
                        self.backup_history.remove(backup)
                        cleanup_results['backups_deleted'] += 1
                        
                        logger.info(
                            "Deleted old backup",
                            backup_id=backup.backup_id,
                            age_days=(datetime.utcnow() - backup.start_time).days
                        )
                        
                    except Exception as e:
                        error_msg = f"Failed to delete backup {backup.backup_id}: {str(e)}"
                        cleanup_results['errors'].append(error_msg)
                        logger.error("Backup deletion failed", backup_id=backup.backup_id, error=str(e))
                
                cleanup_results['configs_processed'] += 1
                
            except Exception as e:
                error_msg = f"Failed to process config {config.name}: {str(e)}"
                cleanup_results['errors'].append(error_msg)
                logger.error("Config processing failed", config=config.name, error=str(e))
        
        cleanup_results['end_time'] = datetime.utcnow()
        cleanup_results['duration'] = (
            cleanup_results['end_time'] - cleanup_results['start_time']
        ).total_seconds()
        
        logger.info(
            "Backup cleanup completed",
            backups_deleted=cleanup_results['backups_deleted'],
            storage_freed=cleanup_results['storage_freed'],
            duration=cleanup_results['duration']
        )
        
        return cleanup_results
    
    async def _delete_from_cloud_storage(
        self,
        metadata: BackupMetadata,
        config: BackupConfig
    ) -> None:
        """Delete backup file from cloud storage."""
        if config.storage_location == "gcs" and self.storage_client:
            try:
                bucket_name = getattr(settings, 'backup_gcs_bucket', 'audit-service-backups')
                bucket = self.storage_client.bucket(bucket_name)
                
                blob_path = f"backups/{config.name}/{Path(metadata.file_path).name}"
                blob = bucket.blob(blob_path)
                
                blob.delete()
                
                logger.info(
                    "Deleted backup from GCS",
                    backup_id=metadata.backup_id,
                    blob_path=blob_path
                )
                
            except Exception as e:
                logger.error("Failed to delete backup from GCS", error=str(e))
                raise
    
    async def get_backup_status(self) -> Dict[str, Any]:
        """Get backup service status and statistics."""
        status = {
            'service': 'BackupService',
            'configs': len(self.backup_configs),
            'total_backups': len(self.backup_history),
            'recent_backups': [],
            'storage_usage': 0,
            'last_backup_time': None,
            'next_scheduled_backup': None
        }
        
        # Recent backups (last 10)
        recent_backups = sorted(
            self.backup_history,
            key=lambda b: b.start_time,
            reverse=True
        )[:10]
        
        status['recent_backups'] = [b.to_dict() for b in recent_backups]
        
        # Calculate storage usage
        for backup in self.backup_history:
            if backup.file_size:
                status['storage_usage'] += backup.file_size
        
        # Last backup time
        if recent_backups:
            status['last_backup_time'] = recent_backups[0].start_time.isoformat()
        
        # Config information
        status['configs'] = [
            {
                'name': config.name,
                'backup_type': config.backup_type,
                'schedule': config.schedule,
                'retention_days': config.retention_days,
                'enabled': config.enabled,
                'storage_location': config.storage_location
            }
            for config in self.backup_configs
        ]
        
        return status
    
    async def verify_backup_integrity(self, backup