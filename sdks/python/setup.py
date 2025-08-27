#!/usr/bin/env python3
"""
Setup script for the Audit Log Framework Python SDK.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(requirements_path):
        with open(requirements_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return [
        "httpx>=0.24.0",
        "dataclasses-json>=0.5.7",
    ]

setup(
    name="audit-log-sdk",
    version="1.0.0",
    author="Audit Log Framework Team",
    author_email="support@yourcompany.com",
    description="Python SDK for the Audit Log Framework API",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourcompany/audit-service",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Logging",
        "Topic :: System :: Monitoring",
        "Topic :: Security",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "sphinx-autodoc-typehints>=1.22.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "audit-log-cli=audit_log_sdk.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "audit",
        "logging",
        "compliance",
        "security",
        "monitoring",
        "api",
        "sdk",
        "async",
        "fastapi",
    ],
    project_urls={
        "Bug Reports": "https://github.com/yourcompany/audit-service/issues",
        "Source": "https://github.com/yourcompany/audit-service",
        "Documentation": "https://audit-service.readthedocs.io/",
    },
)