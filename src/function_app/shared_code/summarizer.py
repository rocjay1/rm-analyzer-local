"""Utilities for building Rocket Money transaction summaries."""

from __future__ import annotations

from typing import Dict, Iterable, IO, List, Tuple, Union

import html
import os
import pandas as pd  # pylint: disable=import-error

CsvInput = Union[str, os.PathLike[str], IO[str], IO[bytes]]


def _build_owners_dict(config: Dict[str, Iterable]) -> Dict[str, Dict[int, str]]:
    """Build dictionary containing account owner and number from config."""
    owners_dict: Dict[str, Dict[int, str]] = {"Owner": {}, "Account Number": {}}
    index = 0
    for person in config.get("People", []):
        for account in person.get("Accounts", []):
            owners_dict["Owner"][index] = person.get("Name", "")
            owners_dict["Account Number"][index] = account
            index += 1
    return owners_dict


def build_summary_df(df: pd.DataFrame, config: Dict[str, Iterable]) -> pd.DataFrame:
    """Return pivot table of totals per owner/category."""
    owners_df = pd.DataFrame(_build_owners_dict(config))
    categories = config.get("Categories", [])

    df_filtered = df[df["Ignored From"].isnull() & df["Category"].isin(categories)]
    df_merged = pd.merge(df_filtered, owners_df, how="left", on="Account Number")
    df_agg = df_merged.groupby(["Category", "Owner"])[["Amount"]].sum().reset_index()
    df_pivot = (
        df_agg.pivot(index="Owner", columns="Category", values="Amount")
        .fillna(0)
        .sort_index(axis=0)
    )
    return df_pivot


def _to_money(value: float) -> str:
    """Format a numeric value as currency string."""
    return f"{value:.2f}"


def _write_summary_sentence(summary_df: pd.DataFrame, totals: pd.Series) -> str:
    """Generate the concluding summary sentence."""
    people: List[str] = list(summary_df.index)
    if len(people) == 2:
        p1, p2 = people
        amount = 0.5 * totals.sum() - totals[p1]
        return f"{p1} owes {p2}: {_to_money(amount)}."

    return "See the table above for transaction totals by person, category."


def write_email_body(
    summary_df: pd.DataFrame, totals: pd.Series, config: Dict[str, Iterable]
) -> str:
    """Return HTML body for summary email."""
    configured_categories: List[str] = [
        category
        for category in config.get("Categories", [])
        if category in summary_df.columns
    ]
    remaining_categories = [
        category
        for category in summary_df.columns
        if category not in configured_categories
    ]
    categories: List[str] = [*configured_categories, *remaining_categories]
    people: List[str] = list(summary_df.index)

    body_parts: List[str] = [
        """\
<!DOCTYPE html>
<html>
<head>
    <style>
        table {
            border-collapse: collapse;
            width: 100%;
        }
        th, td {
            border: 1px solid black;
            padding: 8px 12px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
    </style>
</head>
<body>
    <table border="1">
        <thead>
            <tr>
                <th></th>"""
    ]

    for category in categories:
        body_parts.append(f"\n                <th>{html.escape(str(category), quote=True)}</th>")

    body_parts.append(
        """
                <th>Total</th>
            </tr>
        </thead>
        <tbody>"""
    )

    for person in people:
        body_parts.append(
            f"""
            <tr>
                <td>{html.escape(str(person), quote=True)}</td>"""
        )
        for category in categories:
            body_parts.append(
                f"""
                <td>{_to_money(summary_df.at[person, category])}</td>"""
            )
        body_parts.append(
            f"""
                <td>{_to_money(totals[person])}</td>
            </tr>"""
        )

    if len(people) == 2:
        p1, p2 = people
        body_parts.append(
            """
            <tr>
                <td>Difference</td>"""
        )
        for category in categories:
            body_parts.append(
                f"""
                <td>{_to_money(summary_df.at[p1, category] - summary_df.at[p2, category])}</td>"""
            )
        body_parts.append(
            f"""
                <td>{_to_money(totals[p1] - totals[p2])}</td>
            </tr>"""
        )

    body_parts.append(
        """
        </tbody>
    </table>"""
    )

    body_parts.append(
        f"""
    <p>{html.escape(_write_summary_sentence(summary_df, totals), quote=True)}</p>
</body>
</html>"""
    )

    body = "".join(body_parts)
    return body


def build_summary(path: CsvInput, config: Dict[str, Iterable]) -> Tuple[List[str], str, str]:
    """Build email payload (destinations, subject, html) from CSV input."""
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"])

    summary_df = build_summary_df(df, config)
    totals = summary_df.sum(axis=1)
    totals.name = "Total"
    html_body = write_email_body(summary_df, totals, config)

    date_range = ""
    if not df["Date"].empty:
        min_date = df["Date"].min().strftime("%m/%d")
        max_date = df["Date"].max().strftime("%m/%d")
        date_range = f": {min_date} - {max_date}"

    subject = f"Transactions Summary{date_range}"
    destinations = [
        person.get("Email")
        for person in config.get("People", [])
        if person.get("Email")
    ]
    return destinations, subject, html_body
