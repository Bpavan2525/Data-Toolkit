"""Clean messy spreadsheet data with pandas.

The steps are the ones small businesses ask for again and again: tidy headers,
trim stray spaces, drop blank and duplicate rows, fix emails and phone numbers,
and turn date-like and number-like text into real dates and numbers.
"""
import io
import re
from dataclasses import dataclass, field

import pandas as pd

PHONE_HINTS = ("phone", "mobile", "contact", "whatsapp", "cell")
EMAIL_HINTS = ("email", "e-mail", "mail")
DATE_HINTS = ("date", "dob", "joined", "created", "time")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$")
NUMBER_RE = re.compile(r"^-?[\d,]*\.?\d+$")


@dataclass
class Report:
    rows_in: int = 0
    rows_out: int = 0
    blank_rows_removed: int = 0
    duplicates_removed: int = 0
    empty_columns_removed: list = field(default_factory=list)
    renamed_columns: dict = field(default_factory=dict)
    cells_trimmed: int = 0
    phones_fixed: int = 0
    invalid_emails: int = 0
    date_columns: list = field(default_factory=list)
    number_columns: list = field(default_factory=list)

    def as_dict(self):
        return dict(self.__dict__)


def snake(name):
    s = re.sub(r"[^0-9a-zA-Z]+", "_", str(name).strip()).strip("_").lower()
    return s or "column"


def unique(names):
    seen, out = {}, []
    for n in names:
        if n in seen:
            seen[n] += 1
            out.append(f"{n}_{seen[n]}")
        else:
            seen[n] = 1
            out.append(n)
    return out


def fix_phone(value, country_code="91"):
    if pd.isna(value):
        return value
    digits = re.sub(r"\D", "", str(value))
    if len(digits) == 10:
        return f"+{country_code}{digits}"
    if len(digits) == 12 and digits.startswith(country_code):
        return f"+{digits}"
    if len(digits) == 11 and digits.startswith("0"):
        return f"+{country_code}{digits[1:]}"
    return value


def parse_date(value):
    """Indian-style day-first dates, but year-first stays year-first (2024/04/01)."""
    if pd.isna(value):
        return pd.NaT
    text = str(value).strip()
    year_first = bool(re.match(r"^\d{4}[-/.]", text))
    return pd.to_datetime(text, errors="coerce", dayfirst=not year_first)


def has_hint(col, hints):
    return any(h in col for h in hints)


def clean(df, country_code="91"):
    """Return (clean_df, Report). The input DataFrame is not modified."""
    r = Report(rows_in=len(df))
    df = df.copy()

    new_cols = unique([snake(c) for c in df.columns])
    r.renamed_columns = {str(a): b for a, b in zip(df.columns, new_cols) if str(a) != b}
    df.columns = new_cols

    for col in df.columns:
        if df[col].dtype == object or pd.api.types.is_string_dtype(df[col]):
            before = df[col]
            after = before.map(lambda v: re.sub(r"\s+", " ", v).strip() if isinstance(v, str) else v)
            after = after.replace("", pd.NA)
            r.cells_trimmed += int(((before != after) & before.notna() & after.notna()).sum())
            df[col] = after

    empty = [c for c in df.columns if df[c].isna().all()]
    r.empty_columns_removed = empty
    df = df.drop(columns=empty)

    n = len(df)
    df = df.dropna(how="all")
    r.blank_rows_removed = n - len(df)

    for col in df.columns:
        if has_hint(col, EMAIL_HINTS):
            df[col] = df[col].map(lambda v: v.lower() if isinstance(v, str) else v)
            r.invalid_emails += int(df[col].dropna().map(lambda v: not EMAIL_RE.match(str(v))).sum())
        elif has_hint(col, PHONE_HINTS):
            fixed = df[col].map(lambda v: fix_phone(v, country_code))
            r.phones_fixed += int(((fixed != df[col]) & df[col].notna()).sum())
            df[col] = fixed
        elif has_hint(col, DATE_HINTS):
            parsed = df[col].map(parse_date)
            if parsed.notna().sum() >= max(1, 0.8 * df[col].notna().sum()):
                df[col] = pd.to_datetime(parsed).dt.date
                r.date_columns.append(col)
        else:
            s = df[col].dropna()
            if len(s) and s.map(lambda v: isinstance(v, str)).all() and s.map(lambda v: bool(NUMBER_RE.match(v.replace("₹", "").strip()))).all():
                df[col] = pd.to_numeric(df[col].map(lambda v: v.replace(",", "").replace("₹", "").strip() if isinstance(v, str) else v))
                r.number_columns.append(col)

    n = len(df)
    df = df.drop_duplicates()
    r.duplicates_removed = n - len(df)
    df = df.reset_index(drop=True)
    r.rows_out = len(df)
    return df, r


def read_any(filename, data):
    name = filename.lower()
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(data), dtype=object)
    if name.endswith(".csv") or name.endswith(".txt"):
        return pd.read_csv(io.BytesIO(data), dtype=object, skipinitialspace=False, encoding_errors="replace")
    raise ValueError("Upload a .csv or .xlsx file")


def to_bytes(df, fmt):
    buf = io.BytesIO()
    if fmt == "xlsx":
        df.to_excel(buf, index=False, sheet_name="Cleaned")
    else:
        df.to_csv(buf, index=False)
    return buf.getvalue()
