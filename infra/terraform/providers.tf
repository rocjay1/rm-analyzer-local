terraform {
  required_version = ">= 1.3"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 3.70"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = ">= 2.46"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.5"
    }
  }
}

provider "azurerm" {
  features {}
}

provider "azuread" {}
