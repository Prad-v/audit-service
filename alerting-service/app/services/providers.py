"""
Alert Provider Implementations

This module contains implementations for different alert providers:
- PagerDuty
- Slack
- Webhook
- Email
"""

import asyncio
import json
import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import httpx
import smtplib
from pydantic import BaseModel, ValidationError

from app.models.alert import AlertProviderType, AlertSeverity

logger = logging.getLogger(__name__)


class ProviderConfig(BaseModel):
    """Base configuration for alert providers"""
    pass


class PagerDutyConfig(ProviderConfig):
    """PagerDuty configuration"""
    api_key: str
    service_id: str
    urgency: str = "high"
    severity_map: Dict[str, str] = {
        "critical": "critical",
        "high": "high", 
        "medium": "high",
        "low": "low",
        "info": "low"
    }


class SlackConfig(ProviderConfig):
    """Slack configuration"""
    webhook_url: str
    channel: Optional[str] = None
    username: Optional[str] = None
    icon_emoji: Optional[str] = None
    severity_colors: Dict[str, str] = {
        "critical": "#FF0000",
        "high": "#FF6B35", 
        "medium": "#FFA500",
        "low": "#FFFF00",
        "info": "#00FF00"
    }


class WebhookConfig(ProviderConfig):
    """Webhook configuration"""
    url: str
    method: str = "POST"
    headers: Dict[str, str] = {}
    timeout: int = 30
    retry_count: int = 3


class EmailConfig(ProviderConfig):
    """Email configuration"""
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    use_tls: bool = True
    from_email: str
    to_emails: List[str]
    subject_template: str = "Alert: {severity} - {summary}"


class AlertProvider:
    """Base class for alert providers"""
    
    def __init__(self, provider_type: AlertProviderType, config: Dict[str, Any]):
        self.provider_type = provider_type
        self.config = self._validate_config(config)
    
    def _validate_config(self, config: Dict[str, Any]) -> ProviderConfig:
        """Validate provider configuration"""
        raise NotImplementedError
    
    async def send_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send alert to the provider"""
        raise NotImplementedError
    
    def _format_message(self, alert_data: Dict[str, Any]) -> str:
        """Format alert message for the provider"""
        severity = alert_data.get("severity", "medium")
        title = alert_data.get("title", "Alert")
        message = alert_data.get("message", "")
        summary = alert_data.get("summary", "")
        
        return f"""
**{severity.upper()} Alert: {title}**

{message}

**Summary:** {summary}

**Triggered:** {alert_data.get('triggered_at', datetime.utcnow())}
**Policy:** {alert_data.get('policy_id', 'Unknown')}
        """.strip()


class PagerDutyProvider(AlertProvider):
    """PagerDuty alert provider"""
    
    def _validate_config(self, config: Dict[str, Any]) -> PagerDutyConfig:
        return PagerDutyConfig(**config)
    
    async def send_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send alert to PagerDuty"""
        try:
            config = self.config
            
            # Map severity
            severity = alert_data.get("severity", "medium")
            pagerduty_severity = config.severity_map.get(severity, "high")
            
            # Prepare payload
            payload = {
                "routing_key": config.api_key,
                "event_action": "trigger",
                "payload": {
                    "summary": alert_data.get("summary", "Alert triggered"),
                    "severity": pagerduty_severity,
                    "source": "audit-log-framework",
                    "custom_details": {
                        "title": alert_data.get("title", ""),
                        "message": alert_data.get("message", ""),
                        "policy_id": alert_data.get("policy_id", ""),
                        "event_data": alert_data.get("event_data", {}),
                        "triggered_at": alert_data.get("triggered_at", "").isoformat() if alert_data.get("triggered_at") else None
                    }
                },
                "client": "Audit Log Framework",
                "client_url": "https://github.com/audit-log-framework"
            }
            
            # Send to PagerDuty
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://events.pagerduty.com/v2/enqueue",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 202:
                    result = response.json()
                    return {
                        "success": True,
                        "message": "Alert sent to PagerDuty",
                        "incident_key": result.get("dedup_key"),
                        "status": "sent"
                    }
                else:
                    logger.error(f"PagerDuty API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "message": f"PagerDuty API error: {response.status_code}",
                        "status": "failed"
                    }
                    
        except Exception as e:
            logger.error(f"Error sending alert to PagerDuty: {e}")
            return {
                "success": False,
                "message": f"Error sending alert to PagerDuty: {str(e)}",
                "status": "failed"
            }


class SlackProvider(AlertProvider):
    """Slack alert provider"""
    
    def _validate_config(self, config: Dict[str, Any]) -> SlackConfig:
        return SlackConfig(**config)
    
    async def send_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send alert to Slack"""
        try:
            config = self.config
            
            # Get severity color
            severity = alert_data.get("severity", "medium")
            color = config.severity_colors.get(severity, "#000000")
            
            # Prepare Slack message
            message = {
                "text": f"*{severity.upper()} Alert: {alert_data.get('title', 'Alert')}*",
                "attachments": [
                    {
                        "color": color,
                        "fields": [
                            {
                                "title": "Summary",
                                "value": alert_data.get("summary", ""),
                                "short": False
                            },
                            {
                                "title": "Message",
                                "value": alert_data.get("message", ""),
                                "short": False
                            },
                            {
                                "title": "Policy ID",
                                "value": alert_data.get("policy_id", ""),
                                "short": True
                            },
                            {
                                "title": "Triggered At",
                                "value": alert_data.get("triggered_at", "").isoformat() if alert_data.get("triggered_at") else "Unknown",
                                "short": True
                            }
                        ],
                        "footer": "Audit Log Framework",
                        "ts": int(datetime.utcnow().timestamp())
                    }
                ]
            }
            
            # Add optional fields
            if config.channel:
                message["channel"] = config.channel
            if config.username:
                message["username"] = config.username
            if config.icon_emoji:
                message["icon_emoji"] = config.icon_emoji
            
            # Send to Slack
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    config.webhook_url,
                    json=message,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "message": "Alert sent to Slack",
                        "status": "sent"
                    }
                else:
                    logger.error(f"Slack API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "message": f"Slack API error: {response.status_code}",
                        "status": "failed"
                    }
                    
        except Exception as e:
            logger.error(f"Error sending alert to Slack: {e}")
            return {
                "success": False,
                "message": f"Error sending alert to Slack: {str(e)}",
                "status": "failed"
            }


class WebhookProvider(AlertProvider):
    """Webhook alert provider"""
    
    def _validate_config(self, config: Dict[str, Any]) -> WebhookConfig:
        return WebhookConfig(**config)
    
    async def send_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send alert via webhook"""
        try:
            config = self.config
            
            # Prepare payload
            payload = {
                "alert_id": alert_data.get("alert_id"),
                "policy_id": alert_data.get("policy_id"),
                "severity": alert_data.get("severity"),
                "title": alert_data.get("title"),
                "message": alert_data.get("message"),
                "summary": alert_data.get("summary"),
                "event_data": alert_data.get("event_data", {}),
                "triggered_at": alert_data.get("triggered_at", "").isoformat() if alert_data.get("triggered_at") else None,
                "tenant_id": alert_data.get("tenant_id"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Send webhook
            async with httpx.AsyncClient(timeout=config.timeout) as client:
                for attempt in range(config.retry_count):
                    try:
                        response = await client.request(
                            method=config.method,
                            url=config.url,
                            json=payload,
                            headers=config.headers
                        )
                        
                        if response.status_code < 400:
                            return {
                                "success": True,
                                "message": f"Alert sent via webhook (attempt {attempt + 1})",
                                "status": "sent",
                                "response_code": response.status_code
                            }
                        else:
                            logger.warning(f"Webhook attempt {attempt + 1} failed: {response.status_code}")
                            
                    except Exception as e:
                        logger.warning(f"Webhook attempt {attempt + 1} failed: {e}")
                        
                    if attempt < config.retry_count - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
                return {
                    "success": False,
                    "message": f"Webhook failed after {config.retry_count} attempts",
                    "status": "failed"
                }
                    
        except Exception as e:
            logger.error(f"Error sending alert via webhook: {e}")
            return {
                "success": False,
                "message": f"Error sending alert via webhook: {str(e)}",
                "status": "failed"
            }


class EmailProvider(AlertProvider):
    """Email alert provider"""
    
    def _validate_config(self, config: Dict[str, Any]) -> EmailConfig:
        return EmailConfig(**config)
    
    async def send_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send alert via email"""
        try:
            config = self.config
            
            # Prepare email content
            subject = config.subject_template.format(
                severity=alert_data.get("severity", "medium").upper(),
                summary=alert_data.get("summary", "Alert")
            )
            
            message = self._format_message(alert_data)
            
            # Create email
            msg = MIMEMultipart()
            msg['From'] = config.from_email
            msg['To'] = ", ".join(config.to_emails)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain'))
            
            # Send email
            def send_email():
                server = smtplib.SMTP(config.smtp_host, config.smtp_port)
                if config.use_tls:
                    server.starttls()
                server.login(config.smtp_username, config.smtp_password)
                server.send_message(msg)
                server.quit()
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, send_email)
            
            return {
                "success": True,
                "message": f"Alert sent via email to {len(config.to_emails)} recipients",
                "status": "sent"
            }
                    
        except Exception as e:
            logger.error(f"Error sending alert via email: {e}")
            return {
                "success": False,
                "message": f"Error sending alert via email: {str(e)}",
                "status": "failed"
            }


def create_provider(provider_type: AlertProviderType, config: Dict[str, Any]) -> AlertProvider:
    """Factory function to create alert providers"""
    providers = {
        AlertProviderType.PAGERDUTY: PagerDutyProvider,
        AlertProviderType.SLACK: SlackProvider,
        AlertProviderType.WEBHOOK: WebhookProvider,
        AlertProviderType.EMAIL: EmailProvider,
    }
    
    provider_class = providers.get(provider_type)
    if not provider_class:
        raise ValueError(f"Unsupported provider type: {provider_type}")
    
    return provider_class(provider_type, config)
