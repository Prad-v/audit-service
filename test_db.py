#!/usr/bin/env python3
"""
Simple database test script.
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

async def test_database():
    """Test database connection."""
    try:
        from app.db.database import get_database_manager
        
        print("Testing database connection...")
        db = get_database_manager()
        await db.initialize()
        print("✅ Database initialized successfully")
        
        # Test a simple query
        async with db.get_session() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            print("✅ Database query executed successfully")
        
        await db.close()
        print("✅ Database connection closed")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_database())
