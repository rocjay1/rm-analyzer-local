# rm_analyzer

## Description

Generates a summary email of a Rocket Money transactions export. Helps two people evenly split monthly expenses. 

**Notes**
- The main project and CI/CD is hosted at GitLab. The project is push-mirrored to GitHub.
- Gmail is implemented with OAuth2: [Python quickstart](https://developers.google.com/gmail/api/quickstart/python). `send.py` is based on [Sending Email](https://developers.google.com/gmail/api/guides/sending).
- PyInstaller is used to create the executable. [Using PyInstaller to Easily Distribute Python Applications](https://realpython.com/pyinstaller-python/#using-pyinstaller) is a fantastic resource.
- To build the Windows executable, a build pipeline triggers PyInstaller to run on a Windows Server VM and captures the executable as an artifact. See [Get started with GitLab CI/CD](https://docs.gitlab.com/ee/ci/) and [Hosted runners on Windows](https://docs.gitlab.com/ee/ci/runners/hosted_runners/windows.html).

## Installation

Windows: download executable at [rma.exe](https://gitlab.com/jasonroc19/rm_analyzer/-/jobs/8251519334/artifacts/raw/dist/rma.exe).

## Configuration

Create `~/.rma/config.json`. Example:

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
            "Accounts": [
                1234
            ],
            "Email": "boygeorge@gmail.com"
        },
        {
            "Name": "Tootie",
            "Accounts": [
                1313
            ],
            "Email": "tuttifruity@hotmail.com"
        }
    ]
}
```

## Usage
```
# Open shell
# Executable located at '~/Downloads', e.g.

# Analyze latest '*-transactions.csv' in the Downloads folder
~/Downloads/rma

# Analyze latest CSV saved to a dedicated folder
~/Downloads/rma /Users/roccodavino/Documents/Transactions/

# Analyze a particular CSV
~/Downloads/rma /Users/roccodavino/Documents/Transactions/test-transactions.csv
```
