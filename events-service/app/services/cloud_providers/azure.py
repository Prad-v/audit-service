"""
Azure Cloud Provider Service

This module handles Azure-specific operations like connection testing and service discovery.
"""

import logging
from typing import Dict, Any, List, Optional
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.subscription import SubscriptionClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.storage import StorageManagementClient

logger = logging.getLogger(__name__)


class AzureProvider:
    """Azure cloud provider service"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.subscription_id = config.get("subscription_id")
        self.tenant_id = config.get("tenant_id")
        self.client_id = config.get("client_id")
        self.client_secret = config.get("client_secret")
        self.credential = None
        self._setup_credentials()
    
    def _setup_credentials(self):
        """Setup Azure credentials"""
        try:
            if all([self.tenant_id, self.client_id, self.client_secret]):
                # Use service principal credentials
                self.credential = ClientSecretCredential(
                    tenant_id=self.tenant_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )
            else:
                # Use default credentials
                self.credential = DefaultAzureCredential()
                
        except Exception as e:
            logger.error(f"Error setting up Azure credentials: {e}")
            raise
    
    async def test_connection(self) -> bool:
        """Test connection to Azure"""
        try:
            # Test by calling a simple API
            subscription_client = SubscriptionClient(credential=self.credential)
            subscriptions = subscription_client.subscriptions.list()
            # Just try to get the first subscription to test connection
            next(subscriptions)
            return True
            
        except Exception as e:
            logger.error(f"Error testing Azure connection: {e}")
            return False
    
    async def get_available_services(self) -> List[str]:
        """Get list of available Azure services"""
        try:
            # Common Azure services
            services = [
                "Microsoft.Compute",  # Virtual Machines
                "Microsoft.Storage",  # Storage Accounts
                "Microsoft.Network",  # Virtual Network
                "Microsoft.Web",  # App Service
                "Microsoft.ContainerService",  # AKS
                "Microsoft.ContainerRegistry",  # Container Registry
                "Microsoft.OperationalInsights",  # Log Analytics
                "Microsoft.Insights",  # Application Insights
                "Microsoft.KeyVault",  # Key Vault
                "Microsoft.Sql",  # SQL Database
                "Microsoft.Cache",  # Redis Cache
                "Microsoft.ServiceBus",  # Service Bus
                "Microsoft.EventHub",  # Event Hubs
                "Microsoft.StreamAnalytics",  # Stream Analytics
                "Microsoft.DataFactory",  # Data Factory
                "Microsoft.MachineLearningServices",  # Machine Learning
                "Microsoft.CognitiveServices",  # Cognitive Services
                "Microsoft.Search",  # Search Service
                "Microsoft.DocumentDB",  # Cosmos DB
                "Microsoft.NotificationHubs",  # Notification Hubs
                "Microsoft.ApiManagement",  # API Management
                "Microsoft.Logic",  # Logic Apps
                "Microsoft.Functions",  # Functions
                "Microsoft.Batch",  # Batch
                "Microsoft.HDInsight",  # HDInsight
            ]
            
            # Check which services are available
            available_services = []
            resource_client = ResourceManagementClient(
                credential=self.credential,
                subscription_id=self.subscription_id
            )
            
            for service in services:
                try:
                    # Try to list providers to check if service is available
                    providers = resource_client.providers.list()
                    for provider in providers:
                        if provider.namespace == service:
                            available_services.append(service)
                            break
                except Exception:
                    continue
            
            return available_services
            
        except Exception as e:
            logger.error(f"Error getting Azure services: {e}")
            return []
    
    async def get_available_regions(self) -> List[str]:
        """Get list of available Azure regions"""
        try:
            regions = [
                "eastus", "eastus2", "southcentralus", "westus2", "westus3",
                "australiaeast", "southeastasia", "northeurope", "uksouth",
                "westeurope", "centralus", "northcentralus", "southafricanorth",
                "centralindia", "eastasia", "japaneast", "japanwest",
                "koreacentral", "canadacentral", "francecentral", "germanywestcentral",
                "norwayeast", "switzerlandnorth", "uaeorth", "brazilsouth",
                "centralusstage", "eastusstage", "eastus2stage", "northcentralusstage",
                "southcentralusstage", "westusstage", "westus2stage", "asia",
                "asiapacific", "australia", "brazil", "canada", "europe",
                "global", "india", "japan", "uk", "unitedstates", "eastasiastage",
                "southeastasiastage", "brazilsouthstage", "eastusstages",
                "westeuropestage", "centraluseuap", "eastus2euap", "westcentralus",
                "southafricawest", "australiacentral", "australiacentral2",
                "australiasoutheast", "japanwest", "koreasouth", "southindia",
                "westindia", "canadaeast", "francesouth", "germanynorth",
                "norwaywest", "switzerlandwest", "ukwest", "uaecentral",
                "brazilsoutheast"
            ]
            
            # Check which regions are available for the subscription
            available_regions = []
            resource_client = ResourceManagementClient(
                credential=self.credential,
                subscription_id=self.subscription_id
            )
            
            try:
                locations = resource_client.subscriptions.list_locations(self.subscription_id)
                available_regions = [location.name for location in locations]
            except Exception:
                # If we can't get the list, return common regions
                available_regions = regions[:20]  # Return first 20 common regions
            
            return available_regions
            
        except Exception as e:
            logger.error(f"Error getting Azure regions: {e}")
            return []
    
    async def get_subscription_info(self) -> Dict[str, Any]:
        """Get Azure subscription information"""
        try:
            subscription_client = SubscriptionClient(credential=self.credential)
            subscription = subscription_client.subscriptions.get(self.subscription_id)
            
            return {
                "subscription_id": subscription.subscription_id,
                "display_name": subscription.display_name,
                "state": subscription.state,
                "location_placement_id": subscription.location_placement_id,
                "quota_id": subscription.quota_id,
                "spending_limit": subscription.spending_limit,
                "authorization_source": subscription.authorization_source
            }
            
        except Exception as e:
            logger.error(f"Error getting Azure subscription info: {e}")
            return {"error": str(e)}
    
    async def get_virtual_machines(self) -> List[Dict[str, Any]]:
        """Get list of Virtual Machines"""
        try:
            compute_client = ComputeManagementClient(
                credential=self.credential,
                subscription_id=self.subscription_id
            )
            
            vms = []
            for vm in compute_client.virtual_machines.list_all():
                vms.append({
                    "name": vm.name,
                    "id": vm.id,
                    "location": vm.location,
                    "vm_size": vm.hardware_profile.vm_size if vm.hardware_profile else None,
                    "provisioning_state": vm.provisioning_state,
                    "tags": vm.tags
                })
            
            return vms
            
        except Exception as e:
            logger.error(f"Error getting Azure VMs: {e}")
            return []
    
    async def get_storage_accounts(self) -> List[Dict[str, Any]]:
        """Get list of Storage Accounts"""
        try:
            storage_client = StorageManagementClient(
                credential=self.credential,
                subscription_id=self.subscription_id
            )
            
            accounts = []
            for account in storage_client.storage_accounts.list():
                accounts.append({
                    "name": account.name,
                    "id": account.id,
                    "location": account.location,
                    "account_type": account.sku.name if account.sku else None,
                    "provisioning_state": account.provisioning_state,
                    "tags": account.tags
                })
            
            return accounts
            
        except Exception as e:
            logger.error(f"Error getting Azure Storage Accounts: {e}")
            return []
