"""Command line: python clean.py messy.xlsx -o clean.xlsx"""
import argparse
import json
from pathlib import Path

from cleaner import clean, read_any, to_bytes


def main():
    p = argparse.ArgumentParser(description="Clean a messy CSV or Excel file.")
    p.add_argument("input")
    p.add_argument("-o", "--output", help="Output .csv or .xlsx (default: <input>_clean.csv)")
    p.add_argument("--country-code", default="91", help="Added to 10-digit phone numbers")
    a = p.parse_args()
    src = Path(a.input)
    out_path = Path(a.output) if a.output else src.with_name(src.stem + "_clean.csv")
    df, report = clean(read_any(src.name, src.read_bytes()), a.country_code)
    out_path.write_bytes(to_bytes(df, "xlsx" if out_path.suffix == ".xlsx" else "csv"))
    print(json.dumps(report.as_dict(), indent=2, default=str))
    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
