#!/usr/bin/env python3
"""
Initialize authentication data for the audit log framework.

This script creates a default tenant and admin user for development and testing.
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.config import get_settings
from app.core.security import hash_password
from app.db.database import get_database_manager
from app.db.schemas import Tenant, User
from app.models.auth import UserRole
from datetime import datetime, timezone
from uuid import uuid4

settings = get_settings()


async def create_default_tenant():
    """Create a default tenant for development."""
    db_manager = get_database_manager()
    
    try:
        await db_manager.initialize()
        
        async with db_manager.get_session() as session:
            # Check if default tenant already exists
            from sqlalchemy import select
            stmt = select(Tenant).where(Tenant.name == "Default Organization")
            result = await session.execute(stmt)
            existing_tenant = result.scalar_one_or_none()
            
            if existing_tenant:
                print(f"Default tenant already exists: {existing_tenant.id}")
                return existing_tenant.id
            
            # Create default tenant
            tenant_id = str(uuid4())
            tenant = Tenant(
                id=tenant_id,
                name="Default Organization",
                description="Default tenant for development and testing",
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            
            session.add(tenant)
            await session.commit()
            await session.refresh(tenant)
            
            print(f"Created default tenant: {tenant_id}")
            return tenant_id
            
    except Exception as e:
        print(f"Error creating default tenant: {e}")
        raise
    finally:
        await db_manager.close()


async def create_admin_user(tenant_id: str):
    """Create a default admin user."""
    db_manager = get_database_manager()
    
    try:
        await db_manager.initialize()
        
        async with db_manager.get_session() as session:
            # Check if admin user already exists
            from sqlalchemy import select
            stmt = select(User).where(
                User.username == "admin",
                User.tenant_id == tenant_id
            )
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"Admin user already exists: {existing_user.id}")
                return existing_user.id
            
            # Create admin user
            user_id = str(uuid4())
            password_hash = hash_password("admin123")  # Default password
            
            user = User(
                id=user_id,
                tenant_id=tenant_id,
                username="admin",
                email="admin@example.com",
                full_name="System Administrator",
                password_hash=password_hash,
                roles=[UserRole.SYSTEM_ADMIN, UserRole.TENANT_ADMIN],
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            print(f"Created admin user: {user_id}")
            print("Username: admin")
            print("Password: admin123")
            print("⚠️  Please change the default password in production!")
            
            return user_id
            
    except Exception as e:
        print(f"Error creating admin user: {e}")
        raise
    finally:
        await db_manager.close()


async def create_test_user(tenant_id: str):
    """Create a test user with limited permissions."""
    db_manager = get_database_manager()
    
    try:
        await db_manager.initialize()
        
        async with db_manager.get_session() as session:
            # Check if test user already exists
            from sqlalchemy import select
            stmt = select(User).where(
                User.username == "testuser",
                User.tenant_id == tenant_id
            )
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"Test user already exists: {existing_user.id}")
                return existing_user.id
            
            # Create test user
            user_id = str(uuid4())
            password_hash = hash_password("test123")  # Default password
            
            user = User(
                id=user_id,
                tenant_id=tenant_id,
                username="testuser",
                email="test@example.com",
                full_name="Test User",
                password_hash=password_hash,
                roles=[UserRole.AUDIT_VIEWER],
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            print(f"Created test user: {user_id}")
            print("Username: testuser")
            print("Password: test123")
            
            return user_id
            
    except Exception as e:
        print(f"Error creating test user: {e}")
        raise
    finally:
        await db_manager.close()


async def main():
    """Main initialization function."""
    print("🚀 Initializing authentication data...")
    
    try:
        # Create default tenant
        print("\n📁 Creating default tenant...")
        tenant_id = await create_default_tenant()
        
        # Create admin user
        print("\n👤 Creating admin user...")
        await create_admin_user(tenant_id)
        
        # Create test user
        print("\n🧪 Creating test user...")
        await create_test_user(tenant_id)
        
        print("\n✅ Authentication initialization completed successfully!")
        print(f"\nTenant ID: {tenant_id}")
        print("\nYou can now:")
        print("1. Start the API server: make dev")
        print("2. Login with admin credentials at /docs")
        print("3. Test the authentication endpoints")
        
    except Exception as e:
        print(f"\n❌ Initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())