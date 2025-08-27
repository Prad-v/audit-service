"""
Security hardening configurations and utilities.

This module provides comprehensive security hardening features including
input validation, rate limiting, security headers, encryption, and
vulnerability protection for the audit logging system.
"""

import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

import structlog
from cryptography.fernet import Fernet
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from pydantic import BaseModel, validator

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class SecurityConfig(BaseModel):
    """Security configuration settings."""
    
    # Password policy
    min_password_length: int = 12
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special_chars: bool = True
    password_history_count: int = 5
    password_expiry_days: int = 90
    
    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst_size: int = 10
    rate_limit_window_seconds: int = 60
    
    # Session security
    session_timeout_minutes: int = 30
    max_concurrent_sessions: int = 5
    session_rotation_interval_minutes: int = 15
    
    # API security
    api_key_length: int = 32
    api_key_expiry_days: int = 365
    require_https: bool = True
    allowed_origins: List[str] = []
    
    # Input validation
    max_request_size_mb: int = 10
    max_json_depth: int = 10
    max_array_length: int = 1000
    max_string_length: int = 10000
    
    # Encryption
    encryption_algorithm: str = "AES-256-GCM"
    key_rotation_days: int = 90
    
    # Audit security
    log_failed_attempts: bool = True
    max_failed_attempts: int = 5
    lockout_duration_minutes: int = 15
    
    # Content security
    enable_content_security_policy: bool = True
    enable_hsts: bool = True
    enable_xss_protection: bool = True
    enable_content_type_nosniff: bool = True
    enable_frame_options: bool = True


class SecurityHeaders:
    """Security headers configuration."""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get comprehensive security headers."""
        headers = {}
        
        # Content Security Policy
        if settings.security_config.enable_content_security_policy:
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
                "style-src 'self' 'unsafe-inline'",
                "img-src 'self' data: https:",
                "font-src 'self' https:",
                "connect-src 'self' https:",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'"
            ]
            headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # HTTP Strict Transport Security
        if settings.security_config.enable_hsts:
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # XSS Protection
        if settings.security_config.enable_xss_protection:
            headers["X-XSS-Protection"] = "1; mode=block"
        
        # Content Type Options
        if settings.security_config.enable_content_type_nosniff:
            headers["X-Content-Type-Options"] = "nosniff"
        
        # Frame Options
        if settings.security_config.enable_frame_options:
            headers["X-Frame-Options"] = "DENY"
        
        # Additional security headers
        headers.update({
            "X-Permitted-Cross-Domain-Policies": "none",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Cache-Control": "no-store, no-cache, must-revalidate, private",
            "Pragma": "no-cache",
            "Expires": "0"
        })
        
        return headers


class InputValidator:
    """Input validation and sanitization."""
    
    @staticmethod
    def validate_json_structure(data: Any, max_depth: int = 10, current_depth: int = 0) -> bool:
        """Validate JSON structure depth and complexity."""
        if current_depth > max_depth:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"JSON structure too deep (max depth: {max_depth})"
            )
        
        if isinstance(data, dict):
            if len(data) > settings.security_config.max_array_length:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Object has too many keys (max: {settings.security_config.max_array_length})"
                )
            
            for key, value in data.items():
                if isinstance(key, str) and len(key) > settings.security_config.max_string_length:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Object key too long (max: {settings.security_config.max_string_length})"
                    )
                
                InputValidator.validate_json_structure(value, max_depth, current_depth + 1)
        
        elif isinstance(data, list):
            if len(data) > settings.security_config.max_array_length:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Array too long (max: {settings.security_config.max_array_length})"
                )
            
            for item in data:
                InputValidator.validate_json_structure(item, max_depth, current_depth + 1)
        
        elif isinstance(data, str):
            if len(data) > settings.security_config.max_string_length:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"String too long (max: {settings.security_config.max_string_length})"
                )
        
        return True
    
    @staticmethod
    def sanitize_string(value: str) -> str:
        """Sanitize string input to prevent injection attacks."""
        if not isinstance(value, str):
            return str(value)
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Limit length
        if len(value) > settings.security_config.max_string_length:
            value = value[:settings.security_config.max_string_length]
        
        # Remove potentially dangerous characters for SQL injection
        dangerous_chars = ['--', ';', '/*', '*/', 'xp_', 'sp_']
        for char in dangerous_chars:
            value = value.replace(char, '')
        
        return value.strip()
    
    @staticmethod
    def validate_tenant_id(tenant_id: str) -> str:
        """Validate and sanitize tenant ID."""
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant ID is required"
            )
        
        # Allow only alphanumeric characters, hyphens, and underscores
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', tenant_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant ID contains invalid characters"
            )
        
        if len(tenant_id) > 64:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant ID too long (max 64 characters)"
            )
        
        return tenant_id.lower()
    
    @staticmethod
    def validate_user_id(user_id: str) -> str:
        """Validate and sanitize user ID."""
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID is required"
            )
        
        # Allow alphanumeric characters, hyphens, underscores, and @ for emails
        import re
        if not re.match(r'^[a-zA-Z0-9_@.-]+$', user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID contains invalid characters"
            )
        
        if len(user_id) > 255:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID too long (max 255 characters)"
            )
        
        return user_id.lower()


class RateLimiter:
    """Rate limiting implementation."""
    
    def __init__(self):
        self._requests: Dict[str, List[float]] = {}
        self._blocked_ips: Dict[str, float] = {}
    
    def is_allowed(self, identifier: str, max_requests: int, window_seconds: int) -> bool:
        """Check if request is allowed based on rate limits."""
        current_time = time.time()
        
        # Check if IP is temporarily blocked
        if identifier in self._blocked_ips:
            if current_time < self._blocked_ips[identifier]:
                return False
            else:
                del self._blocked_ips[identifier]
        
        # Initialize request history for new identifiers
        if identifier not in self._requests:
            self._requests[identifier] = []
        
        # Clean old requests outside the window
        cutoff_time = current_time - window_seconds
        self._requests[identifier] = [
            req_time for req_time in self._requests[identifier]
            if req_time > cutoff_time
        ]
        
        # Check if limit exceeded
        if len(self._requests[identifier]) >= max_requests:
            # Block IP for lockout duration
            lockout_duration = settings.security_config.lockout_duration_minutes * 60
            self._blocked_ips[identifier] = current_time + lockout_duration
            
            logger.warning(
                "Rate limit exceeded",
                identifier=identifier,
                requests_count=len(self._requests[identifier]),
                max_requests=max_requests,
                window_seconds=window_seconds
            )
            
            return False
        
        # Add current request
        self._requests[identifier].append(current_time)
        return True
    
    def get_remaining_requests(self, identifier: str, max_requests: int) -> int:
        """Get remaining requests for identifier."""
        if identifier not in self._requests:
            return max_requests
        
        return max(0, max_requests - len(self._requests[identifier]))
    
    def reset_limits(self, identifier: str) -> None:
        """Reset rate limits for identifier."""
        if identifier in self._requests:
            del self._requests[identifier]
        if identifier in self._blocked_ips:
            del self._blocked_ips[identifier]


class PasswordValidator:
    """Password validation and strength checking."""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password strength according to policy."""
        errors = []
        config = settings.security_config
        
        # Length check
        if len(password) < config.min_password_length:
            errors.append(f"Password must be at least {config.min_password_length} characters long")
        
        # Character requirements
        if config.require_uppercase and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if config.require_lowercase and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if config.require_numbers and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        if config.require_special_chars and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")
        
        # Common password check
        if self._is_common_password(password):
            errors.append("Password is too common, please choose a different one")
        
        return len(errors) == 0, errors
    
    def _is_common_password(self, password: str) -> bool:
        """Check if password is in common passwords list."""
        common_passwords = {
            "password", "123456", "password123", "admin", "qwerty",
            "letmein", "welcome", "monkey", "1234567890", "password1"
        }
        return password.lower() in common_passwords
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return self.pwd_context.verify(plain_password, hashed_password)


class DataEncryption:
    """Data encryption and decryption utilities."""
    
    def __init__(self):
        self.encryption_key = self._get_or_create_key()
        self.cipher_suite = Fernet(self.encryption_key)
    
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key."""
        key_str = getattr(settings, 'encryption_key', None)
        if key_str:
            return key_str.encode()
        
        # Generate new key if not provided
        key = Fernet.generate_key()
        logger.warning(
            "No encryption key provided, generated new key. "
            "Store this key securely: %s", key.decode()
        )
        return key
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt string data."""
        if not data:
            return data
        
        encrypted_data = self.cipher_suite.encrypt(data.encode())
        return encrypted_data.decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt string data."""
        if not encrypted_data:
            return encrypted_data
        
        try:
            decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode())
            return decrypted_data.decode()
        except Exception as e:
            logger.error("Failed to decrypt data", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Data decryption failed"
            )
    
    def encrypt_sensitive_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive fields in data dictionary."""
        sensitive_fields = {'user_agent', 'ip_address', 'metadata'}
        
        encrypted_data = data.copy()
        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field]:
                if isinstance(encrypted_data[field], str):
                    encrypted_data[field] = self.encrypt_data(encrypted_data[field])
                elif isinstance(encrypted_data[field], dict):
                    encrypted_data[field] = self.encrypt_data(str(encrypted_data[field]))
        
        return encrypted_data
    
    def decrypt_sensitive_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive fields in data dictionary."""
        sensitive_fields = {'user_agent', 'ip_address', 'metadata'}
        
        decrypted_data = data.copy()
        for field in sensitive_fields:
            if field in decrypted_data and decrypted_data[field]:
                try:
                    decrypted_data[field] = self.decrypt_data(decrypted_data[field])
                    if field == 'metadata':
                        # Try to parse back to dict
                        import json
                        try:
                            decrypted_data[field] = json.loads(decrypted_data[field])
                        except json.JSONDecodeError:
                            pass  # Keep as string if not valid JSON
                except Exception:
                    # If decryption fails, data might not be encrypted
                    pass
        
        return decrypted_data


class SecurityAuditor:
    """Security auditing and monitoring."""
    
    def __init__(self):
        self.failed_attempts: Dict[str, List[datetime]] = {}
        self.suspicious_activities: List[Dict[str, Any]] = []
    
    def log_failed_authentication(self, identifier: str, request: Request) -> None:
        """Log failed authentication attempt."""
        if not settings.security_config.log_failed_attempts:
            return
        
        current_time = datetime.utcnow()
        
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = []
        
        self.failed_attempts[identifier].append(current_time)
        
        # Clean old attempts (older than 1 hour)
        cutoff_time = current_time - timedelta(hours=1)
        self.failed_attempts[identifier] = [
            attempt for attempt in self.failed_attempts[identifier]
            if attempt > cutoff_time
        ]
        
        # Check for brute force attempts
        max_attempts = settings.security_config.max_failed_attempts
        if len(self.failed_attempts[identifier]) >= max_attempts:
            self._log_suspicious_activity(
                "brute_force_attempt",
                identifier,
                request,
                {"failed_attempts": len(self.failed_attempts[identifier])}
            )
    
    def log_suspicious_request(self, request: Request, reason: str) -> None:
        """Log suspicious request activity."""
        client_ip = self._get_client_ip(request)
        self._log_suspicious_activity("suspicious_request", client_ip, request, {"reason": reason})
    
    def _log_suspicious_activity(
        self,
        activity_type: str,
        identifier: str,
        request: Request,
        metadata: Dict[str, Any]
    ) -> None:
        """Log suspicious activity."""
        activity = {
            "timestamp": datetime.utcnow().isoformat(),
            "activity_type": activity_type,
            "identifier": identifier,
            "ip_address": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", ""),
            "path": str(request.url.path),
            "method": request.method,
            "metadata": metadata
        }
        
        self.suspicious_activities.append(activity)
        
        # Keep only recent activities (last 1000)
        if len(self.suspicious_activities) > 1000:
            self.suspicious_activities = self.suspicious_activities[-1000:]
        
        logger.warning(
            "Suspicious activity detected",
            activity_type=activity_type,
            identifier=identifier,
            ip_address=activity["ip_address"],
            metadata=metadata
        )
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics and statistics."""
        current_time = datetime.utcnow()
        last_hour = current_time - timedelta(hours=1)
        last_day = current_time - timedelta(days=1)
        
        # Count recent failed attempts
        recent_failed_attempts = 0
        for attempts in self.failed_attempts.values():
            recent_failed_attempts += len([a for a in attempts if a > last_hour])
        
        # Count recent suspicious activities
        recent_suspicious = len([
            a for a in self.suspicious_activities
            if datetime.fromisoformat(a["timestamp"]) > last_hour
        ])
        
        daily_suspicious = len([
            a for a in self.suspicious_activities
            if datetime.fromisoformat(a["timestamp"]) > last_day
        ])
        
        return {
            "failed_attempts_last_hour": recent_failed_attempts,
            "suspicious_activities_last_hour": recent_suspicious,
            "suspicious_activities_last_day": daily_suspicious,
            "total_blocked_ips": len([
                ip for ip, attempts in self.failed_attempts.items()
                if len(attempts) >= settings.security_config.max_failed_attempts
            ]),
            "security_config": {
                "rate_limiting_enabled": settings.security_config.rate_limit_enabled,
                "max_failed_attempts": settings.security_config.max_failed_attempts,
                "session_timeout_minutes": settings.security_config.session_timeout_minutes,
                "require_https": settings.security_config.require_https
            }
        }


class APIKeyManager:
    """API key management and validation."""
    
    def __init__(self):
        self.active_keys: Dict[str, Dict[str, Any]] = {}
    
    def generate_api_key(self, tenant_id: str, description: str = "") -> Tuple[str, str]:
        """Generate new API key for tenant."""
        # Generate secure random key
        key_bytes = secrets.token_bytes(settings.security_config.api_key_length)
        api_key = key_bytes.hex()
        
        # Create key hash for storage
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Store key metadata
        expiry_date = datetime.utcnow() + timedelta(
            days=settings.security_config.api_key_expiry_days
        )
        
        self.active_keys[key_hash] = {
            "tenant_id": tenant_id,
            "description": description,
            "created_at": datetime.utcnow(),
            "expires_at": expiry_date,
            "last_used": None,
            "usage_count": 0,
            "is_active": True
        }
        
        logger.info(
            "API key generated",
            tenant_id=tenant_id,
            key_hash=key_hash[:8] + "...",
            expires_at=expiry_date
        )
        
        return api_key, key_hash
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate API key and return metadata."""
        if not api_key:
            return None
        
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        if key_hash not in self.active_keys:
            return None
        
        key_info = self.active_keys[key_hash]
        
        # Check if key is active
        if not key_info["is_active"]:
            return None
        
        # Check if key is expired
        if datetime.utcnow() > key_info["expires_at"]:
            key_info["is_active"] = False
            logger.warning("Expired API key used", key_hash=key_hash[:8] + "...")
            return None
        
        # Update usage statistics
        key_info["last_used"] = datetime.utcnow()
        key_info["usage_count"] += 1
        
        return key_info
    
    def revoke_api_key(self, key_hash: str) -> bool:
        """Revoke API key."""
        if key_hash in self.active_keys:
            self.active_keys[key_hash]["is_active"] = False
            logger.info("API key revoked", key_hash=key_hash[:8] + "...")
            return True
        return False
    
    def cleanup_expired_keys(self) -> int:
        """Clean up expired API keys."""
        current_time = datetime.utcnow()
        expired_keys = []
        
        for key_hash, key_info in self.active_keys.items():
            if current_time > key_info["expires_at"]:
                expired_keys.append(key_hash)
        
        for key_hash in expired_keys:
            del self.active_keys[key_hash]
        
        if expired_keys:
            logger.info("Cleaned up expired API keys", count=len(expired_keys))
        
        return len(expired_keys)


# Global instances
security_config = SecurityConfig()
rate_limiter = RateLimiter()
password_validator = PasswordValidator()
data_encryption = DataEncryption()
security_auditor = SecurityAuditor()
api_key_manager = APIKeyManager()


def get_security_config() -> SecurityConfig:
    """Get security configuration."""
    return security_config


def get_rate_limiter() -> RateLimiter:
    """Get rate limiter instance."""
    return rate_limiter


def get_password_validator() -> PasswordValidator:
    """Get password validator instance."""
    return password_validator


def get_data_encryption() -> DataEncryption:
    """Get data encryption instance."""
    return data_encryption


def get_security_auditor() -> SecurityAuditor:
    """Get security auditor instance."""
    return security_auditor


def get_api_key_manager() -> APIKeyManager:
    """Get API key manager instance."""
    return api_key_manager