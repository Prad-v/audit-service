"""
AWS Cloud Provider Service

This module handles AWS-specific operations like connection testing and service discovery.
"""

import logging
from typing import Dict, Any, List, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


class AWSProvider:
    """AWS cloud provider service"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.region = config.get("region", "us-east-1")
        self.session = None
        self._setup_session()
    
    def _setup_session(self):
        """Setup AWS session"""
        try:
            if "access_key_id" in self.config and "secret_access_key" in self.config:
                # Use explicit credentials
                self.session = boto3.Session(
                    aws_access_key_id=self.config["access_key_id"],
                    aws_secret_access_key=self.config["secret_access_key"],
                    region_name=self.region
                )
            elif "profile" in self.config:
                # Use named profile
                self.session = boto3.Session(profile_name=self.config["profile"])
            else:
                # Use default credentials
                self.session = boto3.Session(region_name=self.region)
                
        except Exception as e:
            logger.error(f"Error setting up AWS session: {e}")
            raise
    
    async def test_connection(self) -> bool:
        """Test connection to AWS"""
        try:
            # Test by calling a simple API
            sts = self.session.client('sts')
            sts.get_caller_identity()
            return True
            
        except (ClientError, NoCredentialsError) as e:
            logger.error(f"Error testing AWS connection: {e}")
            return False
    
    async def get_available_services(self) -> List[str]:
        """Get list of available AWS services"""
        try:
            # Common AWS services
            services = [
                "ec2",  # Elastic Compute Cloud
                "s3",  # Simple Storage Service
                "rds",  # Relational Database Service
                "lambda",  # Lambda
                "ecs",  # Elastic Container Service
                "eks",  # Elastic Kubernetes Service
                "cloudwatch",  # CloudWatch
                "cloudtrail",  # CloudTrail
                "iam",  # Identity and Access Management
                "sns",  # Simple Notification Service
                "sqs",  # Simple Queue Service
                "dynamodb",  # DynamoDB
                "elasticache",  # ElastiCache
                "redshift",  # Redshift
                "apigateway",  # API Gateway
                "route53",  # Route 53
                "elbv2",  # Elastic Load Balancing
                "autoscaling",  # Auto Scaling
                "cloudformation",  # CloudFormation
                "codebuild",  # CodeBuild
                "codepipeline",  # CodePipeline
                "ecr",  # Elastic Container Registry
                "secretsmanager",  # Secrets Manager
                "kms",  # Key Management Service
            ]
            
            # Check which services are available
            available_services = []
            for service in services:
                try:
                    client = self.session.client(service)
                    # Try a simple operation to test if service is available
                    if service == "ec2":
                        client.describe_regions()
                    elif service == "s3":
                        client.list_buckets()
                    elif service == "iam":
                        client.get_user()
                    elif service == "sts":
                        client.get_caller_identity()
                    else:
                        # For other services, just try to create the client
                        pass
                    available_services.append(service)
                except ClientError as e:
                    # Service might not be available in this region or account
                    if e.response['Error']['Code'] not in ['AccessDenied', 'UnauthorizedOperation']:
                        available_services.append(service)
                except Exception:
                    continue
            
            return available_services
            
        except Exception as e:
            logger.error(f"Error getting AWS services: {e}")
            return []
    
    async def get_available_regions(self) -> List[str]:
        """Get list of available AWS regions"""
        try:
            ec2 = self.session.client('ec2')
            response = ec2.describe_regions()
            return [region['RegionName'] for region in response['Regions']]
            
        except Exception as e:
            logger.error(f"Error getting AWS regions: {e}")
            return []
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get AWS account information"""
        try:
            sts = self.session.client('sts')
            identity = sts.get_caller_identity()
            
            return {
                "account_id": identity.get("Account"),
                "user_id": identity.get("UserId"),
                "arn": identity.get("Arn"),
                "region": self.region
            }
            
        except Exception as e:
            logger.error(f"Error getting AWS account info: {e}")
            return {"error": str(e)}
    
    async def get_ec2_instances(self) -> List[Dict[str, Any]]:
        """Get list of EC2 instances"""
        try:
            ec2 = self.session.client('ec2')
            response = ec2.describe_instances()
            
            instances = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instances.append({
                        "instance_id": instance['InstanceId'],
                        "instance_type": instance['InstanceType'],
                        "state": instance['State']['Name'],
                        "launch_time": instance['LaunchTime'].isoformat(),
                        "tags": {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    })
            
            return instances
            
        except Exception as e:
            logger.error(f"Error getting EC2 instances: {e}")
            return []
    
    async def get_s3_buckets(self) -> List[Dict[str, Any]]:
        """Get list of S3 buckets"""
        try:
            s3 = self.session.client('s3')
            response = s3.list_buckets()
            
            buckets = []
            for bucket in response['Buckets']:
                buckets.append({
                    "name": bucket['Name'],
                    "creation_date": bucket['CreationDate'].isoformat()
                })
            
            return buckets
            
        except Exception as e:
            logger.error(f"Error getting S3 buckets: {e}")
            return []
