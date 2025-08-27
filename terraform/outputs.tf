# Terraform Outputs for Audit Log Framework GCP Infrastructure

# Network Outputs
output "network_name" {
  description = "Name of the VPC network"
  value       = google_compute_network.main.name
}

output "network_self_link" {
  description = "Self link of the VPC network"
  value       = google_compute_network.main.self_link
}

output "subnet_name" {
  description = "Name of the main subnet"
  value       = google_compute_subnetwork.main.name
}

output "subnet_self_link" {
  description = "Self link of the main subnet"
  value       = google_compute_subnetwork.main.self_link
}

# Database Outputs
output "database_instance_name" {
  description = "Name of the Cloud SQL instance"
  value       = google_sql_database_instance.main.name
}

output "database_connection_name" {
  description = "Connection name for the Cloud SQL instance"
  value       = google_sql_database_instance.main.connection_name
}

output "database_private_ip" {
  description = "Private IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.main.private_ip_address
}

output "database_public_ip" {
  description = "Public IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.main.public_ip_address
}

# Redis Outputs
output "redis_instance_id" {
  description = "ID of the Redis instance"
  value       = google_redis_instance.cache.id
}

output "redis_host" {
  description = "Host IP address of the Redis instance"
  value       = google_redis_instance.cache.host
}

output "redis_port" {
  description = "Port of the Redis instance"
  value       = google_redis_instance.cache.port
}

output "redis_auth_string" {
  description = "Auth string for the Redis instance"
  value       = google_redis_instance.cache.auth_string
  sensitive   = true
}

# GKE Outputs
output "gke_cluster_name" {
  description = "Name of the GKE cluster"
  value       = google_container_cluster.main.name
}

output "gke_cluster_endpoint" {
  description = "Endpoint of the GKE cluster"
  value       = google_container_cluster.main.endpoint
  sensitive   = true
}

output "gke_cluster_ca_certificate" {
  description = "CA certificate of the GKE cluster"
  value       = google_container_cluster.main.master_auth[0].cluster_ca_certificate
  sensitive   = true
}

output "gke_cluster_location" {
  description = "Location of the GKE cluster"
  value       = google_container_cluster.main.location
}

# BigQuery Outputs
output "bigquery_dataset_id" {
  description = "ID of the BigQuery dataset"
  value       = google_bigquery_dataset.audit_logs.dataset_id
}

output "bigquery_dataset_location" {
  description = "Location of the BigQuery dataset"
  value       = google_bigquery_dataset.audit_logs.location
}

output "bigquery_table_id" {
  description = "ID of the BigQuery audit logs table"
  value       = google_bigquery_table.audit_logs.table_id
}

# Pub/Sub Outputs
output "pubsub_topic_name" {
  description = "Name of the Pub/Sub topic"
  value       = google_pubsub_topic.audit_events.name
}

output "pubsub_subscription_name" {
  description = "Name of the Pub/Sub subscription"
  value       = google_pubsub_subscription.audit_processor.name
}

output "pubsub_dlq_topic_name" {
  description = "Name of the Pub/Sub dead letter queue topic"
  value       = google_pubsub_topic.audit_events_dlq.name
}

# Service Account Outputs
output "audit_service_account_email" {
  description = "Email of the audit service account"
  value       = google_service_account.audit_service.email
}

output "gke_nodes_service_account_email" {
  description = "Email of the GKE nodes service account"
  value       = google_service_account.gke_nodes.email
}

# Secret Manager Outputs
output "db_password_secret_name" {
  description = "Name of the database password secret"
  value       = google_secret_manager_secret.db_password.secret_id
}

output "jwt_secret_name" {
  description = "Name of the JWT secret"
  value       = google_secret_manager_secret.jwt_secret.secret_id
}

# Connection Information for Applications
output "connection_info" {
  description = "Connection information for applications"
  value = {
    # Database connection
    database = {
      host     = google_sql_database_instance.main.private_ip_address
      port     = 5432
      database = google_sql_database.audit_logs.name
      username = google_sql_user.audit_user.name
    }
    
    # Redis connection
    redis = {
      host = google_redis_instance.cache.host
      port = google_redis_instance.cache.port
    }
    
    # BigQuery connection
    bigquery = {
      project_id = var.project_id
      dataset_id = google_bigquery_dataset.audit_logs.dataset_id
      table_id   = google_bigquery_table.audit_logs.table_id
    }
    
    # Pub/Sub connection
    pubsub = {
      topic_name        = google_pubsub_topic.audit_events.name
      subscription_name = google_pubsub_subscription.audit_processor.name
    }
    
    # Service account
    service_account_email = google_service_account.audit_service.email
  }
  sensitive = true
}

# Kubernetes Configuration
output "kubernetes_config" {
  description = "Kubernetes configuration for connecting to the cluster"
  value = {
    cluster_name     = google_container_cluster.main.name
    cluster_endpoint = google_container_cluster.main.endpoint
    cluster_location = google_container_cluster.main.location
    
    # Command to get credentials
    get_credentials_command = "gcloud container clusters get-credentials ${google_container_cluster.main.name} --region ${google_container_cluster.main.location} --project ${var.project_id}"
  }
  sensitive = true
}

# Environment Configuration
output "environment_config" {
  description = "Environment-specific configuration values"
  value = {
    project_id  = var.project_id
    region      = var.region
    zone        = var.zone
    environment = var.environment
    
    # Network configuration
    network_name = google_compute_network.main.name
    subnet_name  = google_compute_subnetwork.main.name
    
    # Resource names
    db_instance_name = google_sql_database_instance.main.name
    redis_instance_name = google_redis_instance.cache.name
    gke_cluster_name = google_container_cluster.main.name
    
    # BigQuery configuration
    bigquery_dataset = google_bigquery_dataset.audit_logs.dataset_id
    bigquery_table   = google_bigquery_table.audit_logs.table_id
    
    # Pub/Sub configuration
    pubsub_topic = google_pubsub_topic.audit_events.name
    pubsub_subscription = google_pubsub_subscription.audit_processor.name
  }
}

# Monitoring and Logging
output "monitoring_config" {
  description = "Monitoring and logging configuration"
  value = {
    # Cloud Logging
    log_sink_destination = "bigquery.googleapis.com/projects/${var.project_id}/datasets/${google_bigquery_dataset.audit_logs.dataset_id}"
    
    # Cloud Monitoring
    notification_channels = []
    
    # Workload Identity
    workload_identity_pool = "${var.project_id}.svc.id.goog"
    
    # Service account for monitoring
    service_account_email = google_service_account.audit_service.email
  }
}

# Security Configuration
output "security_config" {
  description = "Security configuration information"
  value = {
    # Secret Manager secrets
    secrets = {
      db_password = google_secret_manager_secret.db_password.secret_id
      jwt_secret  = google_secret_manager_secret.jwt_secret.secret_id
    }
    
    # Service accounts
    service_accounts = {
      audit_service = google_service_account.audit_service.email
      gke_nodes     = google_service_account.gke_nodes.email
    }
    
    # Workload Identity
    workload_identity = {
      pool = "${var.project_id}.svc.id.goog"
      namespace = var.k8s_namespace
      service_account = var.k8s_service_account
    }
    
    # Network security
    private_cluster = true
    authorized_networks = ["0.0.0.0/0"] # Should be restricted in production
  }
  sensitive = true
}

# Deployment Information
output "deployment_info" {
  description = "Information needed for application deployment"
  value = {
    # Infrastructure readiness
    infrastructure_ready = true
    
    # Required environment variables for the application
    environment_variables = {
      PROJECT_ID = var.project_id
      REGION     = var.region
      ENVIRONMENT = var.environment
      
      # Database
      DB_HOST = google_sql_database_instance.main.private_ip_address
      DB_PORT = "5432"
      DB_NAME = google_sql_database.audit_logs.name
      DB_USER = google_sql_user.audit_user.name
      
      # Redis
      REDIS_HOST = google_redis_instance.cache.host
      REDIS_PORT = tostring(google_redis_instance.cache.port)
      
      # BigQuery
      BIGQUERY_DATASET = google_bigquery_dataset.audit_logs.dataset_id
      BIGQUERY_TABLE   = google_bigquery_table.audit_logs.table_id
      
      # Pub/Sub
      PUBSUB_TOPIC        = google_pubsub_topic.audit_events.name
      PUBSUB_SUBSCRIPTION = google_pubsub_subscription.audit_processor.name
      
      # Service Account
      GOOGLE_APPLICATION_CREDENTIALS = "/var/secrets/google/key.json"
    }
    
    # Kubernetes configuration
    kubernetes = {
      namespace       = var.k8s_namespace
      service_account = var.k8s_service_account
      cluster_name    = google_container_cluster.main.name
      cluster_location = google_container_cluster.main.location
    }
  }
  sensitive = true
}