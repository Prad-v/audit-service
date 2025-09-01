"""
Minimal test configuration for Event Processor tests

This file provides basic pytest configuration without complex imports
that could cause compatibility issues.
"""

import pytest
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Minimal pytest configuration
pytest_plugins = []


def pytest_configure(config):
    """Configure pytest for event processor tests."""
    config.addinivalue_line(
        "markers", "event_processor: marks tests as event processor tests"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark event processor tests."""
    for item in items:
        if "event_processor" in item.nodeid:
            item.add_marker(pytest.mark.event_processor)
