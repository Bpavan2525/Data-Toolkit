# Spreadsheet Cleaner

Clean messy CSV and Excel files with **Python and pandas**, from a web page or the command line. Built for the files small businesses actually have: customer lists, orders and leads typed by hand, exported from different tools, and full of stray spaces, duplicates and mixed formats.

**Live demo:** LIVE_URL (press "Try the sample file" to see a before and after)

## What it fixes

| Problem | What the cleaner does |
| --- | --- |
| Headers like ` Customer Name ` and `Amount Spent (₹)` | Renames to `customer_name`, `amount_spent`; de-duplicates repeated headers |
| Extra spaces inside and around values | Collapses and trims them |
| Blank rows and fully empty columns | Drops them |
| Exact duplicate rows | Drops them |
| Phones as `98765 43210`, `098765-43210`, `+91-98765-43210` | Formats as `+919876543210` (country code is configurable) |
| Emails in mixed case | Lowercases; counts invalid ones for a manual check |
| Dates as `05/01/2024`, `12-03-2024`, `2024/04/01` | Real dates, day-first for Indian formats, year-first kept as is |
| Amounts as `"1,250"` or `₹980` | Real numbers |

Every run returns a report of what changed, so nothing happens silently.

## Use it

**Web:** open the live demo, upload a `.csv` or `.xlsx` (up to 4 MB), choose CSV or Excel output, download.

**Command line:**

```bash
pip install -r requirements.txt
python clean.py samples/customers_messy.csv -o customers_clean.xlsx
```

**In your own code:**

```python
from cleaner import clean, read_any
df, report = clean(read_any("leads.xlsx", open("leads.xlsx", "rb").read()))
print(report.as_dict())
```

## Run locally and test

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python app.py      # http://127.0.0.1:5000
pytest
```

## Layout

```
cleaner/core.py        cleaning rules and the change report
cleaner/web.py         Flask upload page
clean.py               command-line tool
samples/               a deliberately messy example file
tests/                 pytest suite
notebooks/             NumPy, pandas, Matplotlib, Seaborn and Plotly exercises
```
