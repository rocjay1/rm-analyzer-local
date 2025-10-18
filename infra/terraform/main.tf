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
  storage_account_access_key = azurerm_storage_account.main.primary_access_key

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
    AzureWebJobsStorage                   = azurerm_storage_account.main.primary_connection_string
    WEBSITE_RUN_FROM_PACKAGE              = "1"
    CONFIG_JSON                           = var.config_json
    AZURE_COMMUNICATION_CONNECTION_STRING = var.communication_connection_string
    EMAIL_SENDER_ADDRESS                  = var.communication_sender_address
    APPINSIGHTS_INSTRUMENTATIONKEY        = azurerm_application_insights.main.instrumentation_key
    APPLICATIONINSIGHTS_CONNECTION_STRING = azurerm_application_insights.main.connection_string
  }
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
    STORAGE_ACCOUNT_CONNECTION_STRING     = azurerm_storage_account.main.primary_connection_string
    UPLOAD_CONTAINER_NAME                 = azurerm_storage_container.uploads.name
    AUTHORIZED_USER_EMAILS                = var.authorized_user_emails
    APPINSIGHTS_INSTRUMENTATIONKEY        = azurerm_application_insights.main.instrumentation_key
    APPLICATIONINSIGHTS_CONNECTION_STRING = azurerm_application_insights.main.connection_string
    AadClientSecret                       = var.aad_client_secret
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
