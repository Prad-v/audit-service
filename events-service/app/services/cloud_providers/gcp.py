"""
GCP Cloud Provider Service

This module handles GCP-specific operations like connection testing and service discovery.
"""

import logging
from typing import Dict, Any, List, Optional
import httpx
from google.auth import default
from google.auth.transport.requests import Request
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


class GCPProvider:
    """GCP cloud provider service"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.project_id = config.get("project_id")
        self.credentials = None
        self._setup_credentials()
    
    def _setup_credentials(self):
        """Setup GCP credentials"""
        try:
            if "service_account_key" in self.config:
                # Use service account key
                self.credentials = service_account.Credentials.from_service_account_info(
                    self.config["service_account_key"]
                )
            elif "service_account_file" in self.config:
                # Use service account file
                self.credentials = service_account.Credentials.from_service_account_file(
                    self.config["service_account_file"]
                )
            else:
                # Use default credentials
                self.credentials, _ = default()
                
        except Exception as e:
            logger.error(f"Error setting up GCP credentials: {e}")
            raise
    
    async def test_connection(self) -> bool:
        """Test connection to GCP"""
        try:
            # Test by calling a simple API
            async with httpx.AsyncClient() as client:
                # Get access token
                self.credentials.refresh(Request())
                token = self.credentials.token
                
                # Test with Compute Engine API
                headers = {"Authorization": f"Bearer {token}"}
                url = f"https://compute.googleapis.com/compute/v1/projects/{self.project_id}/zones"
                
                response = await client.get(url, headers=headers)
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Error testing GCP connection: {e}")
            return False
    
    async def get_available_services(self) -> List[str]:
        """Get list of available GCP services"""
        try:
            # Common GCP services
            services = [
                "compute.googleapis.com",  # Compute Engine
                "storage.googleapis.com",  # Cloud Storage
                "bigquery.googleapis.com",  # BigQuery
                "pubsub.googleapis.com",  # Pub/Sub
                "cloudfunctions.googleapis.com",  # Cloud Functions
                "run.googleapis.com",  # Cloud Run
                "container.googleapis.com",  # GKE
                "sqladmin.googleapis.com",  # Cloud SQL
                "monitoring.googleapis.com",  # Cloud Monitoring
                "logging.googleapis.com",  # Cloud Logging
                "iam.googleapis.com",  # IAM
                "cloudkms.googleapis.com",  # Cloud KMS
                "secretmanager.googleapis.com",  # Secret Manager
                "cloudbuild.googleapis.com",  # Cloud Build
                "artifactregistry.googleapis.com",  # Artifact Registry
            ]
            
            # Check which services are enabled
            enabled_services = []
            async with httpx.AsyncClient() as client:
                self.credentials.refresh(Request())
                token = self.credentials.token
                headers = {"Authorization": f"Bearer {token}"}
                
                for service in services:
                    try:
                        url = f"https://servicemanagement.googleapis.com/v1/services/{service}"
                        response = await client.get(url, headers=headers)
                        if response.status_code == 200:
                            enabled_services.append(service)
                    except:
                        continue
            
            return enabled_services
            
        except Exception as e:
            logger.error(f"Error getting GCP services: {e}")
            return []
    
    async def get_available_regions(self) -> List[str]:
        """Get list of available GCP regions"""
        try:
            regions = [
                "us-central1", "us-east1", "us-west1", "us-west2", "us-west3", "us-west4",
                "us-east4", "us-central2", "us-east5", "us-central3", "us-east6", "us-central4",
                "europe-west1", "europe-west2", "europe-west3", "europe-west4", "europe-west5",
                "europe-west6", "europe-west7", "europe-west8", "europe-west9", "europe-west10",
                "europe-west11", "europe-west12", "europe-central1", "europe-central2",
                "asia-east1", "asia-east2", "asia-northeast1", "asia-northeast2", "asia-northeast3",
                "asia-south1", "asia-south2", "asia-southeast1", "asia-southeast2",
                "australia-southeast1", "australia-southeast2", "southamerica-east1",
                "northamerica-northeast1", "northamerica-northeast2"
            ]
            
            # Check which regions are available for the project
            available_regions = []
            async with httpx.AsyncClient() as client:
                self.credentials.refresh(Request())
                token = self.credentials.token
                headers = {"Authorization": f"Bearer {token}"}
                
                for region in regions:
                    try:
                        url = f"https://compute.googleapis.com/compute/v1/projects/{self.project_id}/regions/{region}"
                        response = await client.get(url, headers=headers)
                        if response.status_code == 200:
                            available_regions.append(region)
                    except:
                        continue
            
            return available_regions
            
        except Exception as e:
            logger.error(f"Error getting GCP regions: {e}")
            return []
    
    async def get_project_info(self) -> Dict[str, Any]:
        """Get project information"""
        try:
            async with httpx.AsyncClient() as client:
                self.credentials.refresh(Request())
                token = self.credentials.token
                headers = {"Authorization": f"Bearer {token}"}
                
                url = f"https://cloudresourcemanager.googleapis.com/v1/projects/{self.project_id}"
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"Failed to get project info: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Error getting GCP project info: {e}")
            return {"error": str(e)}
