# Cloud Architecture Overview

## Goals

- Allow two authenticated users to upload Rocket Money exports from any device.
- Automate analysis and summary email delivery after each upload.
- Manage all Azure resources declaratively with Terraform.

## High-Level Flow

1. A user signs into the uploader web app using Azure AD.
2. The web app uploads the CSV to a private Blob Storage container.
3. A Blob-triggered Azure Function runs the analyzer logic.
4. The function produces the summary and sends an email using Azure Communication Services Email.

## Azure Resources

- **Resource Group** – logical container for all components.
- **Storage Account**
  - Blob container `uploads` receives user files.
  - The same account backs the Function App's runtime storage.
- **Linux Function App**
  - Python 3.10 runtime.
  - Loads the summarization utilities from `src/function_app/summarizer.py`.
  - Reads configuration and other secrets via Key Vault references.
  - Sends HTML summaries through Azure Communication Services.
- **Linux Web App**
  - Hosts the Flask uploader (`src/webapp`).
  - Authentication enforced via App Service Authentication + Azure AD.
  - Uploads files to Blob Storage using its managed identity (no connection strings at runtime).
- **Key Vault**
  - Stores the Rocket Money config JSON, Azure Communication credentials, the Azure AD client secret, and the Function App storage connection string.
  - Managed identities for the web app and Function App have `Get/List` permissions; optional admins can be granted additional access.
- **Application Insights**
  - Centralized telemetry for both the web app and the function.
- **Azure Communication Services Email**
  - Provides transactional email delivery. Connection string and sender address are injected through app settings.

## Configuration

The Terraform module (`infra/terraform`) expects the following inputs:

- `authorized_user_emails` – comma-separated list of user principal names allowed to upload files.
- `aad_tenant_id`, `aad_client_id`, `aad_client_secret` – credentials for the Azure AD app that protects the web frontend.
- `communication_connection_string`, `communication_sender_address` – values from an Azure Communication Services Email resource.
- `config_json` – JSON payload containing the categories and people definition used by the analyzer (same structure as the legacy `~/.rma/config.json`).
- `key_vault_admin_object_ids` – optional list of Azure AD object IDs granted full secret access.

Secrets such as the Azure Communication connection string and Azure AD client secret should be supplied via environment variables or a secure backend (e.g., Azure Key Vault) when running `terraform apply`.

## Deployment Notes

1. Initialize Terraform inside `infra/terraform`.
2. Provide the required variables (via `terraform.tfvars`, CLI flags, or environment variables).
3. Deploy the uploader web application by zip-deploying the contents of `src/webapp`.
4. Deploy the Function App by publishing `src/function_app`.
5. Verify:
   - Users can authenticate and upload files.
   - Blob uploads trigger the Function App automatically.
   - Summary emails arrive via Azure Communication Services.
