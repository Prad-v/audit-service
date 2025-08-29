"""
Alert Engine Service

This module contains the alert engine that processes events and triggers alerts
based on configured policies.
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from uuid import uuid4

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.schemas import AlertPolicy, AlertProvider, Alert, AlertThrottle, AlertSuppression
from app.models.alert import AlertRule, AlertSeverity, AlertStatus, AlertProviderType
from app.services.providers import create_provider

logger = logging.getLogger(__name__)


class AlertEngine:
    """Alert engine for processing events and triggering alerts"""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    async def process_event(self, event_data: Dict[str, Any], tenant_id: str) -> List[Dict[str, Any]]:
        """Process an event and trigger alerts based on matching policies"""
        try:
            # Get all enabled policies for the tenant
            policies = await self._get_enabled_policies(tenant_id)
            
            triggered_alerts = []
            
            for policy in policies:
                # Check if policy matches the event
                if await self._policy_matches_event(policy, event_data):
                    # Check if alert should be throttled
                    if await self._should_throttle_alert(policy):
                        logger.info(f"Alert throttled for policy {policy.policy_id}")
                        continue
                    
                    # Check if alert should be suppressed
                    if await self._is_alert_suppressed(policy, event_data):
                        logger.info(f"Alert suppressed for policy {policy.policy_id}")
                        continue
                    
                    # Create and send alert
                    alert_result = await self._create_and_send_alert(policy, event_data, tenant_id)
                    if alert_result:
                        triggered_alerts.append(alert_result)
            
            return triggered_alerts
            
        except Exception as e:
            logger.error(f"Error processing event: {e}")
            return []
    
    async def _get_enabled_policies(self, tenant_id: str) -> List[AlertPolicy]:
        """Get all enabled policies for a tenant"""
        result = await self.db_session.execute(
            select(AlertPolicy)
            .where(and_(
                AlertPolicy.tenant_id == tenant_id,
                AlertPolicy.enabled == True
            ))
        )
        return result.scalars().all()
    
    async def _policy_matches_event(self, policy: AlertPolicy, event_data: Dict[str, Any]) -> bool:
        """Check if a policy matches the event data"""
        try:
            # Parse rules from JSON
            rules_data = policy.rules if isinstance(policy.rules, list) else json.loads(policy.rules)
            rules = [AlertRule(**rule) for rule in rules_data]
            
            # Check time window if configured
            if policy.time_window:
                if not self._is_within_time_window(policy.time_window):
                    return False
            
            # Evaluate rules
            rule_results = []
            for rule in rules:
                rule_result = self._evaluate_rule(rule, event_data)
                rule_results.append(rule_result)
            
            # Apply match logic (AND/OR)
            if policy.match_all:
                return all(rule_results)
            else:
                return any(rule_results)
                
        except Exception as e:
            logger.error(f"Error evaluating policy {policy.policy_id}: {e}")
            return False
    
    def _evaluate_rule(self, rule: AlertRule, event_data: Dict[str, Any]) -> bool:
        """Evaluate a single rule against event data"""
        try:
            # Get field value from event data
            field_value = self._get_nested_value(event_data, rule.field)
            
            if field_value is None:
                return False
            
            # Apply operator
            if rule.operator == "eq":
                return self._compare_values(field_value, rule.value, rule.case_sensitive) == 0
            elif rule.operator == "ne":
                return self._compare_values(field_value, rule.value, rule.case_sensitive) != 0
            elif rule.operator == "gt":
                return self._compare_values(field_value, rule.value, rule.case_sensitive) > 0
            elif rule.operator == "lt":
                return self._compare_values(field_value, rule.value, rule.case_sensitive) < 0
            elif rule.operator == "gte":
                return self._compare_values(field_value, rule.value, rule.case_sensitive) >= 0
            elif rule.operator == "lte":
                return self._compare_values(field_value, rule.value, rule.case_sensitive) <= 0
            elif rule.operator == "in":
                return field_value in rule.value
            elif rule.operator == "not_in":
                return field_value not in rule.value
            elif rule.operator == "contains":
                if isinstance(field_value, str) and isinstance(rule.value, str):
                    if rule.case_sensitive:
                        return rule.value in field_value
                    else:
                        return rule.value.lower() in field_value.lower()
                return False
            elif rule.operator == "regex":
                if isinstance(field_value, str) and isinstance(rule.value, str):
                    try:
                        pattern = re.compile(rule.value, re.IGNORECASE if not rule.case_sensitive else 0)
                        return pattern.search(field_value) is not None
                    except re.error:
                        logger.error(f"Invalid regex pattern: {rule.value}")
                        return False
                return False
            else:
                logger.error(f"Unknown operator: {rule.operator}")
                return False
                
        except Exception as e:
            logger.error(f"Error evaluating rule {rule.field} {rule.operator} {rule.value}: {e}")
            return False
    
    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get nested value from dictionary using dot notation"""
        try:
            keys = field_path.split('.')
            value = data
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return None
            
            return value
        except Exception:
            return None
    
    def _compare_values(self, value1: Any, value2: Any, case_sensitive: bool = True) -> int:
        """Compare two values, returning -1, 0, or 1"""
        try:
            # Handle string comparison
            if isinstance(value1, str) and isinstance(value2, str):
                if not case_sensitive:
                    value1 = value1.lower()
                    value2 = value2.lower()
                return (value1 > value2) - (value1 < value2)
            
            # Handle numeric comparison
            if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
                return (value1 > value2) - (value1 < value2)
            
            # Handle boolean comparison
            if isinstance(value1, bool) and isinstance(value2, bool):
                return (value1 > value2) - (value1 < value2)
            
            # Default string comparison
            str1 = str(value1)
            str2 = str(value2)
            if not case_sensitive:
                str1 = str1.lower()
                str2 = str2.lower()
            return (str1 > str2) - (str1 < str2)
            
        except Exception:
            return 0
    
    def _is_within_time_window(self, time_window: Dict[str, Any]) -> bool:
        """Check if current time is within the policy time window"""
        try:
            from datetime import time
            import pytz
            
            # Parse time window
            start_time = time.fromisoformat(time_window["start_time"])
            end_time = time.fromisoformat(time_window["end_time"])
            days_of_week = time_window.get("days_of_week", [0, 1, 2, 3, 4, 5, 6])
            timezone_str = time_window.get("timezone", "UTC")
            
            # Get current time in specified timezone
            tz = pytz.timezone(timezone_str)
            now = datetime.now(tz)
            current_time = now.time()
            current_day = now.weekday()  # 0=Monday, 6=Sunday
            
            # Check day of week
            if current_day not in days_of_week:
                return False
            
            # Check time range
            if start_time <= end_time:
                # Same day range (e.g., 09:00 to 17:00)
                return start_time <= current_time <= end_time
            else:
                # Overnight range (e.g., 22:00 to 06:00)
                return current_time >= start_time or current_time <= end_time
                
        except Exception as e:
            logger.error(f"Error checking time window: {e}")
            return True  # Default to allowing if time window check fails
    
    async def _should_throttle_alert(self, policy: AlertPolicy) -> bool:
        """Check if alert should be throttled based on policy settings"""
        try:
            if policy.throttle_minutes <= 0 and policy.max_alerts_per_hour <= 0:
                return False
            
            now = datetime.utcnow()
            
            # Check throttle minutes
            if policy.throttle_minutes > 0:
                last_alert = await self._get_last_alert_time(policy.policy_id)
                if last_alert and (now - last_alert).total_seconds() < policy.throttle_minutes * 60:
                    return True
            
            # Check max alerts per hour
            if policy.max_alerts_per_hour > 0:
                hour_start = now.replace(minute=0, second=0, microsecond=0)
                alert_count = await self._get_alert_count_in_hour(policy.policy_id, hour_start)
                if alert_count >= policy.max_alerts_per_hour:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking alert throttling: {e}")
            return False
    
    async def _get_last_alert_time(self, policy_id: str) -> Optional[datetime]:
        """Get the last alert time for a policy"""
        result = await self.db_session.execute(
            select(Alert.triggered_at)
            .where(Alert.policy_id == policy_id)
            .order_by(Alert.triggered_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def _get_alert_count_in_hour(self, policy_id: str, hour_start: datetime) -> int:
        """Get alert count for a policy in the current hour"""
        result = await self.db_session.execute(
            select(func.count(Alert.alert_id))
            .where(and_(
                Alert.policy_id == policy_id,
                Alert.triggered_at >= hour_start
            ))
        )
        return result.scalar() or 0
    
    async def _is_alert_suppressed(self, policy: AlertPolicy, event_data: Dict[str, Any]) -> bool:
        """Check if alert is suppressed"""
        try:
            # Create suppression key based on event data
            suppression_key = self._create_suppression_key(policy, event_data)
            
            # Check for active suppression
            result = await self.db_session.execute(
                select(AlertSuppression)
                .where(and_(
                    AlertSuppression.policy_id == policy.policy_id,
                    AlertSuppression.suppression_key == suppression_key,
                    AlertSuppression.suppressed_until > datetime.utcnow()
                ))
            )
            
            return result.scalar_one_or_none() is not None
            
        except Exception as e:
            logger.error(f"Error checking alert suppression: {e}")
            return False
    
    def _create_suppression_key(self, policy: AlertPolicy, event_data: Dict[str, Any]) -> str:
        """Create a suppression key based on policy and event data"""
        # Use a combination of policy ID and key event fields
        key_parts = [policy.policy_id]
        
        # Add key fields from event data for suppression
        for field in ["user_id", "ip_address", "event_type", "service_name"]:
            if field in event_data:
                key_parts.append(f"{field}:{event_data[field]}")
        
        return "|".join(key_parts)
    
    async def _create_and_send_alert(self, policy: AlertPolicy, event_data: Dict[str, Any], tenant_id: str) -> Optional[Dict[str, Any]]:
        """Create and send an alert"""
        try:
            # Generate alert ID
            alert_id = f"alert-{uuid4().hex[:8]}"
            
            # Format alert message
            title = self._format_template(policy.message_template, event_data)
            summary = self._format_template(policy.summary_template, event_data)
            message = self._format_template(policy.message_template, event_data)
            
            # Create alert record
            alert = Alert(
                alert_id=alert_id,
                policy_id=policy.policy_id,
                severity=policy.severity,
                status=AlertStatus.ACTIVE,
                title=title,
                message=message,
                summary=summary,
                event_data=event_data,
                event_id=event_data.get("event_id"),
                triggered_at=datetime.utcnow(),
                tenant_id=tenant_id,
                delivery_status={}
            )
            
            self.db_session.add(alert)
            await self.db_session.commit()
            await self.db_session.refresh(alert)
            
            # Send to providers
            delivery_results = await self._send_to_providers(policy, alert, event_data)
            
            # Update delivery status
            alert.delivery_status = delivery_results
            await self.db_session.commit()
            
            return {
                "alert_id": alert_id,
                "policy_id": policy.policy_id,
                "severity": policy.severity,
                "title": title,
                "summary": summary,
                "delivery_results": delivery_results
            }
            
        except Exception as e:
            logger.error(f"Error creating and sending alert: {e}")
            return None
    
    def _format_template(self, template: str, event_data: Dict[str, Any]) -> str:
        """Format a template string with event data"""
        try:
            # Simple template formatting with {field} placeholders
            formatted = template
            
            for key, value in event_data.items():
                placeholder = f"{{{key}}}"
                if placeholder in formatted:
                    formatted = formatted.replace(placeholder, str(value))
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error formatting template: {e}")
            return template
    
    async def _send_to_providers(self, policy: AlertPolicy, alert: Alert, event_data: Dict[str, Any]) -> Dict[str, str]:
        """Send alert to all configured providers"""
        delivery_results = {}
        
        try:
            # Get provider IDs
            provider_ids = policy.providers if isinstance(policy.providers, list) else json.loads(policy.providers)
            
            # Get providers
            providers = await self._get_providers(provider_ids)
            
            # Send to each provider
            for provider in providers:
                try:
                    result = await self._send_to_provider(provider, alert, event_data)
                    delivery_results[provider.provider_id] = result.get("status", "failed")
                except Exception as e:
                    logger.error(f"Error sending to provider {provider.provider_id}: {e}")
                    delivery_results[provider.provider_id] = "failed"
            
        except Exception as e:
            logger.error(f"Error sending to providers: {e}")
        
        return delivery_results
    
    async def _get_providers(self, provider_ids: List[str]) -> List[AlertProvider]:
        """Get provider configurations"""
        result = await self.db_session.execute(
            select(AlertProvider)
            .where(and_(
                AlertProvider.provider_id.in_(provider_ids),
                AlertProvider.enabled == True
            ))
        )
        return result.scalars().all()
    
    async def _send_to_provider(self, provider: AlertProvider, alert: Alert, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send alert to a specific provider"""
        try:
            # Create provider instance
            provider_instance = create_provider(
                AlertProviderType(provider.provider_type),
                provider.config
            )
            
            # Prepare alert data
            alert_data = {
                "alert_id": alert.alert_id,
                "policy_id": alert.policy_id,
                "severity": alert.severity,
                "title": alert.title,
                "message": alert.message,
                "summary": alert.summary,
                "event_data": alert.event_data,
                "triggered_at": alert.triggered_at,
                "tenant_id": alert.tenant_id
            }
            
            # Send alert
            result = await provider_instance.send_alert(alert_data)
            return result
            
        except Exception as e:
            logger.error(f"Error sending to provider {provider.provider_id}: {e}")
            return {
                "success": False,
                "message": f"Error sending to provider: {str(e)}",
                "status": "failed"
            }
