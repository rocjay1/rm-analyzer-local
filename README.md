# rm_analyzer_local

Cloud-native tooling that analyzes Rocket Money (formerly "Truebill") transaction exports and emails a summary so two people can split shared expenses. The legacy desktop CLI has been retired; the Azure-hosted workflow is now the single implementation.

## Architecture

- **Uploader Web App (App Service + Flask)** authenticates via Azure AD and saves CSV uploads to Blob Storage with its managed identity.
- **Blob Storage** stores uploaded exports and triggers downstream processing.
- **Azure Function** (Python) parses the CSV, hydrates an HTML summary, and sends it using Azure Communication Services Email.
- **Azure Key Vault** holds the Rocket Money configuration JSON and other secrets referenced by the apps.
- **Terraform** (`infra/terraform`) provisions the complete environment.

See `docs/architecture.md` for resource details and deployment notes.

## Deployment

1. Populate Terraform variables (AAD credentials, allowed user emails, Communication Services secrets, `config_json`, and optional Key Vault admin object IDs).
2. Run `terraform init && terraform apply` inside `infra/terraform`.
3. Zip-deploy `src/webapp` to the created web app (`az webapp deploy ...`).
4. Publish the Function App by deploying the contents of `src/function_app`.
5. Upload a Rocket Money CSV through the site and confirm the summary email arrives.

## Local Development

- Install tooling for linting/utilities:
  ```sh
  pip install -r requirements.txt
  ```
- Function runtime dependencies live in `src/function_app/requirements.txt`; web app dependencies live in `src/webapp/requirements.txt`.
- Provide a Rocket Money configuration JSON (same schema as before) via the `CONFIG_JSON` environment variable or Key Vault secret when running locally.

The summarization logic now resides in `src/function_app/summarizer.py` and is shared directly by the blob-triggered function. Legacy package code, CLI tooling, and GitLab CI assets have been removed to keep the repository focused on the Azure-native workflow.
