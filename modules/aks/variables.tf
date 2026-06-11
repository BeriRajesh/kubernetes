variable "resource_group_name" {
  description = "The name of the existing resource group"
  type        = string
}

variable "kubernetes_cluster_name" {
  description = "The name of the AKS Kubernetes cluster"
  type        = string
}

variable "dns_prefix" {
  description = "DNS prefix for the AKS cluster"
  type        = string
}

variable "kubernetes_version" {
  description = "The version of Kubernetes to use for the AKS cluster"
  type        = string
  default     = "1.24.3"
}

variable "local_account_disabled" {
  description = "Whether local accounts should be disabled on the AKS cluster"
  type        = bool
  default     = true
}

variable "private_cluster_enabled" {
  description = "Enable private AKS cluster"
  type        = bool
  default     = true
}

variable "private_cluster_public_fqdn_enabled" {
  description = "Enable public FQDN for private AKS cluster"
  type        = bool
  default     = true
}

variable "oidc_issuer_enabled" {
  description = "Enable OIDC issuer URL"
  type        = bool
  default     = true
}

variable "workload_identity_enabled" {
  description = "Enable workload identity"
  type        = bool
  default     = true
}

variable "image_cleaner_enabled" {
  description = "Enable image cleaner"
  type        = bool
  default     = true
}

variable "image_cleaner_interval_hours" {
  description = "Interval in hours for image cleaner to run"
  type        = number
  default     = 24
}

variable "sku_tier" {
  description = "The SKU tier of the AKS cluster (e.g., Free, Paid, Premium)"
  type        = string
  default     = "Premium"
}

variable "support_plan" {
  description = "The support plan for the AKS cluster"
  type        = string
  default     = "AKSLongTermSupport"
}

variable "log_analytics_workspace_id" {
  description = "Log Analytics Workspace resource ID for Azure Monitor integration"
  type        = string
}

variable "network_plugin" {
  description = "The network plugin to use (e.g., azure, kubenet)"
  type        = string
  default     = "azure"
}

variable "network_plugin_mode" {
  description = "The network plugin mode (e.g., overlay, bridge)"
  type        = string
  default     = "overlay"
}

variable "load_balancer_sku" {
  description = "SKU for the load balancer (e.g., standard)"
  type        = string
  default     = "standard"
}

variable "outbound_type" {
  description = "Outbound type for network profile (e.g., userDefinedRouting, managedNATGateway)"
  type        = string
  default     = "userDefinedRouting"
}

variable "service_cidr" {
  description = "CIDR for the Kubernetes services"
  type        = string
  default     = "10.0.0.0/16"
}

variable "dns_service_ip" {
  description = "DNS service IP address"
  type        = string
  default     = "10.0.0.10"
}

variable "azure_rbac_enabled" {
  description = "Enable Azure RBAC for AKS"
  type        = bool
  default     = true
}

variable "tenant_id" {
  description = "Azure Active Directory tenant ID"
  type        = string
}

variable "identity_type" {
  description = "The type of managed identity to use (SystemAssigned or UserAssigned)"
  type        = string
  default     = "SystemAssigned"
}

variable "default_node_pool_name" {
  description = "Name of the default node pool"
  type        = string
  default     = "default"
}

variable "node_count" {
  description = "Number of nodes in the node pool"
  type        = number
  default     = 3
}

variable "node_vm_size" {
  description = "VM size for default node pool"
  type        = string
  default     = "Standard_DS2_v2"
}

variable "zones" {
  description = "Availability zones to deploy the AKS nodes"
  type        = list(string)
  default     = ["1"]
}

variable "aks_subnet_id" {
  description = "Subnet ID where AKS nodes will be deployed"
  type        = string
}

variable "tags" {
  description = "Tags to apply to the AKS resources"
  type        = map(string)
  default     = {}
}

variable "usernode_pool" {
  description = "Name of the user node pool"
  type        = string
  default     = "workerpool"
}

variable "vm_size" {
  description = "VM size for user node pool"
  type        = string
  default     = "Standard_D2s_v3"
}

variable "container_registry_name" {
  description = "Name of the Azure Container Registry"
  type        = string
}

variable "sku" {
  description = "SKU for Azure Container Registry"
  type        = string
  default     = "Standard"
}
variable "tag_name" {
  description = "Value for the 'Name' tag"
  type        = string
}

variable "tag_scope" {
  description = "Value for the 'Scope' tag"
  type        = string
}

variable "tag_location" {
  description = "Value for the 'Location' tag"
  type        = string
}

variable "client" {
  description = "Value for the 'Client' tag"
  type        = string
}

variable "Environment" {
  description = "Value for the 'Environment' tag"
  type        = string
}

variable "Placement" {
  description = "Value for the 'Placement' tag"
  type        = string
}

variable "Compliance" {
  description = "Value for the 'Compliance' tag"
  type        = string
}

variable "data_classification" {
  description = "Value for the 'Data Classification' tag"
  type        = string
}

variable "job_Code" {
  description = "Value for the 'Job Code' tag"
  type        = string
}

variable "Hyperion" {
  description = "Value for the 'Hyperion' tag"
  type        = string
}

variable "RITM" {
  description = "Value for the 'RITM' tag"
  type        = string
}

variable "ApplicationOwner" {
  description = "Value for the 'ApplicationOwner' tag"
  type        = string
}

variable "SystemOwner" {
  description = "Value for the 'SystemOwner' tag"
  type        = string
}

variable "Engineer" {
  description = "Value for the 'Engineer' tag"
  type        = string
}

variable "node_os_upgrade_channel" {
  description = "The upgrade channel for node OS."
  type        = string
  default     = "SecurityPatch"
}

variable "node_resource_group" {
  description = "Resource group for the nodes."
  type        = string
  default     = "OIT-MUE1-RG01-DEV-AKS"
}

variable "admin_group_object_ids" {
  description = "List of Azure AD admin group object IDs."
  type        = list(string)
  default     = ["93c77ab1-70b3-46a1-a05c-1f11975c7d03"]
}

variable "secret_rotation_enabled" {
  description = "Enable secret rotation for key vault."
  type        = bool
  default     = false
}

variable "secret_rotation_interval" {
  description = "Secret rotation interval."
  type        = string
  default     = "2m"
}

variable "maintenance_window_node_os" {
  description = "List of maintenance window configurations for node OS."
  type = list(object({
    day_of_month = number
    day_of_week  = string
    duration     = number
    frequency    = string
    interval     = number
    start_date   = string
    start_time   = string
    utc_offset   = string
    week_index   = string
  }))
  default = [
    {
      day_of_month = 0
      day_of_week  = "Sunday"
      duration     = 8
      frequency    = "RelativeMonthly"
      interval     = 1
      start_date   = "2025-09-04T00:00:00Z"
      start_time   = "00:00"
      utc_offset   = "+00:00"
      week_index   = "First"
    }
  ]
}

# variable "vn-subnet-id" {
#   description = "Subnet name for ACI connector Linux."
#   type        = string
#   default     = ""
# }

variable "os_sku" {
  description = "Node OS SKU."
  type        = string
  default     = "Ubuntu"
}

variable "monitor_metrics_enabled" {
  type    = bool
  default = false
}

variable "oms_agent_enabled" {
  type    = bool
  default = false
}

variable "prometheus_addon_enabled" {
  type    = bool
  default = false
}

variable "managed_grafana_enabled" {
  type    = bool
  default = false
}

