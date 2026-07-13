terraform {
  required_version = ">= 1.5"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }

  backend "azurerm" {}
}

provider "azurerm" {
  features {}
}

# Dados do contexto atual (tenant/subscription) — usado no Key Vault
data "azurerm_client_config" "current" {}

# Locals para tags organizacionais
locals {
  common_tags = {
    Project     = "tech-challenge-fase2"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# ============================================================
# Grupo de Recursos
# ============================================================
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.azure_region
  tags     = local.common_tags
}

# ============================================================
# Storage Account (Data Lake Gen2 — Arquitetura Medalhão)
# ============================================================
resource "azurerm_storage_account" "data_lake" {
  name                     = var.storage_account_name # Globalmente único, minúsculo, sem traços
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS" # FinOps: redundância local é suficiente para o caso
  is_hns_enabled           = true  # Habilita ADLS Gen2 (namespace hierárquico)

  tags = local.common_tags
}

# ============================================================
# Containers do Medalhão
# Nomes alinhados com o código dos notebooks (abfss://bronze@..., etc)
# ============================================================
resource "azurerm_storage_container" "bronze" {
  name                  = "bronze"
  storage_account_name  = azurerm_storage_account.data_lake.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "silver" {
  name                  = "silver"
  storage_account_name  = azurerm_storage_account.data_lake.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "gold" {
  name                  = "gold"
  storage_account_name  = azurerm_storage_account.data_lake.name
  container_access_type = "private"
}

# Filesystem auxiliar do Synapse (logs e arquivos internos do workspace)
resource "azurerm_storage_data_lake_gen2_filesystem" "synapse" {
  name               = "synapse"
  storage_account_id = azurerm_storage_account.data_lake.id
}

# ============================================================
# Política de Ciclo de Vida (FinOps)
# Bronze: dados brutos migram para camadas mais baratas com o tempo
# ============================================================
resource "azurerm_storage_management_policy" "data_lake_lifecycle" {
  storage_account_id = azurerm_storage_account.data_lake.id

  rule {
    name    = "bronze-to-cool-or-archive"
    enabled = true
    filters {
      prefix_match = ["bronze/"]
      blob_types   = ["blockBlob"]
    }
    actions {
      base_blob {
        tier_to_cool_after_days_since_modification_greater_than    = 30
        tier_to_archive_after_days_since_modification_greater_than = 90
      }
    }
  }
}

# ============================================================
# Synapse Workspace — motor de processamento PySpark
# ============================================================
resource "azurerm_synapse_workspace" "synapse" {
  name                                 = var.synapse_workspace_name
  resource_group_name                  = azurerm_resource_group.rg.name
  location                             = azurerm_resource_group.rg.location
  storage_data_lake_gen2_filesystem_id = azurerm_storage_data_lake_gen2_filesystem.synapse.id
  sql_administrator_login              = var.synapse_sql_admin_login
  sql_administrator_login_password     = var.synapse_sql_admin_password

  identity {
    type = "SystemAssigned" # Identidade gerenciada — usada no acesso ao Key Vault e Storage
  }

  tags = local.common_tags
}

# ============================================================
# Spark Pool — Small com pausa automática (FinOps)
# ============================================================
resource "azurerm_synapse_spark_pool" "sparkpool" {
  name                 = var.spark_pool_name
  synapse_workspace_id = azurerm_synapse_workspace.synapse.id
  node_size_family     = "MemoryOptimized"
  node_size            = "Small" # 4 vCores / 32 GB — suficiente para o volume do projeto
  spark_version        = "3.4"

  auto_scale {
    min_node_count = 3
    max_node_count = 10
  }

  auto_pause {
    delay_in_minutes = 5 # FinOps: zero custo ocioso após 5 min sem uso
  }

  tags = local.common_tags
}

# ============================================================
# Key Vault — credenciais fora do código
# ============================================================
resource "azurerm_key_vault" "kv" {
  name                      = var.key_vault_name
  resource_group_name       = azurerm_resource_group.rg.name
  location                  = azurerm_resource_group.rg.location
  tenant_id                 = data.azurerm_client_config.current.tenant_id
  sku_name                  = "standard"
  enable_rbac_authorization = true # Controle de acesso via RBAC (não access policies)

  tags = local.common_tags
}

# Secret: chave de acesso do Storage (lida pelos notebooks em runtime)
resource "azurerm_key_vault_secret" "storage_key" {
  name         = "storage-account-key"
  value        = azurerm_storage_account.data_lake.primary_access_key
  key_vault_id = azurerm_key_vault.kv.id

  depends_on = [azurerm_role_assignment.deployer_kv_admin]
}

# ============================================================
# RBAC — Permissões (princípio do menor privilégio)
# ============================================================

# Quem executa o Terraform precisa poder criar o secret
resource "azurerm_role_assignment" "deployer_kv_admin" {
  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Synapse lê o secret do Key Vault em runtime
resource "azurerm_role_assignment" "synapse_kv_reader" {
  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_synapse_workspace.synapse.identity[0].principal_id
}

# Synapse lê/grava no Data Lake
resource "azurerm_role_assignment" "synapse_storage_contributor" {
  scope                = azurerm_storage_account.data_lake.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_synapse_workspace.synapse.identity[0].principal_id
}

# ============================================================
# Outputs
# ============================================================
output "resource_group_name" {
  value = azurerm_resource_group.rg.name
}

output "storage_account_name" {
  value = azurerm_storage_account.data_lake.name
}

output "storage_account_id" {
  value = azurerm_storage_account.data_lake.id
}

output "synapse_workspace_name" {
  value = azurerm_synapse_workspace.synapse.name
}

output "synapse_studio_url" {
  value = "https://web.azuresynapse.net?workspace=${azurerm_synapse_workspace.synapse.id}"
}

output "key_vault_uri" {
  value = azurerm_key_vault.kv.vault_uri
}