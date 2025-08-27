# Terraform Variables for Audit Log Framework GCP Infrastructure

# Project Configuration
variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "The GCP zone for zonal resources"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  default     = "development"
  
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production."
  }
}

# Network Configuration
variable "subnet_cidr" {
  description = "CIDR block for the main subnet"
  type        = string
  default     = "10.0.0.0/24"
}

variable "pods_cidr" {
  description = "CIDR block for GKE pods"
  type        = string
  default     = "10.1.0.0/16"
}

variable "services_cidr" {
  description = "CIDR block for GKE services"
  type        = string
  default     = "10.2.0.0/16"
}

variable "master_cidr" {
  description = "CIDR block for GKE master nodes"
  type        = string
  default     = "10.3.0.0/28"
}

# Database Configuration
variable "db_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-custom-2-4096"
}

variable "db_disk_size" {
  description = "Cloud SQL disk size in GB"
  type        = number
  default     = 100
}

variable "db_max_disk_size" {
  description = "Cloud SQL maximum disk size in GB"
  type        = number
  default     = 1000
}

variable "db_password" {
  description = "Password for the database user"
  type        = string
  sensitive   = true
}

# Redis Configuration
variable "redis_tier" {
  description = "Redis instance tier (BASIC or STANDARD_HA)"
  type        = string
  default     = "BASIC"
  
  validation {
    condition     = contains(["BASIC", "STANDARD_HA"], var.redis_tier)
    error_message = "Redis tier must be either BASIC or STANDARD_HA."
  }
}

variable "redis_memory_size" {
  description = "Redis memory size in GB"
  type        = number
  default     = 1
}

# GKE Configuration
variable "gke_release_channel" {
  description = "GKE release channel"
  type        = string
  default     = "STABLE"
  
  validation {
    condition     = contains(["RAPID", "REGULAR", "STABLE"], var.gke_release_channel)
    error_message = "GKE release channel must be one of: RAPID, REGULAR, STABLE."
  }
}

variable "gke_machine_type" {
  description = "Machine type for GKE nodes"
  type        = string
  default     = "e2-standard-4"
}

variable "gke_disk_size" {
  description = "Disk size for GKE nodes in GB"
  type        = number
  default     = 50
}

variable "gke_node_count" {
  description = "Initial number of GKE nodes"
  type        = number
  default     = 3
}

variable "gke_min_nodes" {
  description = "Minimum number of GKE nodes"
  type        = number
  default     = 1
}

variable "gke_max_nodes" {
  description = "Maximum number of GKE nodes"
  type        = number
  default     = 10
}

# BigQuery Configuration
variable "bigquery_location" {
  description = "BigQuery dataset location"
  type        = string
  default     = "US"
}

variable "bigquery_table_expiration_ms" {
  description = "Default table expiration in milliseconds (null for no expiration)"
  type        = number
  default     = null
}

variable "bigquery_partition_expiration_ms" {
  description = "Partition expiration in milliseconds (90 days default)"
  type        = number
  default     = 7776000000 # 90 days
}

# Security Configuration
variable "jwt_secret_key" {
  description = "JWT secret key for authentication"
  type        = string
  sensitive   = true
}

# Kubernetes Configuration
variable "k8s_namespace" {
  description = "Kubernetes namespace for the audit service"
  type        = string
  default     = "audit-system"
}

variable "k8s_service_account" {
  description = "Kubernetes service account name"
  type        = string
  default     = "audit-service"
}

# Environment-specific configurations
locals {
  environment_configs = {
    development = {
      db_tier              = "db-custom-1-2048"
      db_disk_size        = 20
      redis_tier          = "BASIC"
      redis_memory_size   = 1
      gke_machine_type    = "e2-standard-2"
      gke_node_count      = 1
      gke_min_nodes       = 1
      gke_max_nodes       = 3
    }
    staging = {
      db_tier              = "db-custom-2-4096"
      db_disk_size        = 50
      redis_tier          = "BASIC"
      redis_memory_size   = 2
      gke_machine_type    = "e2-standard-2"
      gke_node_count      = 2
      gke_min_nodes       = 1
      gke_max_nodes       = 5
    }
    production = {
      db_tier              = "db-custom-4-8192"
      db_disk_size        = 100
      redis_tier          = "STANDARD_HA"
      redis_memory_size   = 4
      gke_machine_type    = "e2-standard-4"
      gke_node_count      = 3
      gke_min_nodes       = 2
      gke_max_nodes       = 10
    }
  }
}

# Override defaults with environment-specific values
variable "use_environment_defaults" {
  description = "Whether to use environment-specific default values"
  type        = bool
  default     = true
}