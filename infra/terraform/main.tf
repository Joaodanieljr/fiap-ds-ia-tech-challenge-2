terraform {
  required_version = ">= 1.5"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0" # ou ~> 4.0 dependendo do seu ambiente
    }
  }

  backend "azurerm" {
    resource_group_name  = "rg-terraform-state"
    storage_account_name = "stterraformstate"
    container_name       = "tfstate"
    key                  = "alfabetizacao/terraform.tfstate"
  }
}

provider "azurerm" {
  features {}
}

# Grupo de Recursos
resource "azurerm_resource_group" "rg" {
  name     = "rg-tech-challenge-fase2"
  location = var.azure_region
  tags     = local.common_tags
}

# Azure Storage Account (Data Lake / Medalhão)
resource "azurerm_storage_account" "data_lake" {
  name                     = var.storage_account_name # Nome precisa ser globalmente único, minúsculo e sem traços
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  is_hns_enabled           = true # Habilita o formato Data Lake Storage Gen2 (Hierárquico)

  tags = local.common_tags
}

# Containers
resource "azurerm_storage_container" "bronze" {
  name                  = "bronze"
  storage_account_name  = azurerm_storage_account.data_lake.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "prata" {
  name                  = "prata"
  storage_account_name  = azurerm_storage_account.data_lake.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "ouro" {
  name                  = "ouro"
  storage_account_name  = azurerm_storage_account.data_lake.name
  container_access_type = "private"
}

# Policiamento de Ciclo de Vida
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

# 3. Azure Data Factory (ADF)
resource "azurerm_data_factory" "adf" {
  name                = "adf-alfabetizacao-pipeline"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  tags                = local.common_tags
}

# Locals para tags organizacionais
locals {
  common_tags = {
    Project     = "tech-challenge-fase2"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}