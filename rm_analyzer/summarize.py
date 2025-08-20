"""Functions for summarizing a transactions CSV."""

# Standard library imports
import pandas as pd


def _build_owners_dict(config):
    """Builds dictionary containing Account Owner, Account Number data from config file."""
    owners_dict = {"Owner": {}, "Account Number": {}}
    c = 0
    for p in config["People"]:
        for n in p["Accounts"]:
            owners_dict["Owner"][c] = p["Name"]
            owners_dict["Account Number"][c] = n
            c += 1
    return owners_dict


def build_summary_df(df, config):
    """Builds the transactions CSV summary dataframe."""
    owners_df = pd.DataFrame(_build_owners_dict(config))
    cats = config["Categories"]
    df_filtered = df[df["Ignored From"].isnull() * df["Category"].isin(cats)]
    df_merged = pd.merge(df_filtered, owners_df, how="left", on="Account Number")
    df_agg = df_merged.groupby(["Category", "Owner"])[["Amount"]].sum().reset_index()
    df_pivot = df_agg.pivot(index="Owner", columns="Category", values="Amount").fillna(
        0
    )
    return df_pivot


def _to_money(n):
    """Formats a number as money."""
    return f"{n:.2f}"


def _write_summary_sentence(summ_df, tot_series, config):
    """Writes the transactions CSV summary sentence."""
    people = list(summ_df.index)
    if len(people) == 2:
        p1, p2 = people
        s = (
            f"{p1} owes {p2}: "
            f"{_to_money(0.5 * tot_series.sum() - tot_series[p1])}."
        )
    else:
        s = "See the table above for transaction totals by person, category."
    return s


def write_email_body(summ_df, tot_series, config):
    """Writes the summary HTML for email body."""
    cats = list(summ_df.columns)
    people = list(summ_df.index)

    body_parts = []
    body_parts.append(
        """\
<!DOCTYPE html>
<html>
<head>
    <style>
        table {
            border-collapse: collapse;
            width: 100%
        }
        th,td {
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
    )

    for c in cats:
        body_parts.append(
            f"""
                <th>{c}</th>"""
        )

    body_parts.append(
        """
                <th>Total</th>
            </tr>
        </thead>
        <tbody>"""
    )

    for p in people:
        body_parts.append(
            f"""
            <tr>
                <td>{p}</td>"""
        )
        for c in cats:
            body_parts.append(
                f"""
                <td>{_to_money(summ_df.at[p, c])}</td>"""
            )
        body_parts.append(
            f"""
                <td>{_to_money(tot_series[p])}</td>
            </tr>"""
        )

    if len(people) == 2:
        p1, p2 = people
        body_parts.append(
            """
            <tr>
                <td>Difference</td>"""
        )
        for c in cats:
            body_parts.append(
                f"""
                <td>{_to_money(summ_df.at[p1, c] - summ_df.at[p2, c])}</td>"""
            )
        body_parts.append(
            f"""
                <td>{_to_money(tot_series[p1] - tot_series[p2])}</td>
            </tr>"""
        )

    body_parts.append(
        """
        </tbody>
    </table>"""
    )

    body_parts.append(
        f"""
    <p>{_write_summary_sentence(summ_df, tot_series, config)}</p>
</body>
</html>"""
    )

    body = "".join(body_parts).replace("&", "&amp;")
    return body


def build_summary(path, config):
    """Builds the summary email parts."""
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"])

    summ_df = build_summary_df(df, config)
    tot_series = summ_df.sum(axis=1)
    tot_series.name = "Total"
    html = write_email_body(summ_df, tot_series, config)

    min_date = df["Date"].min().strftime("%m/%d")
    max_date = df["Date"].max().strftime("%m/%d")
    subject = f"Transactions Summary: {min_date} - {max_date}"

    dest = [p["Email"] for p in config["People"]]

    return dest, subject, html
