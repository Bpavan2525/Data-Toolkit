import io
from pathlib import Path

import pandas as pd
import pytest

from cleaner import clean, read_any, to_bytes
from cleaner.core import fix_phone, snake
from cleaner.web import create_app

SAMPLE = Path(__file__).parent.parent / "samples" / "customers_messy.csv"


@pytest.fixture
def sample():
    return read_any(SAMPLE.name, SAMPLE.read_bytes())


def test_sample_end_to_end(sample):
    out, r = clean(sample)
    assert (r.rows_in, r.rows_out) == (6, 4)
    assert r.duplicates_removed == 1 and r.blank_rows_removed == 1
    assert list(out.columns) == ["customer_name", "phone_number", "e_mail", "join_date", "amount_spent", "notes"]
    assert out.loc[0, "customer_name"] == "Ravi Kumar"
    assert out["phone_number"].tolist() == ["+919876543210", "+919123456780", "+919988776655", "+919900112233"]
    assert out.loc[3, "e_mail"] == "meena@yahoo.com"
    assert r.invalid_emails == 1
    assert str(out.loc[0, "join_date"]) == "2024-01-05"   # day first
    assert str(out.loc[3, "join_date"]) == "2024-04-01"   # year first stays year first
    assert out["amount_spent"].sum() == 1250 + 980 + 450 + 2300


def test_input_not_modified(sample):
    before = sample.copy()
    clean(sample)
    pd.testing.assert_frame_equal(sample, before)


@pytest.mark.parametrize("raw,expected", [
    ("98765 43210", "+919876543210"),
    ("+91-98765-43210", "+919876543210"),
    ("098765 43210", "+919876543210"),
    ("12345", "12345"),
])
def test_fix_phone(raw, expected):
    assert fix_phone(raw) == expected


def test_snake_and_duplicate_headers():
    assert snake(" Amount Spent (₹) ") == "amount_spent"
    out, _ = clean(pd.DataFrame([[1, 2]], columns=["Name", "name"]))
    assert list(out.columns) == ["name", "name_2"]


def test_excel_round_trip(sample):
    out, _ = clean(sample)
    back = pd.read_excel(io.BytesIO(to_bytes(out, "xlsx")), dtype=object)
    assert len(back) == 4


def test_rejects_unknown_file_type():
    with pytest.raises(ValueError):
        read_any("notes.pdf", b"%PDF")


def test_web_sample_and_upload():
    client = create_app().test_client()
    assert client.get("/").status_code == 200
    r = client.post("/", data={"sample": "1", "format": "xlsx"})
    assert r.status_code == 200 and b"customers_messy_clean.xlsx" in r.data
    r = client.post("/", data={"file": (io.BytesIO(SAMPLE.read_bytes()), "leads.csv")},
                    content_type="multipart/form-data")
    assert r.status_code == 200 and b"leads_clean.csv" in r.data
    r = client.post("/", data={"file": (io.BytesIO(b"x"), "bad.pdf")}, content_type="multipart/form-data")
    assert r.status_code == 400
    assert client.post("/", data={}).status_code == 400
