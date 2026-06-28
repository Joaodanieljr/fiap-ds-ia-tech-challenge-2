variable "azure_region" {
  description = "Regiao Azure para deploy dos recursos"
  type        = string
  default     = "eastus" 
}

variable "storage_account_name" {
  description = "Nome da conta"
  type        = string
  default     = "alfabetizacao"
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
  default     = "dev"
}