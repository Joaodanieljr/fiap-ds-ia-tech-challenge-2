variable "azure_region" {
  description = "Regiao Azure para deploy dos recursos"
  type        = string
  default     = "brazilsouth" # Alinhado com a infra real (Brazil South)
}

variable "resource_group_name" {
  description = "Nome do resource group a ser criado"
  type        = string
  default     = "rg-alfabetizacao"
}

variable "storage_account_name" {
  description = "Nome da Storage Account (globalmente único, minúsculo, sem traços)"
  type        = string
  default     = "stalfalfabetizacao"
}

variable "synapse_workspace_name" {
  description = "Nome do Synapse Workspace (motor PySpark da pipeline)"
  type        = string
  default     = "synapse-alfabetizacao"
}

variable "spark_pool_name" {
  description = "Nome do Spark Pool do Synapse"
  type        = string
  default     = "sparkpool"
}

variable "key_vault_name" {
  description = "Nome do Azure Key Vault (globalmente único)"
  type        = string
  default     = "kv-alfabetizacao"
}

variable "synapse_sql_admin_login" {
  description = "Login do administrador SQL do Synapse"
  type        = string
  default     = "sqladminuser"
}

variable "synapse_sql_admin_password" {
  description = "Senha do administrador SQL do Synapse — NUNCA definir default; passar via terraform.tfvars ou variável de ambiente TF_VAR_synapse_sql_admin_password"
  type        = string
  sensitive   = true
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
  default     = "dev"
}