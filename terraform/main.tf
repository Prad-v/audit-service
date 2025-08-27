# Audit Log Framework - GCP Infrastructure
# This Terraform configuration creates the complete GCP infrastructure
# for the production audit log framework deployment

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
}

# Configure the Google Cloud Provider
provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Local values for resource naming and tagging
locals {
  name_prefix = "${var.environment}-audit-log"
  
  common_labels = {
    environment = var.environment
    project     = "audit-log-framework"
    managed_by  = "terraform"
    team        = "platform"
  }
  
  # Network configuration
  network_name    = "${local.name_prefix}-network"
  subnet_name     = "${local.name_prefix}-subnet"
  
  # Database configuration
  db_instance_name = "${local.name_prefix}-postgres"
  
  # GKE configuration
  gke_cluster_name = "${local.name_prefix}-cluster"
  
  # BigQuery configuration
  dataset_name = "${var.environment}_audit_logs"
  
  # Pub/Sub configuration
  topic_name        = "${local.name_prefix}-events"
  subscription_name = "${local.name_prefix}-processor"
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "compute.googleapis.com",
    "container.googleapis.com",
    "sql.googleapis.com",
    "bigquery.googleapis.com",
    "pubsub.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "secretmanager.googleapis.com",
    "redis.googleapis.com",
    "servicenetworking.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com"
  ])
  
  service = each.value
  
  disable_dependent_services = false
  disable_on_destroy        = false
}

# VPC Network
resource "google_compute_network" "main" {
  name                    = local.network_name
  auto_create_subnetworks = false
  mtu                     = 1460
  
  depends_on = [google_project_service.required_apis]
  
  labels = local.common_labels
}

# Subnet for GKE and other resources
resource "google_compute_subnetwork" "main" {
  name          = local.subnet_name
  ip_cidr_range = var.subnet_cidr
  region        = var.region
  network       = google_compute_network.main.id
  
  # Secondary IP ranges for GKE
  secondary_ip_range {
    range_name    = "gke-pods"
    ip_cidr_range = var.pods_cidr
  }
  
  secondary_ip_range {
    range_name    = "gke-services"
    ip_cidr_range = var.services_cidr
  }
  
  private_ip_google_access = true
}

# Cloud Router for NAT
resource "google_compute_router" "main" {
  name    = "${local.name_prefix}-router"
  region  = var.region
  network = google_compute_network.main.id
}

# Cloud NAT for outbound internet access
resource "google_compute_router_nat" "main" {
  name                               = "${local.name_prefix}-nat"
  router                            = google_compute_router.main.name
  region                            = var.region
  nat_ip_allocate_option            = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
  
  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# Firewall rules
resource "google_compute_firewall" "allow_internal" {
  name    = "${local.name_prefix}-allow-internal"
  network = google_compute_network.main.name
  
  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }
  
  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }
  
  allow {
    protocol = "icmp"
  }
  
  source_ranges = [var.subnet_cidr, var.pods_cidr, var.services_cidr]
  
  target_tags = ["gke-node"]
}

resource "google_compute_firewall" "allow_health_checks" {
  name    = "${local.name_prefix}-allow-health-checks"
  network = google_compute_network.main.name
  
  allow {
    protocol = "tcp"
    ports    = ["8080", "8000", "3000"]
  }
  
  source_ranges = ["130.211.0.0/22", "35.191.0.0/16"]
  target_tags   = ["gke-node"]
}

# Private service connection for Cloud SQL
resource "google_compute_global_address" "private_ip_address" {
  name          = "${local.name_prefix}-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.main.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.main.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
  
  depends_on = [google_project_service.required_apis]
}

# Cloud SQL PostgreSQL instance
resource "google_sql_database_instance" "main" {
  name             = local.db_instance_name
  database_version = "POSTGRES_15"
  region           = var.region
  
  settings {
    tier                        = var.db_tier
    availability_type           = var.environment == "production" ? "REGIONAL" : "ZONAL"
    disk_type                   = "PD_SSD"
    disk_size                   = var.db_disk_size
    disk_autoresize            = true
    disk_autoresize_limit      = var.db_max_disk_size
    
    backup_configuration {
      enabled                        = true
      start_time                     = "02:00"
      location                       = var.region
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 30
        retention_unit   = "COUNT"
      }
    }
    
    maintenance_window {
      day          = 7
      hour         = 3
      update_track = "stable"
    }
    
    database_flags {
      name  = "shared_preload_libraries"
      value = "pg_stat_statements"
    }
    
    database_flags {
      name  = "log_statement"
      value = "all"
    }
    
    database_flags {
      name  = "log_min_duration_statement"
      value = "1000"
    }
    
    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = google_compute_network.main.id
      enable_private_path_for_google_cloud_services = true
    }
    
    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = true
    }
  }
  
  deletion_protection = var.environment == "production"
  
  depends_on = [google_service_networking_connection.private_vpc_connection]
}

# Database
resource "google_sql_database" "audit_logs" {
  name     = "audit_logs"
  instance = google_sql_database_instance.main.name
}

# Database user
resource "google_sql_user" "audit_user" {
  name     = "audit_user"
  instance = google_sql_database_instance.main.name
  password = var.db_password
}

# Redis instance for caching
resource "google_redis_instance" "cache" {
  name           = "${local.name_prefix}-cache"
  tier           = var.redis_tier
  memory_size_gb = var.redis_memory_size
  region         = var.region
  
  location_id             = var.zone
  alternative_location_id = var.redis_tier == "STANDARD_HA" ? "${var.region}-b" : null
  
  authorized_network = google_compute_network.main.id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"
  
  redis_version     = "REDIS_7_0"
  display_name      = "${local.name_prefix} Cache"
  
  maintenance_policy {
    weekly_maintenance_window {
      day = "SUNDAY"
      start_time {
        hours   = 3
        minutes = 0
        seconds = 0
        nanos   = 0
      }
    }
  }
  
  labels = local.common_labels
  
  depends_on = [google_project_service.required_apis]
}

# GKE Cluster
resource "google_container_cluster" "main" {
  name     = local.gke_cluster_name
  location = var.region
  
  # We can't create a cluster with no node pool defined, but we want to only use
  # separately managed node pools. So we create the smallest possible default
  # node pool and immediately delete it.
  remove_default_node_pool = true
  initial_node_count       = 1
  
  network    = google_compute_network.main.name
  subnetwork = google_compute_subnetwork.main.name
  
  # IP allocation for pods and services
  ip_allocation_policy {
    cluster_secondary_range_name  = "gke-pods"
    services_secondary_range_name = "gke-services"
  }
  
  # Network policy
  network_policy {
    enabled = true
  }
  
  # Private cluster configuration
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = var.master_cidr
    
    master_global_access_config {
      enabled = true
    }
  }
  
  # Master authorized networks
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = "0.0.0.0/0"
      display_name = "All networks"
    }
  }
  
  # Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }
  
  # Addons
  addons_config {
    http_load_balancing {
      disabled = false
    }
    
    horizontal_pod_autoscaling {
      disabled = false
    }
    
    network_policy_config {
      disabled = false
    }
    
    gcp_filestore_csi_driver_config {
      enabled = false
    }
  }
  
  # Logging and monitoring
  logging_service    = "logging.googleapis.com/kubernetes"
  monitoring_service = "monitoring.googleapis.com/kubernetes"
  
  # Maintenance window
  maintenance_policy {
    recurring_window {
      start_time = "2023-01-01T03:00:00Z"
      end_time   = "2023-01-01T07:00:00Z"
      recurrence = "FREQ=WEEKLY;BYDAY=SU"
    }
  }
  
  # Release channel
  release_channel {
    channel = var.gke_release_channel
  }
  
  depends_on = [
    google_project_service.required_apis,
    google_compute_subnetwork.main
  ]
}

# GKE Node Pool
resource "google_container_node_pool" "main" {
  name       = "${local.gke_cluster_name}-nodes"
  location   = var.region
  cluster    = google_container_cluster.main.name
  node_count = var.gke_node_count
  
  # Auto-scaling
  autoscaling {
    min_node_count = var.gke_min_nodes
    max_node_count = var.gke_max_nodes
  }
  
  # Node configuration
  node_config {
    preemptible  = var.environment != "production"
    machine_type = var.gke_machine_type
    disk_size_gb = var.gke_disk_size
    disk_type    = "pd-ssd"
    
    # Google service account
    service_account = google_service_account.gke_nodes.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
    
    # Workload Identity
    workload_metadata_config {
      mode = "GKE_METADATA"
    }
    
    # Shielded instance
    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }
    
    # Labels and tags
    labels = merge(local.common_labels, {
      node_pool = "main"
    })
    
    tags = ["gke-node", "${local.gke_cluster_name}-node"]
  }
  
  # Node management
  management {
    auto_repair  = true
    auto_upgrade = true
  }
  
  # Upgrade settings
  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
  }
  
  depends_on = [google_container_cluster.main]
}

# Service account for GKE nodes
resource "google_service_account" "gke_nodes" {
  account_id   = "${local.name_prefix}-gke-nodes"
  display_name = "GKE Nodes Service Account"
  description  = "Service account for GKE nodes in the audit log cluster"
}

# IAM bindings for GKE nodes
resource "google_project_iam_member" "gke_nodes" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/monitoring.viewer",
    "roles/stackdriver.resourceMetadata.writer"
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.gke_nodes.email}"
}

# BigQuery dataset
resource "google_bigquery_dataset" "audit_logs" {
  dataset_id                  = local.dataset_name
  friendly_name              = "Audit Logs Dataset"
  description                = "Dataset for storing audit log data"
  location                   = var.bigquery_location
  default_table_expiration_ms = var.bigquery_table_expiration_ms
  
  access {
    role          = "OWNER"
    user_by_email = google_service_account.audit_service.email
  }
  
  access {
    role          = "READER"
    user_by_email = google_service_account.audit_service.email
  }
  
  access {
    role          = "WRITER"
    user_by_email = google_service_account.audit_service.email
  }
  
  labels = local.common_labels
  
  depends_on = [google_project_service.required_apis]
}

# BigQuery table for audit logs
resource "google_bigquery_table" "audit_logs" {
  dataset_id = google_bigquery_dataset.audit_logs.dataset_id
  table_id   = "audit_logs"
  
  description = "Main audit logs table"
  
  time_partitioning {
    type                     = "DAY"
    field                    = "created_at"
    expiration_ms           = var.bigquery_partition_expiration_ms
    require_partition_filter = true
  }
  
  clustering = ["tenant_id", "event_type"]
  
  schema = jsonencode([
    {
      name = "id"
      type = "STRING"
      mode = "REQUIRED"
      description = "Unique identifier for the audit log entry"
    },
    {
      name = "tenant_id"
      type = "STRING"
      mode = "REQUIRED"
      description = "Tenant identifier"
    },
    {
      name = "event_type"
      type = "STRING"
      mode = "REQUIRED"
      description = "Type of event being audited"
    },
    {
      name = "user_id"
      type = "STRING"
      mode = "NULLABLE"
      description = "User who performed the action"
    },
    {
      name = "resource_id"
      type = "STRING"
      mode = "NULLABLE"
      description = "Resource that was acted upon"
    },
    {
      name = "action"
      type = "STRING"
      mode = "NULLABLE"
      description = "Action that was performed"
    },
    {
      name = "metadata"
      type = "JSON"
      mode = "NULLABLE"
      description = "Additional metadata about the event"
    },
    {
      name = "ip_address"
      type = "STRING"
      mode = "NULLABLE"
      description = "IP address of the client"
    },
    {
      name = "user_agent"
      type = "STRING"
      mode = "NULLABLE"
      description = "User agent of the client"
    },
    {
      name = "created_at"
      type = "TIMESTAMP"
      mode = "REQUIRED"
      description = "Timestamp when the event occurred"
    },
    {
      name = "processed_at"
      type = "TIMESTAMP"
      mode = "NULLABLE"
      description = "Timestamp when the event was processed"
    }
  ])
  
  labels = local.common_labels
}

# Pub/Sub topic for audit events
resource "google_pubsub_topic" "audit_events" {
  name = local.topic_name
  
  labels = local.common_labels
  
  depends_on = [google_project_service.required_apis]
}

# Pub/Sub subscription for processing audit events
resource "google_pubsub_subscription" "audit_processor" {
  name  = local.subscription_name
  topic = google_pubsub_topic.audit_events.name
  
  # Message retention
  message_retention_duration = "604800s" # 7 days
  
  # Acknowledgment deadline
  ack_deadline_seconds = 60
  
  # Retry policy
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
  
  # Dead letter policy
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.audit_events_dlq.id
    max_delivery_attempts = 5
  }
  
  labels = local.common_labels
}

# Dead letter queue for failed messages
resource "google_pubsub_topic" "audit_events_dlq" {
  name = "${local.topic_name}-dlq"
  
  labels = local.common_labels
}

# Service account for the audit service
resource "google_service_account" "audit_service" {
  account_id   = "${local.name_prefix}-service"
  display_name = "Audit Service Account"
  description  = "Service account for the audit log service"
}

# IAM bindings for the audit service
resource "google_project_iam_member" "audit_service" {
  for_each = toset([
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/pubsub.publisher",
    "roles/pubsub.subscriber",
    "roles/cloudsql.client",
    "roles/redis.editor",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter"
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.audit_service.email}"
}

# Workload Identity binding
resource "google_service_account_iam_binding" "audit_service_workload_identity" {
  service_account_id = google_service_account.audit_service.name
  role               = "roles/iam.workloadIdentityUser"
  
  members = [
    "serviceAccount:${var.project_id}.svc.id.goog[${var.k8s_namespace}/${var.k8s_service_account}]"
  ]
}

# Secret Manager secrets
resource "google_secret_manager_secret" "db_password" {
  secret_id = "${local.name_prefix}-db-password"
  
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
  
  labels = local.common_labels
  
  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = var.db_password
}

resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "${local.name_prefix}-jwt-secret"
  
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
  
  labels = local.common_labels
}

resource "google_secret_manager_secret_version" "jwt_secret" {
  secret      = google_secret_manager_secret.jwt_secret.id
  secret_data = var.jwt_secret_key
}

# IAM binding for secret access
resource "google_secret_manager_secret_iam_binding" "audit_service_secrets" {
  for_each = toset([
    google_secret_manager_secret.db_password.secret_id,
    google_secret_manager_secret.jwt_secret.secret_id
  ])
  
  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  members   = ["serviceAccount:${google_service_account.audit_service.email}"]
}