terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>4.0.0"
    }
  }
  required_version = ">=1.1.0"
}

provider "azurerm" {
  features {}
  subscription_id = "c003579a-e346-4356-a88e-7e50c4df4e6e"
}