locals {
  base_name         = "${var.project_name}-${var.environment}"
  sanitized_project = join("", regexall("[a-z0-9]", lower(var.project_name)))
}

resource "random_string" "suffix" {
  length  = 4
  upper   = false
  lower   = true
  numeric = true
  special = false
}

resource "azurerm_resource_group" "main" {
  name     = "${local.base_name}-rg"
  location = var.location
}

resource "azurerm_storage_account" "main" {
  name                            = substr("${local.sanitized_project}${var.environment}${random_string.suffix.result}", 0, 24)
  resource_group_name             = azurerm_resource_group.main.name
  location                        = azurerm_resource_group.main.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  allow_nested_items_to_be_public = false

  blob_properties {
    versioning_enabled = true
  }
}

resource "azurerm_key_vault" "main" {
  name                = "${local.base_name}-kv"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tenant_id           = var.aad_tenant_id
  sku_name            = "standard"

  rbac_authorization_enabled = false
  purge_protection_enabled   = true
  soft_delete_retention_days = 7
}

resource "azurerm_key_vault_access_policy" "admins" {
  for_each = toset(var.key_vault_admin_object_ids)

  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = var.aad_tenant_id
  object_id    = each.value

  secret_permissions = ["Get", "List", "Set", "Delete", "Recover"]
}

resource "azurerm_key_vault_secret" "communication_connection" {
  name         = "CommunicationConnectionString"
  value        = var.communication_connection_string
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_key_vault_secret" "communication_sender" {
  name         = "CommunicationSenderAddress"
  value        = var.communication_sender_address
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_key_vault_secret" "aad_client_secret" {
  name         = "AadClientSecret"
  value        = var.aad_client_secret
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_key_vault_secret" "config_json" {
  name         = "ConfigJson"
  value        = var.config_json
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_storage_container" "uploads" {
  name                  = "uploads"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = "private"
}

resource "azurerm_application_insights" "main" {
  name                = "${local.base_name}-appi"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  application_type    = "web"
}

resource "azurerm_service_plan" "function" {
  name                = "${local.base_name}-func-plan"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  sku_name            = "Y1"
}

resource "azurerm_service_plan" "web" {
  name                = "${local.base_name}-web-plan"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  sku_name            = "B1"
}

resource "azurerm_linux_function_app" "analyzer" {
  name                       = "${local.base_name}-func"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  service_plan_id            = azurerm_service_plan.function.id
  storage_account_name       = azurerm_storage_account.main.name
  storage_uses_managed_identity = true

  identity {
    type = "SystemAssigned"
  }

  site_config {
    application_stack {
      python_version = "3.10"
    }
    application_insights_key = azurerm_application_insights.main.instrumentation_key
  }

  app_settings = {
    FUNCTIONS_EXTENSION_VERSION           = "~4"
    FUNCTIONS_WORKER_RUNTIME              = "python"
    WEBSITE_RUN_FROM_PACKAGE              = "1"
    CONFIG_JSON                           = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.config_json.secret_uri_with_version})"
    AZURE_COMMUNICATION_CONNECTION_STRING = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.communication_connection.secret_uri_with_version})"
    EMAIL_SENDER_ADDRESS                  = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.communication_sender.secret_uri_with_version})"
    APPINSIGHTS_INSTRUMENTATIONKEY        = azurerm_application_insights.main.instrumentation_key
    APPLICATIONINSIGHTS_CONNECTION_STRING = azurerm_application_insights.main.connection_string
    AzureWebJobsStorage__credential       = "managedidentity"
    AzureWebJobsStorage__accountName      = azurerm_storage_account.main.name
    AzureWebJobsStorage__blobServiceUri   = "https://${azurerm_storage_account.main.name}.blob.core.windows.net"
    AzureWebJobsStorage__queueServiceUri  = "https://${azurerm_storage_account.main.name}.queue.core.windows.net"
  }
}

resource "azurerm_key_vault_access_policy" "function" {
  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = var.aad_tenant_id
  object_id    = azurerm_linux_function_app.analyzer.identity[0].principal_id

  secret_permissions = ["Get", "List"]
}

resource "azurerm_linux_web_app" "uploader" {
  name                = "${local.base_name}-web"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  service_plan_id     = azurerm_service_plan.web.id

  identity {
    type = "SystemAssigned"
  }

  site_config {
    application_stack {
      python_version = "3.10"
    }
    minimum_tls_version = "1.2"
    ftps_state          = "Disabled"
    http2_enabled       = true
    app_command_line    = "gunicorn --bind=0.0.0.0 --timeout 600 app:app"
  }

  app_settings = {
    SCM_DO_BUILD_DURING_DEPLOYMENT        = "1"
    STORAGE_ACCOUNT_NAME                  = azurerm_storage_account.main.name
    UPLOAD_CONTAINER_NAME                 = azurerm_storage_container.uploads.name
    AUTHORIZED_USER_EMAILS                = var.authorized_user_emails
    APPINSIGHTS_INSTRUMENTATIONKEY        = azurerm_application_insights.main.instrumentation_key
    APPLICATIONINSIGHTS_CONNECTION_STRING = azurerm_application_insights.main.connection_string
    AadClientSecret                       = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.aad_client_secret.secret_uri_with_version})"
  }

  auth_settings_v2 {
    auth_enabled           = true
    require_authentication = true
    default_provider       = "azureactivedirectory"

    login {
      token_store_enabled = true
    }

    active_directory_v2 {
      client_id                  = var.aad_client_id
      tenant_auth_endpoint       = "https://login.microsoftonline.com/${var.aad_tenant_id}/v2.0"
      client_secret_setting_name = "AadClientSecret"
    }
  }
}

resource "azurerm_key_vault_access_policy" "web" {
  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = var.aad_tenant_id
  object_id    = azurerm_linux_web_app.uploader.identity[0].principal_id

  secret_permissions = ["Get", "List"]
}

resource "azurerm_role_assignment" "web_blob_contributor" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_linux_web_app.uploader.identity[0].principal_id
}

resource "azurerm_role_assignment" "function_blob_contributor" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_linux_function_app.analyzer.identity[0].principal_id
}

resource "azurerm_role_assignment" "function_queue_contributor" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Queue Data Contributor"
  principal_id         = azurerm_linux_function_app.analyzer.identity[0].principal_id
}
