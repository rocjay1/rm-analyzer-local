"""Tests for the summarizer module."""

# pylint: disable=redefined-outer-name

from __future__ import annotations

# Standard library imports
import sys
from io import StringIO
from pathlib import Path
from typing import Dict, List

# Third-party imports
import pandas as pd
import pandas.testing as tm
import pytest

# Make sure the application code is importable when pytest discovers tests
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
FUNCTION_APP_DIR = SRC_DIR / "function_app"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(FUNCTION_APP_DIR) not in sys.path:
    sys.path.insert(0, str(FUNCTION_APP_DIR))

from shared_code import summarizer  # noqa: E402  pylint: disable=wrong-import-position


@pytest.fixture
def summarizer_config() -> Dict[str, List]:
    """Return a representative configuration with two people and categories."""
    return {
        "Categories": ["Dining & Drinks", "Groceries"],
        "People": [
            {
                "Name": "Alice",
                "Accounts": [1111],
                "Email": "alice@example.com",
            },
            {
                "Name": "Bob",
                "Accounts": [2222],
                "Email": "bob@example.com",
            },
        ],
    }


@pytest.fixture
def transactions_df() -> pd.DataFrame:
    """Provide a fixture containing sample Rocket Money transactions."""
    return pd.DataFrame(
        [
            {
                "Date": "2024-01-01",
                "Category": "Dining & Drinks",
                "Account Number": 1111,
                "Amount": 50.0,
                "Ignored From": None,
            },
            {
                "Date": "2024-01-02",
                "Category": "Dining & Drinks",
                "Account Number": 2222,
                "Amount": 30.0,
                "Ignored From": None,
            },
            {
                "Date": "2024-01-03",
                "Category": "Groceries",
                "Account Number": 1111,
                "Amount": 80.0,
                "Ignored From": None,
            },
            {
                "Date": "2024-01-04",
                "Category": "Groceries",
                "Account Number": 2222,
                "Amount": 20.0,
                "Ignored From": None,
            },
            {
                "Date": "2024-01-05",
                "Category": "Travel",
                "Account Number": 1111,
                "Amount": 999.0,
                "Ignored From": None,
            },
            {
                "Date": "2024-01-06",
                "Category": "Dining & Drinks",
                "Account Number": 1111,
                "Amount": 10.0,
                "Ignored From": "Manual",
            },
        ]
    )


@pytest.fixture
def summary_df(transactions_df: pd.DataFrame, summarizer_config: Dict[str, List]) -> pd.DataFrame:
    """Build the summary DataFrame using the fixture data."""
    return summarizer.build_summary_df(transactions_df, summarizer_config)


def test_build_summary_df_groups_totals_per_owner_and_category(summary_df: pd.DataFrame) -> None:
    """Ensure per-person, per-category totals match the expected pivot output."""
    expected = pd.DataFrame(
        {
            "Dining & Drinks": {"Alice": 50.0, "Bob": 30.0},
            "Groceries": {"Alice": 80.0, "Bob": 20.0},
        }
    )
    expected.index.name = "Owner"
    expected.columns.name = "Category"
    tm.assert_frame_equal(summary_df, expected, check_like=True)


def test_write_email_body_renders_difference_row(
    summary_df: pd.DataFrame, summarizer_config: Dict[str, List]
) -> None:
    """Verify the email body includes the net-difference row for two people."""
    totals = summary_df.sum(axis=1)
    html = summarizer.write_email_body(summary_df, totals, summarizer_config)

    assert "<th>Dining &amp; Drinks</th>" in html
    assert "<td>Difference</td>" in html
    assert "<td>130.00</td>" in html  # Alice total
    assert "Alice owes Bob" in html


def test_build_summary_reads_csv_and_returns_payload(
    transactions_df: pd.DataFrame, summarizer_config: Dict[str, List]
) -> None:
    """Check that CSV uploads convert to the expected email payload."""
    csv_buffer = StringIO()
    transactions_df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    destinations, subject, html = summarizer.build_summary(csv_buffer, summarizer_config)

    assert destinations == ["alice@example.com", "bob@example.com"]
    assert subject == "Transactions Summary: 01/01 - 01/06"
    assert "<td>Difference</td>" in html
    assert "Dining &amp; Drinks" in html


def test_write_email_body_escapes_html_entities() -> None:
    """Confirm the email body properly HTML-escapes dangerous content."""
    summary_df = pd.DataFrame(
        {
            "<script>alert(1)</script>": {
                "<img src=x onerror=y>": 25.0,
                "<svg onload=alert(2)>": 75.0,
            }
        }
    )
    summary_df.index.name = "Owner"
    summary_df.columns.name = "Category"
    totals = summary_df.sum(axis=1)
    config = {
        "Categories": ["<script>alert(1)</script>"],
        "People": [
            {"Name": "<img src=x onerror=y>", "Accounts": [123], "Email": "safe@example.com"},
            {"Name": "<svg onload=alert(2)>", "Accounts": [456], "Email": "safe2@example.com"},
        ],
    }

    html = summarizer.write_email_body(summary_df, totals, config)

    assert "<th>&lt;script&gt;alert(1)&lt;/script&gt;</th>" in html
    assert "<td>&lt;img src=x onerror=y&gt;</td>" in html
    assert "<td>&lt;svg onload=alert(2)&gt;</td>" in html
    owes_sentence = "&lt;img src=x onerror=y&gt; owes &lt;svg onload=alert(2)&gt;: 25.00."
    assert owes_sentence in html
    assert "<img src=x onerror=y>" not in html
    assert "<svg onload=alert(2)>" not in html
