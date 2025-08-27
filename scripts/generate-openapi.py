#!/usr/bin/env python3
"""
Generate OpenAPI specification from FastAPI application.

This script generates the OpenAPI JSON specification that can be used
to create client SDKs and documentation.
"""

import json
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.main import app


def generate_openapi_spec():
    """Generate and save the OpenAPI specification."""
    try:
        # Get the OpenAPI schema from FastAPI
        openapi_schema = app.openapi()
        
        # Enhance the schema with additional information
        openapi_schema["info"]["title"] = "Audit Log Framework API"
        openapi_schema["info"]["description"] = """
# Audit Log Framework API

A high-performance, multi-tenant audit logging system with comprehensive event tracking,
advanced filtering, and real-time processing capabilities.

## Features

- **Multi-tenant Architecture**: Complete tenant isolation and RBAC
- **High Performance**: Handle 1M+ events per day with async processing
- **Advanced Filtering**: 12+ filter types with full-text search
- **Real-time Processing**: NATS-based event streaming
- **Export Capabilities**: JSON/CSV export with up to 100k records
- **Authentication**: JWT tokens and API keys support
- **Caching**: Redis-based query result caching

## Authentication

The API supports two authentication methods:

### JWT Bearer Token
```
Authorization: Bearer <jwt_token>
```

### API Key
```
X-API-Key: <api_key>
X-Tenant-ID: <tenant_id>
```

## Rate Limits

- **Write Operations**: 1000 requests/minute
- **Read Operations**: 300 requests/minute  
- **Export Operations**: 10 requests/minute
- **Batch Operations**: 100 requests/minute

## Error Handling

All endpoints return structured error responses:

```json
{
  "error": "error_code",
  "message": "Human readable error message",
  "details": {}
}
```

## Pagination

List endpoints support pagination with the following parameters:

- `page`: Page number (default: 1)
- `size`: Page size (default: 50, max: 1000)

Response includes pagination metadata:

```json
{
  "items": [...],
  "total": 1000,
  "page": 1,
  "size": 50,
  "pages": 20
}
```
        """.strip()
        
        openapi_schema["info"]["version"] = "1.0.0"
        openapi_schema["info"]["contact"] = {
            "name": "Audit Log Framework",
            "url": "https://github.com/your-org/audit-log-framework",
            "email": "support@yourcompany.com"
        }
        
        openapi_schema["info"]["license"] = {
            "name": "Apache 2.0",
            "url": "https://www.apache.org/licenses/LICENSE-2.0.html"
        }
        
        # Add server information
        openapi_schema["servers"] = [
            {
                "url": "http://localhost:8000",
                "description": "Local development server"
            },
            {
                "url": "https://api.yourcompany.com",
                "description": "Production server"
            }
        ]
        
        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT token obtained from /api/v1/auth/login"
            },
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API key for programmatic access"
            },
            "TenantHeader": {
                "type": "apiKey",
                "in": "header", 
                "name": "X-Tenant-ID",
                "description": "Tenant ID (required when using API key)"
            }
        }
        
        # Add global security requirements
        openapi_schema["security"] = [
            {"BearerAuth": []},
            {"ApiKeyAuth": [], "TenantHeader": []}
        ]
        
        # Add tags for better organization
        openapi_schema["tags"] = [
            {
                "name": "Authentication",
                "description": "User authentication and token management"
            },
            {
                "name": "Audit Logs", 
                "description": "Audit log creation, querying, and management"
            },
            {
                "name": "Health",
                "description": "System health and status endpoints"
            }
        ]
        
        # Save the OpenAPI specification
        output_dir = Path(__file__).parent.parent / "docs" / "api"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save as JSON
        json_file = output_dir / "openapi.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(openapi_schema, f, indent=2, ensure_ascii=False)
        
        # Save as YAML (for better readability)
        yaml_file = output_dir / "openapi.yaml"
        try:
            import yaml
            with open(yaml_file, "w", encoding="utf-8") as f:
                yaml.dump(openapi_schema, f, default_flow_style=False, allow_unicode=True)
        except ImportError:
            print("PyYAML not installed, skipping YAML output")
        
        print(f"✅ OpenAPI specification generated successfully!")
        print(f"📄 JSON: {json_file}")
        if yaml_file.exists():
            print(f"📄 YAML: {yaml_file}")
        
        # Print some statistics
        paths_count = len(openapi_schema.get("paths", {}))
        components_count = len(openapi_schema.get("components", {}).get("schemas", {}))
        
        print(f"\n📊 API Statistics:")
        print(f"   • {paths_count} endpoints")
        print(f"   • {components_count} data models")
        print(f"   • Authentication: JWT + API Key")
        print(f"   • Multi-tenant: ✅")
        print(f"   • Rate Limited: ✅")
        
        return openapi_schema
        
    except Exception as e:
        print(f"❌ Failed to generate OpenAPI specification: {e}")
        sys.exit(1)


if __name__ == "__main__":
    generate_openapi_spec()