"""
OCI Cloud Provider Service

This module handles OCI-specific operations like connection testing and service discovery.
"""

import logging
from typing import Dict, Any, List, Optional
import oci
from oci.exceptions import ServiceError, ClientError

logger = logging.getLogger(__name__)


class OCIProvider:
    """OCI cloud provider service"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.tenancy_id = config.get("tenancy_id")
        self.user_id = config.get("user_id")
        self.fingerprint = config.get("fingerprint")
        self.private_key = config.get("private_key")
        self.region = config.get("region", "us-ashburn-1")
        self.config_dict = None
        self._setup_config()
    
    def _setup_config(self):
        """Setup OCI configuration"""
        try:
            if all([self.tenancy_id, self.user_id, self.fingerprint, self.private_key]):
                # Use explicit configuration
                self.config_dict = {
                    "tenancy": self.tenancy_id,
                    "user": self.user_id,
                    "fingerprint": self.fingerprint,
                    "key_content": self.private_key,
                    "region": self.region
                }
            else:
                # Use default configuration file
                self.config_dict = oci.config.from_file()
                
        except Exception as e:
            logger.error(f"Error setting up OCI configuration: {e}")
            raise
    
    async def test_connection(self) -> bool:
        """Test connection to OCI"""
        try:
            # Test by calling a simple API
            identity_client = oci.identity.IdentityClient(self.config_dict)
            tenancy = identity_client.get_tenancy(self.tenancy_id)
            return tenancy.status == 200
            
        except (ServiceError, ClientError) as e:
            logger.error(f"Error testing OCI connection: {e}")
            return False
    
    async def get_available_services(self) -> List[str]:
        """Get list of available OCI services"""
        try:
            # Common OCI services
            services = [
                "core",  # Compute
                "objectstorage",  # Object Storage
                "database",  # Database
                "loadbalancer",  # Load Balancer
                "container_engine",  # Container Engine for Kubernetes
                "container_instances",  # Container Instances
                "functions",  # Functions
                "streaming",  # Streaming
                "monitoring",  # Monitoring
                "logging",  # Logging
                "vault",  # Vault
                "key_management",  # Key Management
                "identity",  # Identity and Access Management
                "network_load_balancer",  # Network Load Balancer
                "apigateway",  # API Gateway
                "service_mesh",  # Service Mesh
                "data_science",  # Data Science
                "data_flow",  # Data Flow
                "data_catalog",  # Data Catalog
                "data_integration",  # Data Integration
                "analytics",  # Analytics
                "ai_anomaly_detection",  # AI Anomaly Detection
                "ai_vision",  # AI Vision
                "ai_speech",  # AI Speech
                "ai_language",  # AI Language
            ]
            
            # Check which services are available
            available_services = []
            for service in services:
                try:
                    # Try to create a client for the service
                    if service == "core":
                        client = oci.core.ComputeClient(self.config_dict)
                        # Try a simple operation
                        client.list_instances(self.config_dict["tenancy"])
                    elif service == "objectstorage":
                        client = oci.object_storage.ObjectStorageClient(self.config_dict)
                        # Try a simple operation
                        client.list_namespaces()
                    elif service == "identity":
                        client = oci.identity.IdentityClient(self.config_dict)
                        # Try a simple operation
                        client.list_compartments(self.config_dict["tenancy"])
                    else:
                        # For other services, just assume they're available
                        pass
                    available_services.append(service)
                except Exception:
                    continue
            
            return available_services
            
        except Exception as e:
            logger.error(f"Error getting OCI services: {e}")
            return []
    
    async def get_available_regions(self) -> List[str]:
        """Get list of available OCI regions"""
        try:
            regions = [
                "us-ashburn-1", "us-phoenix-1", "us-sanjose-1", "us-chicago-1",
                "ca-toronto-1", "ca-montreal-1", "sa-saopaulo-1", "sa-santiago-1",
                "sa-vinhedo-1", "uk-london-1", "uk-cardiff-1", "uk-gov-london-1",
                "uk-gov-cardiff-1", "de-frankfurt-1", "de-munich-1", "fr-paris-1",
                "fr-marseille-1", "it-milan-1", "nl-amsterdam-1", "eu-frankfurt-1",
                "eu-zurich-1", "ap-mumbai-1", "ap-hyderabad-1", "ap-melbourne-1",
                "ap-osaka-1", "ap-seoul-1", "ap-sydney-1", "ap-tokyo-1",
                "ap-chuncheon-1", "ap-singapore-1", "ap-bangkok-1", "ap-jakarta-1",
                "me-jeddah-1", "me-abudhabi-1", "me-dubai-1", "il-jerusalem-1",
                "af-johannesburg-1", "ap-chiyoda-1", "ap-ibaraki-1", "us-langley-1",
                "us-luke-1", "us-gov-ashburn-1", "us-gov-chicago-1", "us-gov-phoenix-1",
                "us-gov-orlando-1", "us-gov-sanjose-1", "us-gov-luke-1", "us-gov-langley-1"
            ]
            
            # Check which regions are available for the tenancy
            available_regions = []
            identity_client = oci.identity.IdentityClient(self.config_dict)
            
            try:
                response = identity_client.list_regions()
                available_regions = [region.name for region in response.data]
            except Exception:
                # If we can't get the list, return common regions
                available_regions = regions[:20]  # Return first 20 common regions
            
            return available_regions
            
        except Exception as e:
            logger.error(f"Error getting OCI regions: {e}")
            return []
    
    async def get_tenancy_info(self) -> Dict[str, Any]:
        """Get OCI tenancy information"""
        try:
            identity_client = oci.identity.IdentityClient(self.config_dict)
            tenancy = identity_client.get_tenancy(self.tenancy_id)
            
            return {
                "tenancy_id": tenancy.data.id,
                "name": tenancy.data.name,
                "description": tenancy.data.description,
                "home_region_key": tenancy.data.home_region_key,
                "upi_idcs_compatibility_layer_endpoint": tenancy.data.upi_idcs_compatibility_layer_endpoint,
                "freeform_tags": tenancy.data.freeform_tags,
                "defined_tags": tenancy.data.defined_tags
            }
            
        except Exception as e:
            logger.error(f"Error getting OCI tenancy info: {e}")
            return {"error": str(e)}
    
    async def get_compartments(self) -> List[Dict[str, Any]]:
        """Get list of compartments"""
        try:
            identity_client = oci.identity.IdentityClient(self.config_dict)
            response = identity_client.list_compartments(self.tenancy_id)
            
            compartments = []
            for compartment in response.data:
                compartments.append({
                    "id": compartment.id,
                    "name": compartment.name,
                    "description": compartment.description,
                    "lifecycle_state": compartment.lifecycle_state,
                    "time_created": compartment.time_created.isoformat(),
                    "freeform_tags": compartment.freeform_tags,
                    "defined_tags": compartment.defined_tags
                })
            
            return compartments
            
        except Exception as e:
            logger.error(f"Error getting OCI compartments: {e}")
            return []
    
    async def get_compute_instances(self, compartment_id: str = None) -> List[Dict[str, Any]]:
        """Get list of compute instances"""
        try:
            if not compartment_id:
                compartment_id = self.tenancy_id
            
            compute_client = oci.core.ComputeClient(self.config_dict)
            response = compute_client.list_instances(compartment_id)
            
            instances = []
            for instance in response.data:
                instances.append({
                    "id": instance.id,
                    "display_name": instance.display_name,
                    "availability_domain": instance.availability_domain,
                    "lifecycle_state": instance.lifecycle_state,
                    "shape": instance.shape,
                    "time_created": instance.time_created.isoformat(),
                    "freeform_tags": instance.freeform_tags,
                    "defined_tags": instance.defined_tags
                })
            
            return instances
            
        except Exception as e:
            logger.error(f"Error getting OCI compute instances: {e}")
            return []
    
    async def get_storage_buckets(self, compartment_id: str = None) -> List[Dict[str, Any]]:
        """Get list of storage buckets"""
        try:
            if not compartment_id:
                compartment_id = self.tenancy_id
            
            object_storage_client = oci.object_storage.ObjectStorageClient(self.config_dict)
            namespace = object_storage_client.get_namespace().data
            
            response = object_storage_client.list_buckets(namespace, compartment_id)
            
            buckets = []
            for bucket in response.data:
                buckets.append({
                    "name": bucket.name,
                    "namespace": bucket.namespace,
                    "compartment_id": bucket.compartment_id,
                    "time_created": bucket.time_created.isoformat(),
                    "etag": bucket.etag,
                    "public_access_type": bucket.public_access_type,
                    "storage_tier": bucket.storage_tier,
                    "object_events_enabled": bucket.object_events_enabled,
                    "freeform_tags": bucket.freeform_tags,
                    "defined_tags": bucket.defined_tags
                })
            
            return buckets
            
        except Exception as e:
            logger.error(f"Error getting OCI storage buckets: {e}")
            return []
