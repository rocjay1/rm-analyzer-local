variable "project_name" {
  description = "Short name for resource naming."
  type        = string
  default     = "rm-analyzer"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "prod"
}

variable "location" {
  description = "Azure region for resources."
  type        = string
  default     = "eastus"
}

variable "authorized_user_emails" {
  description = "Comma-delimited list of user principal names allowed to use the upload site."
  type        = string
}

variable "aad_tenant_id" {
  description = "Azure Active Directory tenant ID used for App Service authentication."
  type        = string
}

variable "aad_client_id" {
  description = "Client ID for the Azure AD application used by App Service authentication."
  type        = string
}

variable "aad_client_secret" {
  description = "Client secret for the Azure AD application used by App Service authentication."
  type        = string
  sensitive   = true
}

variable "communication_connection_string" {
  description = "Connection string for Azure Communication Services Email resource."
  type        = string
  sensitive   = true
}

variable "communication_sender_address" {
  description = "Verified sender address for Azure Communication Services."
  type        = string
}

variable "key_vault_admin_object_ids" {
  description = "Object IDs granted administrative access to Key Vault secrets."
  type        = list(string)
  default     = []
}

variable "config_json" {
  description = "JSON document containing category and participant configuration."
  type        = string
}
