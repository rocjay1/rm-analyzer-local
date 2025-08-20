import unittest
import pandas as pd
from rm_analyzer_local import summarize

class TestSummarize(unittest.TestCase):
    def setUp(self):
        self.config = {
            "People": [
                {"Name": "Alice", "Email": "alice@example.com", "Accounts": ["A1"]},
                {"Name": "Bob", "Email": "bob@example.com", "Accounts": ["B1"]}
            ],
            "Categories": ["Food", "Rent"]
        }
        self.df = pd.DataFrame({
            "Date": ["2023-01-01", "2023-01-02"],
            "Account Number": ["A1", "B1"],
            "Category": ["Food", "Rent"],
            "Amount": [100, 200],
            "Ignored From": [None, None]
        })

    def test_build_summary_df(self):
        result = summarize.build_summary_df(self.df, self.config)
        self.assertIn("Food", result.columns)
        self.assertIn("Rent", result.columns)
        self.assertIn("Alice", result.index)
        self.assertIn("Bob", result.index)

    def test_write_email_body(self):
        summ_df = summarize.build_summary_df(self.df, self.config)
        tot_series = summ_df.sum(axis=1)
        tot_series.name = "Total"
        html = summarize.write_email_body(summ_df, tot_series, self.config)
        self.assertIn("<html>", html)
        self.assertIn("Food", html)
        self.assertIn("Rent", html)

if __name__ == "__main__":
    unittest.main()
