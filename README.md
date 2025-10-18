# rm_analyzer_local

Tools for generating a summary email from a Rocket Money (formerly "Truebill") transactions CSV export so two people can split shared expenses. The project now includes a cloud-native Azure implementation in addition to the original local CLI.

## Cloud-native architecture

- **Uploader Web App (App Service + Flask)** – Authenticated via Azure AD, limited to trusted users, and uploads directly to Blob Storage with its managed identity.
- **Blob Storage** – Stores uploaded transaction exports and triggers analysis workflows.
- **Azure Function** – Parses the CSV, reuses the summarization logic, and sends HTML summaries with Azure Communication Services Email using secrets pulled from Key Vault.
- **Azure Key Vault** – Houses the Rocket Money configuration, Azure Communication credentials, the Function storage connection string, and the Azure AD client secret.
- **Terraform** – End-to-end infrastructure as code in `infra/terraform`.

See `docs/architecture.md` for the full design overview, required configuration, and deployment notes.

### Deploying to Azure

1. Populate the Terraform variables (AAD credentials, allowed user emails, Azure Communication Services secrets, `config_json`, and optional Key Vault admin object IDs).
2. `terraform init && terraform apply` inside `infra/terraform`.
3. Zip-deploy `src/webapp` to the created App Service (`az webapp deploy ...`).
4. Publish the Function App by deploying `src/function_app` (including the `rm_analyzer_local` package).
5. Upload a CSV through the web app and verify the summary email arrives.

## Legacy local CLI

The original CLI remains available for local execution and testing.

### Installation

Clone the repository and install runtime dependencies (if using the source):

## Installation

Clone the repository and install runtime dependencies (if using the source):

```sh
git clone https://github.com/rocjay1/rm-analyzer-local.git
cd rm-analyzer-local
pip install -r requirements.txt
```

### Configuration

Create a config at `~/.rma/config.json`. Minimal example:

```json
{
    "Categories": [
        "Dining & Drinks",
        "Groceries",
        "Bills & Utilities",
        "Travel & Vacation"
    ],
    "People": [
        {
            "Name": "George",
            "Accounts": [1234],
            "Email": "boygeorge@gmail.com"
        },
        {
            "Name": "Tootie",
            "Accounts": [1313],
            "Email": "tuttifruity@hotmail.com"
        }
    ]
}
```

Fields:

- `Categories`: list of transaction categories to include in summaries.
- `People`: list of participants with `Name`, `Accounts` (list of account suffixes), and `Email`.

### Usage

Examples below assume the executable is `rma` or you run the `cli.py` entrypoint with Python.

```sh
# Analyze the latest '*-transactions.csv' in your Downloads folder
~/Downloads/rma

# Analyze latest CSV in a specific folder
~/Downloads/rma /path/to/Transactions/

# Analyze a specific CSV file
~/Downloads/rma /path/to/Transactions/test-transactions.csv

# Or run from source
python cli.py /path/to/Transactions/test-transactions.csv
```

### Implementation notes

- Email sending (`send.py`) uses Gmail OAuth2 (based on the Google Gmail API quickstart and "Sending Email" guide).
- The Windows executable was produced with PyInstaller; the original CI built it on a Windows runner and uploaded the artifact.

### Testing

Run the unit and integration tests using Python's built-in unittest discovery:

```sh
python -m unittest discover -v tests
```

To run a single test module or test case:

```sh
# module
python -m unittest tests.test_send_unit

# specific test method
python -m unittest tests.test_send_unit.TestSendUnit.test_example_method
```
