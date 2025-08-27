"""
Database connection and management for the audit log framework.

This module provides database connection management, session handling,
and basic database operations using SQLAlchemy with async support.
"""

from typing import AsyncGenerator, Optional, Any, Dict, List
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, select, func
from sqlalchemy.exc import SQLAlchemyError
import structlog

from app.config import DatabaseSettings
from app.core.exceptions import DatabaseError
from app.db.schemas import Base, AuditLog, Tenant, User, APIKey

logger = structlog.get_logger(__name__)


class DatabaseManager:
    """Database connection manager with async support."""
    
    def __init__(self, settings: DatabaseSettings):
        self.settings = settings
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize database connection and create tables."""
        try:
            # Create async engine
            self.engine = create_async_engine(
                self.settings.url,
                pool_size=self.settings.pool_size,
                max_overflow=self.settings.max_overflow,
                pool_timeout=self.settings.pool_timeout,
                pool_recycle=self.settings.pool_recycle,
                echo=self.settings.echo,
                # Additional async settings
                pool_pre_ping=True,
                pool_reset_on_return='commit',
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False,
            )
            
            # Test connection
            await self._test_connection()
            
            # Create tables if they don't exist
            await self._create_tables()
            
            self._initialized = True
            logger.info("Database connection initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize database", error=str(e))
            raise DatabaseError(f"Database initialization failed: {str(e)}")
    
    async def close(self) -> None:
        """Close database connection."""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False
            logger.info("Database connection closed")
    
    async def _test_connection(self) -> None:
        """Test database connection."""
        if not self.engine:
            raise DatabaseError("Database engine not initialized")
        
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                result.fetchone()
            logger.info("Database connection test successful")
        except Exception as e:
            logger.error("Database connection test failed", error=str(e))
            raise DatabaseError(f"Database connection test failed: {str(e)}")
    
    async def _create_tables(self) -> None:
        """Create database tables."""
        if not self.engine:
            raise DatabaseError("Database engine not initialized")
        
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error("Failed to create database tables", error=str(e))
            raise DatabaseError(f"Failed to create database tables: {str(e)}")
    
    def get_session(self) -> AsyncSession:
        """Get database session."""
        if not self._initialized or not self.session_factory:
            raise DatabaseError("Database not initialized")
        return self.session_factory()
    
    @asynccontextmanager
    async def session_scope(self) -> AsyncGenerator[AsyncSession, None]:
        """Provide a transactional scope around a series of operations."""
        session = self.get_session()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    async def execute_raw_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute raw SQL query."""
        if not self.engine:
            raise DatabaseError("Database engine not initialized")
        
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text(query), params or {})
                return result
        except SQLAlchemyError as e:
            logger.error("Raw query execution failed", query=query, error=str(e))
            raise DatabaseError(f"Query execution failed: {str(e)}")
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get database connection statistics."""
        if not self.engine:
            return {"status": "not_initialized"}
        
        pool = self.engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check."""
        try:
            start_time = logger.info("Starting database health check")
            
            # Test basic connectivity
            async with self.session_scope() as session:
                result = await session.execute(text("SELECT 1 as health_check"))
                result.fetchone()
            
            # Get connection stats
            stats = await self.get_connection_stats()
            
            # Get table counts for basic validation
            async with self.session_scope() as session:
                tenant_count = await session.scalar(select(func.count(Tenant.id)))
                user_count = await session.scalar(select(func.count(User.id)))
                audit_count = await session.scalar(select(func.count(AuditLog.audit_id)))
            
            return {
                "status": "healthy",
                "connection_stats": stats,
                "table_counts": {
                    "tenants": tenant_count,
                    "users": user_count,
                    "audit_logs": audit_count,
                },
                "response_time_ms": (logger.info("Database health check completed") - start_time) * 1000,
            }
            
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
            }


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if not _db_manager:
        raise DatabaseError("Database manager not initialized")
    return _db_manager


def set_database_manager(manager: DatabaseManager) -> None:
    """Set the global database manager instance."""
    global _db_manager
    _db_manager = manager


async def get_database() -> AsyncSession:
    """Dependency to get database session."""
    manager = get_database_manager()
    return manager.get_session()


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session with automatic cleanup."""
    manager = get_database_manager()
    async with manager.session_scope() as session:
        yield session


# Repository base class for common database operations
class BaseRepository:
    """Base repository class with common database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, obj: Any) -> Any:
        """Create a new record."""
        try:
            self.session.add(obj)
            await self.session.flush()
            await self.session.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            logger.error("Failed to create record", error=str(e))
            raise DatabaseError(f"Failed to create record: {str(e)}")
    
    async def get_by_id(self, model_class: Any, id_value: Any) -> Optional[Any]:
        """Get record by ID."""
        try:
            result = await self.session.get(model_class, id_value)
            return result
        except SQLAlchemyError as e:
            logger.error("Failed to get record by ID", model=model_class.__name__, id=id_value, error=str(e))
            raise DatabaseError(f"Failed to get record: {str(e)}")
    
    async def update(self, obj: Any, **kwargs) -> Any:
        """Update a record."""
        try:
            for key, value in kwargs.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            
            await self.session.flush()
            await self.session.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            logger.error("Failed to update record", error=str(e))
            raise DatabaseError(f"Failed to update record: {str(e)}")
    
    async def delete(self, obj: Any) -> None:
        """Delete a record."""
        try:
            await self.session.delete(obj)
            await self.session.flush()
        except SQLAlchemyError as e:
            logger.error("Failed to delete record", error=str(e))
            raise DatabaseError(f"Failed to delete record: {str(e)}")
    
    async def list_with_pagination(
        self,
        query: Any,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """Execute query with pagination."""
        try:
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_count = await self.session.scalar(count_query)
            
            # Apply pagination
            offset = (page - 1) * page_size
            paginated_query = query.offset(offset).limit(page_size)
            
            # Execute query
            result = await self.session.execute(paginated_query)
            items = result.scalars().all()
            
            # Calculate pagination info
            total_pages = (total_count + page_size - 1) // page_size
            has_next = page < total_pages
            has_previous = page > 1
            
            return {
                "items": items,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_previous": has_previous,
            }
            
        except SQLAlchemyError as e:
            logger.error("Failed to execute paginated query", error=str(e))
            raise DatabaseError(f"Failed to execute query: {str(e)}")


# Utility functions for database operations
async def create_partition_if_not_exists(partition_date: str) -> None:
    """Create audit log partition for the given date if it doesn't exist."""
    manager = get_database_manager()
    
    partition_name = f"audit_logs_{partition_date.replace('-', '_')}"
    start_date = partition_date
    end_date = f"DATE '{partition_date}' + INTERVAL '1 month'"
    
    create_partition_sql = f"""
    CREATE TABLE IF NOT EXISTS {partition_name} PARTITION OF audit_logs
    FOR VALUES FROM ('{start_date}') TO ({end_date});
    """
    
    try:
        await manager.execute_raw_query(create_partition_sql)
        logger.info("Created partition", partition_name=partition_name)
    except Exception as e:
        logger.error("Failed to create partition", partition_name=partition_name, error=str(e))
        # Don't raise exception as partition might already exist


async def cleanup_old_partitions(retention_months: int = 12) -> List[str]:
    """Clean up old audit log partitions based on retention policy."""
    manager = get_database_manager()
    
    # Get list of partitions older than retention period
    query = """
    SELECT schemaname, tablename 
    FROM pg_tables 
    WHERE tablename LIKE 'audit_logs_%'
    AND tablename < 'audit_logs_' || TO_CHAR(CURRENT_DATE - INTERVAL '%s months', 'YYYY_MM')
    """
    
    try:
        result = await manager.execute_raw_query(query, {"months": retention_months})
        old_partitions = result.fetchall()
        
        dropped_partitions = []
        for partition in old_partitions:
            partition_name = partition.tablename
            drop_sql = f"DROP TABLE IF EXISTS {partition_name}"
            
            try:
                await manager.execute_raw_query(drop_sql)
                dropped_partitions.append(partition_name)
                logger.info("Dropped old partition", partition_name=partition_name)
            except Exception as e:
                logger.error("Failed to drop partition", partition_name=partition_name, error=str(e))
        
        return dropped_partitions
        
    except Exception as e:
        logger.error("Failed to cleanup old partitions", error=str(e))
        return []