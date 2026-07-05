variable "azure_region" {
  description = "Regiao Azure para deploy dos recursos"
  type        = string
  default     = "eastus" 
}

variable "resource_group_name" {
  description = "Nome do resource group a ser criado"
  type        = string
  default     = "rg-tech-challenge-fase2"
}

variable "storage_account_name" {
  description = "Nome da Storage Account (deve ser globalmente único, minúsculo e sem traços)"
  type        = string
  default     = "alfabetizacao"
}

variable "data_factory_name" {
  description = "Nome do Azure Data Factory"
  type        = string
  default     = "adf-alfabetizacao-pipeline"
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
  default     = "dev"
}