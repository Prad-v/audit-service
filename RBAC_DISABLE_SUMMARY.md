# RBAC Disable Functionality Summary

## Overview
The audit service now supports disabling RBAC (Role-Based Access Control) using environment variables. This allows for easier development, testing, and debugging by bypassing authentication and authorization requirements.

## Environment Variables

### RBAC_AUTHENTICATION_DISABLED
- **Purpose**: Disables authentication requirements
- **Default**: `false`
- **When `true`**: 
  - No login required for any endpoint
  - All requests are treated as authenticated with system defaults
  - User context: `system` user with `system_admin` role

### RBAC_AUTHORIZATION_DISABLED
- **Purpose**: Disables authorization/permission checks
- **Default**: `false`
- **When `true`**:
  - No permission checks are performed
  - All users have access to all endpoints
  - Role-based restrictions are bypassed

## Configuration

### Current Configuration (RBAC Disabled)
```yaml
# docker-compose.yml
environment:
  - RBAC_AUTHENTICATION_DISABLED=true
  - RBAC_AUTHORIZATION_DISABLED=true
```

### To Re-enable RBAC
```yaml
# docker-compose.yml
environment:
  - RBAC_AUTHENTICATION_DISABLED=false
  - RBAC_AUTHORIZATION_DISABLED=false
```

Then restart the service:
```bash
docker-compose restart api
```

## Default Credentials

When RBAC is enabled, you can use these default credentials:

### Admin User
- **Username**: `admin`
- **Password**: `admin123`
- **Roles**: `SYSTEM_ADMIN`, `TENANT_ADMIN`
- **Email**: `admin@example.com`

### Test User
- **Username**: `testuser`
- **Password**: `test123`
- **Roles**: `AUDIT_VIEWER`
- **Email**: `test@example.com`

⚠️ **Important**: Change these default passwords in production!

## Swagger Documentation

### Swagger UI
- **URL**: http://localhost:8000/docs
- **Status**: ✅ Accessible when `DEBUG=true`

### OpenAPI Schema
- **URL**: http://localhost:8000/openapi.json
- **Status**: ✅ Accessible when `DEBUG=true`

## API Endpoints

### Public Endpoints (Always Accessible)
- `GET /health/` - Health check
- `GET /health/ready` - Readiness check
- `GET /health/live` - Liveness check
- `GET /health/detailed` - Detailed health status
- `GET /docs` - Swagger UI (when debug enabled)
- `GET /openapi.json` - OpenAPI schema (when debug enabled)

### Protected Endpoints (Require Authentication when RBAC enabled)
- `GET /api/v1/audit/events` - List audit events
- `GET /api/v1/audit/events/{audit_id}` - Get specific audit event
- `POST /api/v1/audit/events` - Create audit event
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/login` - User login
- And many more...

## Testing the Functionality

### With RBAC Disabled
```bash
# Test health endpoint
curl http://localhost:8000/health/

# Test protected endpoint (should work without auth)
curl http://localhost:8000/api/v1/audit/events

# Test Swagger docs
curl http://localhost:8000/docs
```

### With RBAC Enabled
```bash
# Test protected endpoint (should require auth)
curl http://localhost:8000/api/v1/audit/events
# Returns: 401 Unauthorized

# Login to get token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Use token for authenticated requests
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/audit/events
```

## Implementation Details

### Middleware Changes
The authentication middleware (`backend/app/api/middleware.py`) has been updated to:

1. **Check RBAC settings** before authentication
2. **Set default user context** when authentication is disabled:
   - `user_id`: "system"
   - `username`: "system"
   - `tenant_id`: "default"
   - `roles`: ["system_admin"]
   - `permissions`: ["*"]

3. **Skip permission checks** when authorization is disabled

### Configuration Changes
The settings (`backend/app/config.py`) now include:

```python
class RBACSettings(BaseSettings):
    authentication_disabled: bool = Field(default=False)
    authorization_disabled: bool = Field(default=False)
    
    class Config:
        env_prefix = "RBAC_"
```

## Security Considerations

1. **Development Only**: RBAC disable should only be used in development/testing environments
2. **Production**: Always enable RBAC in production with proper authentication
3. **Default Passwords**: Change default passwords before deploying to production
4. **Environment Variables**: Use secure methods to manage environment variables in production

## Troubleshooting

### Common Issues

1. **Environment variables not picked up**
   - Solution: Restart the container completely (`docker-compose down && docker-compose up -d`)

2. **Swagger docs not accessible**
   - Solution: Ensure `DEBUG=true` is set in environment variables

3. **Authentication still required**
   - Solution: Check that both `RBAC_AUTHENTICATION_DISABLED=true` and `RBAC_AUTHORIZATION_DISABLED=true` are set

### Verification Commands

```bash
# Check current RBAC settings
docker-compose exec api python -c "
from app.config import get_settings; 
s = get_settings(); 
print(f'Auth disabled: {s.rbac.authentication_disabled}'); 
print(f'Authz disabled: {s.rbac.authorization_disabled}')
"

# Check environment variables
docker-compose exec api env | grep RBAC

# Test endpoint accessibility
curl -v http://localhost:8000/api/v1/audit/events
```
