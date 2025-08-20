# rm_analyzer_local

A small Python utility that generates a summary email from a Rocket Money (formerly 'Truebill') transactions CSV export to help two people split shared expenses.

## Status / Disclaimer

This codebase is no longer in active use or maintained. Use at your own risk.

Note: The original project used GitLab for CI/CD. That GitLab CI/CD pipeline is not functional after the repository was moved/pushed to GitHub.

## Quick facts

- Languages: Python 3
- Purpose: Parse a Rocket Money transactions CSV, categorize shared items, and produce a summary email.
- Distribution: A Windows executable was produced with PyInstaller in the original CI pipeline.

## Installation

Clone the repository and install runtime dependencies (if using the source):

```sh
git clone https://github.com/rocjay1/rm-analyzer-local.git
cd rm-analyzer-local
pip install -r requirements.txt
```

## Configuration

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

## Usage

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

## Implementation notes

- Email sending (`send.py`) uses Gmail OAuth2 (based on the Google Gmail API quickstart and "Sending Email" guide).
- The Windows executable was produced with PyInstaller; the original CI built it on a Windows runner and uploaded the artifact.

## Testing

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
