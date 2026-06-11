# Reference existing resource group
data "azurerm_resource_group" "main" {
  name = var.resource_group_name
}

# Create Private AKS Cluster
resource "azurerm_kubernetes_cluster" "main" {
  name                   = var.kubernetes_cluster_name
  location               = data.azurerm_resource_group.main.location
  resource_group_name    = data.azurerm_resource_group.main.name
  dns_prefix             = var.dns_prefix
  kubernetes_version     = var.kubernetes_version
  local_account_disabled = var.local_account_disabled
  node_os_upgrade_channel = var.node_os_upgrade_channel

  dynamic "maintenance_window_node_os" {
    for_each = var.maintenance_window_node_os
    content {
      day_of_month = maintenance_window_node_os.value.day_of_month
      day_of_week  = maintenance_window_node_os.value.day_of_week
      duration     = maintenance_window_node_os.value.duration
      frequency    = maintenance_window_node_os.value.frequency
      interval     = maintenance_window_node_os.value.interval
      start_date   = maintenance_window_node_os.value.start_date
      start_time   = maintenance_window_node_os.value.start_time
      utc_offset   = maintenance_window_node_os.value.utc_offset
      week_index   = maintenance_window_node_os.value.week_index
    }
  }
  # # Virtual Nodes
  # aci_connector_linux {
  #   subnet_name = var.vn-subnet-id
  # }
  # Private cluster configuration - Core Requirement #1
  private_cluster_enabled             = var.private_cluster_enabled 
  private_cluster_public_fqdn_enabled = var.private_cluster_public_fqdn_enabled
  oidc_issuer_enabled                 = var.oidc_issuer_enabled
  workload_identity_enabled           = var.workload_identity_enabled
  image_cleaner_enabled               = var.image_cleaner_enabled
  image_cleaner_interval_hours        = var.image_cleaner_interval_hours
  sku_tier                            = var.sku_tier
  support_plan                        = var.support_plan

  key_vault_secrets_provider {
    secret_rotation_enabled  = var.secret_rotation_enabled
    secret_rotation_interval = var.secret_rotation_interval
  }
  oms_agent {
    log_analytics_workspace_id = var.log_analytics_workspace_id
  }
  azure_monitor_metrics {
    enabled = var.monitor_metrics_enabled
  }
  # Network profile configuration - Core Requirements #2, #3, #4
  network_profile {
    network_plugin      = var.network_plugin
    network_plugin_mode = var.network_plugin_mode
    load_balancer_sku   = var.load_balancer_sku
    outbound_type       = var.outbound_type
    service_cidr        = var.service_cidr
    dns_service_ip      = var.dns_service_ip
  }
  azure_active_directory_role_based_access_control {
    admin_group_object_ids = var.admin_group_object_ids
    azure_rbac_enabled     = var.azure_rbac_enabled
    tenant_id              = var.tenant_id
  }
  identity {
    type = var.identity_type
  }

  default_node_pool {
    name           = var.default_node_pool_name
    node_count     = var.node_count
    vm_size        = var.node_vm_size
    vnet_subnet_id = var.aks_subnet_id
    zones          = var.zones
    os_sku         = var.os_sku
  }

  tags = {
    Name                = var.tag_name
    Scope               = var.tag_scope
    Location            = var.tag_location
    Client              = var.client
    Environment         = var.Environment
    Placement           = var.Placement
    Compliance          = var.Compliance
    "Data Classification" = var.data_classification
    "Job Code"            = var.job_Code
    Hyperion            = var.Hyperion
    RITM                = var.RITM
    ApplicationOwner    = var.ApplicationOwner
    SystemOwner         = var.SystemOwner
    Engineer            = var.Engineer
  }
}

resource "azurerm_kubernetes_cluster_node_pool" "workerpool" {
  name                  = var.usernode_pool
  kubernetes_cluster_id = azurerm_kubernetes_cluster.main.id
  vm_size               = var.vm_size
  node_count            = var.node_count
  zones                 = var.zones
}

resource "azurerm_container_registry" "acr" {
  name                = var.container_registry_name
  resource_group_name = data.azurerm_resource_group.main.name
  location            = data.azurerm_resource_group.main.location
  sku                 = var.sku
}