output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "function_app_name" {
  value = azurerm_linux_function_app.analyzer.name
}

output "web_app_default_hostname" {
  value = azurerm_linux_web_app.uploader.default_hostname
}

output "storage_account_name" {
  value = azurerm_storage_account.main.name
}

output "upload_container_name" {
  value = azurerm_storage_container.uploads.name
}
