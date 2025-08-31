"""
AWS Webhook Handler

Handles incoming webhook events from AWS services like CloudWatch, SNS, etc.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class AWSWebhookHandler:
    """Handler for AWS webhook events"""
    
    def __init__(self, *args, **kwargs):
        self.supported_services = [
            "cloudwatch", "sns", "s3", "ec2", "rds", "lambda", 
            "dynamodb", "sqs", "api-gateway", "elb", "autoscaling"
        ]
    
    async def process_webhook(self, payload: Dict[str, Any]) -> List[Any]:
        """
        Process AWS webhook payload and convert to standard event format
        
        Args:
            payload: Raw webhook payload from AWS
            
        Returns:
            List of created event objects
        """
        try:
            # Extract basic information
            event_type = self._determine_event_type(payload)
            source = "aws"
            service = self._extract_service(payload)
            severity = self._determine_severity(payload)
            message = self._extract_message(payload)
            details = self._extract_details(payload)
            
            # Create standardized event
            event_data = {
                "event_type": event_type,
                "source": source,
                "service": service,
                "severity": severity,
                "message": message,
                "details": details,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "raw_payload": payload
            }
            
            logger.info(f"Processed AWS webhook: {event_type} - {message}")
            
            # For now, return a mock event object
            # In a real implementation, this would create and save to database
            mock_event = type("Event", (), {
                "event_id": f"aws-{datetime.utcnow().timestamp()}",
                "event_type": event_type,
                "source": source,
                "service": service,
                "severity": severity,
                "message": message,
                "details": details
            })()
            
            return [mock_event]
            
        except Exception as e:
            logger.error(f"Error processing AWS webhook: {e}")
            raise
    
    def _determine_event_type(self, payload: Dict[str, Any]) -> str:
        """Determine the event type from AWS payload"""
        # Check for CloudWatch Alarm
        if "AlarmName" in payload:
            return "cloud_alert"
        
        # Check for SNS notification
        if "Type" in payload and payload["Type"] == "Notification":
            return "cloud_alert"
        
        # Check for S3 event
        if "Records" in payload and any("s3" in record.get("eventSource", "") for record in payload["Records"]):
            return "cloud_alert"
        
        # Check for EC2 event
        if "detail-type" in payload and "EC2" in payload["detail-type"]:
            return "cloud_alert"
        
        # Default to cloud_alert
        return "cloud_alert"
    
    def _extract_service(self, payload: Dict[str, Any]) -> str:
        """Extract the AWS service from the payload"""
        # Check for CloudWatch
        if "AlarmName" in payload:
            return "cloudwatch"
        
        # Check for SNS
        if "Type" in payload and payload["Type"] == "Notification":
            return "sns"
        
        # Check for S3
        if "Records" in payload and any("s3" in record.get("eventSource", "") for record in payload["Records"]):
            return "s3"
        
        # Check for EC2
        if "detail-type" in payload and "EC2" in payload["detail-type"]:
            return "ec2"
        
        # Check for RDS
        if "detail-type" in payload and "RDS" in payload["detail-type"]:
            return "rds"
        
        # Check for Lambda
        if "detail-type" in payload and "Lambda" in payload["detail-type"]:
            return "lambda"
        
        # Default
        return "unknown"
    
    def _determine_severity(self, payload: Dict[str, Any]) -> str:
        """Determine severity from AWS payload"""
        # CloudWatch Alarm severity
        if "NewStateValue" in payload:
            state = payload["NewStateValue"]
            if state == "ALARM":
                return "critical"
            elif state == "INSUFFICIENT_DATA":
                return "warning"
            else:
                return "info"
        
        # Check for error indicators
        if "error" in str(payload).lower() or "failed" in str(payload).lower():
            return "critical"
        
        # Default to info
        return "info"
    
    def _extract_message(self, payload: Dict[str, Any]) -> str:
        """Extract message from AWS payload"""
        # CloudWatch Alarm
        if "AlarmName" in payload:
            return f"CloudWatch Alarm: {payload['AlarmName']} - {payload.get('NewStateReason', 'State changed')}"
        
        # SNS notification
        if "Message" in payload:
            return payload["Message"]
        
        # S3 event
        if "Records" in payload and payload["Records"]:
            record = payload["Records"][0]
            if "s3" in record.get("eventSource", ""):
                bucket = record.get("s3", {}).get("bucket", {}).get("name", "unknown")
                key = record.get("s3", {}).get("object", {}).get("key", "unknown")
                event_name = record.get("eventName", "unknown")
                return f"S3 {event_name}: {bucket}/{key}"
        
        # EC2 event
        if "detail-type" in payload:
            return f"EC2 {payload['detail-type']}: {payload.get('detail', {}).get('state', 'unknown')}"
        
        # Default
        return "AWS event received"
    
    def _extract_details(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant details from AWS payload"""
        details = {}
        
        # CloudWatch Alarm details
        if "AlarmName" in payload:
            details.update({
                "alarm_name": payload["AlarmName"],
                "alarm_arn": payload.get("AlarmARN"),
                "old_state": payload.get("OldStateValue"),
                "new_state": payload.get("NewStateValue"),
                "region": payload.get("AWSRegion")
            })
        
        # S3 event details
        if "Records" in payload and payload["Records"]:
            record = payload["Records"][0]
            if "s3" in record.get("eventSource", ""):
                details.update({
                    "bucket": record.get("s3", {}).get("bucket", {}).get("name"),
                    "key": record.get("s3", {}).get("object", {}).get("key"),
                    "event_name": record.get("eventName"),
                    "region": record.get("awsRegion")
                })
        
        # EC2 event details
        if "detail-type" in payload and "EC2" in payload["detail-type"]:
            details.update({
                "instance_id": payload.get("detail", {}).get("instance-id"),
                "state": payload.get("detail", {}).get("state"),
                "region": payload.get("region")
            })
        
        return details

# Create handler instance
aws_handler = AWSWebhookHandler()
