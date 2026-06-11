module "aks" {
  source                  = "./modules/aks"
  resource_group_name     = "ANN-MUE1-RG01-DEV-PAAS"
  kubernetes_cluster_name = "annmue1pocdev-aks"
  dns_prefix              = "annmue1-poc-dev-dns"
  sku_tier                = "Free"
  support_plan            = "KubernetesOfficial"
  zones                   = ["1"]
  kubernetes_version      = "1.32.6"
  local_account_disabled  = true
  node_os_upgrade_channel = "SecurityPatch"
  maintenance_window_node_os = [
    {
      day_of_month = 0
      day_of_week  = "Sunday"
      duration     = 8
      frequency    = "RelativeMonthly"
      interval     = 1
      start_date   = "2025-09-26T00:00:00Z"
      start_time   = "00:00"
      utc_offset   = "+00:00"
      week_index   = "First"
  }]

  admin_group_object_ids = [
    "43002588-0df5-4642-9d3f-cc664a708fbc"
  ]
  azure_rbac_enabled = true
  tenant_id          = "41eb501a-f671-4ce0-a5bf-b64168c3705f"

  private_cluster_enabled             = true
  private_cluster_public_fqdn_enabled = true
  oidc_issuer_enabled                 = true
  workload_identity_enabled           = true
  image_cleaner_enabled               = false
  #  image_cleaner_interval_hours        = 24

  monitor_metrics_enabled            = true
  oms_agent_enabled                  = true
  prometheus_addon_enabled          = true
  managed_grafana_enabled           = true

  log_analytics_workspace_id = "/subscriptions/22166e93-ca89-4b2b-8c93-10ad0d60d498/resourcegroups/ann-mue1-rg01-dev-paas/providers/microsoft.operationalinsights/workspaces/annmue1pocdevaks-la"

  network_plugin      = "azure"
  network_plugin_mode = "overlay"
  load_balancer_sku   = "standard"
  outbound_type       = "userDefinedRouting"
  service_cidr        = "10.0.3.0/24"
  dns_service_ip      = "10.0.3.10"
  identity_type       = "SystemAssigned"

  default_node_pool_name = "SystemPool"
  node_count             = 2
#  node_vm_size           = "Standard_A4_v2"
  node_vm_size           = "Standard_D4ds_v5"

  aks_subnet_id = ""
#  aks_subnet_id = "/subscriptions/5148fbf8-1b98-4a91-ad83-86ddce3a62e1/resourceGroups/OIT-MUE1-RG01-DEV-NET/providers/Microsoft.Network/virtualNetworks/OIT-MUE1-RG01-DEV-NET-VN01/subnets/OIT-MUE1-RG01-DEV-NET-VN01-AKSCLUSTER-sn"
#  aks_subnet_id = "/subscriptions/2037140b-5f66-431c-bdeb-9887110b8b15/resourceGroups/OMN-MEW1-RG01-DEV-NET/providers/Microsoft.Network/virtualNetworks/OMN-MEW1-RG01-DEV-NET-VN01/subnets/OMN-MEW1-RG01-DEV-NET-VN01-PRIVATE-sn"
  secret_rotation_enabled  = false
  secret_rotation_interval = "2m"

  node_resource_group = "OIT-MUE1-RG01-DEV-AKS"

  usernode_pool = "NodePool1"
  vm_size       = "Standard_D4ds_v5"
  os_sku        = "Ubuntu"

  container_registry_name = "annmue1pocdev-creg"
  sku                     = "Standard"

 # vn-subnet-id = "/subscriptions/5148fbf8-1b98-4a91-ad83-86ddce3a62e1/resourceGroups/OIT-MUE1-RG01-DEV-NET/providers/Microsoft.Network/virtualNetworks/OIT-MUE1-RG01-DEV-NET-VN01/subnets/OIT-MUE1-RG01-DEV-NET-VN01-AKSNODE-sn"

  # Tags

  tag_name            = "annmue1pocdev-aks"
  tag_scope           = "Regional"
  tag_location        = "MUE1 - East US - Virginia"
  client              = "OMG Annalect Omni Platform"
  Environment         = "Development"
  Placement           = "Private"
  Compliance          = "NONE"
  data_classification = "internal"
  job_Code            = "5usOMDmsg"
  Hyperion            = "5usOMDmsg"
  RITM                = "RITM3835213"
  ApplicationOwner    = "gadupu.kumar@omc.com"
  SystemOwner         = "john.briscoe@omc.com"
  Engineer            = "Ramanaia.Konatham@omc.com"

}