import streamlit as st
import pandas as pd
import tkinter as tk
from datetime import date
import unicodedata, re
from uploadC import upload_to_council_connect

# ========== TKINTER CREDENTIAL PROMPT ==========
def get_credentials():
    creds = {}

    def submit():
        creds["username"] = username_var.get()
        creds["password"] = password_var.get()
        creds["auto_click"] = auto_click_var.get()
        root.destroy()

    root = tk.Tk()
    root.title("Council Connect Login")
    root.geometry("350x220")
    root.attributes("-topmost", True)

    tk.Label(root, text="Council ID:").pack(pady=(10, 0))
    username_var = tk.StringVar()
    tk.Entry(root, textvariable=username_var, width=36).pack()

    tk.Label(root, text="Password:").pack(pady=(10, 0))
    password_var = tk.StringVar()
    tk.Entry(root, textvariable=password_var, show="*", width=36).pack()

    auto_click_var = tk.BooleanVar()
    tk.Checkbutton(root, text="Auto-click 'Create Casework'", variable=auto_click_var).pack(pady=8)

    tk.Button(root, text="Start", command=submit, width=18).pack(pady=6)
    root.mainloop()
    return creds if creds else None

# ========== STREAMLIT FRONTEND ==========
st.set_page_config(page_title="📤 Upload Intake Excel", layout="wide")
st.title("📤 Upload Constituent Excel to Council Connect")

uploaded_file = st.file_uploader("Upload your Excel file with casework entries", type=["xlsx"])
if not uploaded_file:
    st.warning("Please upload an Excel file.")
    st.stop()

# ========== PARSE EXCEL ==========
df = pd.read_excel(uploaded_file, dtype=str)
df.fillna("", inplace=True)

# Find a 'Timestamp' column robustly
def _norm(s: str) -> str:
    return (
        str(s)
        .replace("\u200b", "").replace("\u200e", "").replace("\u200f", "").replace("\ufeff", "")
        .strip().lower()
    )

col_map = {c: _norm(c) for c in df.columns}
ts_candidates = [orig for orig, normed in col_map.items() if normed == "timestamp"]
if not ts_candidates:
    st.error("The uploaded file is missing a 'Timestamp' column.")
    st.stop()
TS_COL = ts_candidates[0]

# Clean and normalize timestamps
def clean_ts(val):
    if val is None:
        return None
    s = unicodedata.normalize("NFKC", str(val))         # full-width → ASCII
    s = re.sub(r"[\u200b\u200c\u200d\u200e\u200f\ufeff\u00a0\u202f]", "", s)  # zero-widths & NBSPs
    s = re.sub(r"\s+", " ", s).strip()                  # collapse whitespace/newlines
    return None if s == "" or s.lower() in {"nan", "nat"} else s

ts_text = df[TS_COL].map(clean_ts)

# Try multiple parse strategies (ISO, MDY, serials)
p_iso_ms = pd.to_datetime(ts_text, errors="coerce", format="%Y-%m-%d %H:%M:%S.%f")
p_iso_s  = pd.to_datetime(ts_text, errors="coerce", format="%Y-%m-%d %H:%M:%S")
p_gen    = pd.to_datetime(ts_text, errors="coerce", infer_datetime_format=True)
p_mdys   = pd.to_datetime(ts_text, errors="coerce", format="%m/%d/%Y %H:%M:%S")
p_mdy    = pd.to_datetime(ts_text, errors="coerce", format="%m/%d/%Y")

# Excel serials, if any snuck in as numbers but we read as text
ts_num   = pd.to_numeric(ts_text, errors="coerce")
p_xls    = pd.to_datetime(ts_num, errors="coerce", unit="D", origin="1899-12-30")

parsed   = p_iso_ms.fillna(p_iso_s).fillna(p_gen).fillna(p_mdys).fillna(p_mdy).fillna(p_xls)
try:
    parsed = parsed.dt.tz_localize(None)
except Exception:
    pass

df["__TimestampParsed"] = parsed
st.caption(f"Parsed timestamps: {df['__TimestampParsed'].notna().sum()} / {len(df)}")

# ========== DATE SELECTION ==========
st.subheader("📅 Filter by Submission Date")
start_date = st.date_input("Upload rows from this date (inclusive) through today:")

# Inclusive window: start at 00:00 that day → today 23:59:59.999999
start_dt = pd.to_datetime(start_date)
end_dt   = pd.Timestamp.today().normalize() + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)

mask = (df["__TimestampParsed"] >= start_dt) & (df["__TimestampParsed"] <= end_dt)
preview_df = df.loc[mask].drop(columns=["__TimestampParsed"])

st.write(f"Found **{len(preview_df)}** rows from {start_dt.date()} to {end_dt.date()}.")
if len(preview_df) > 0:
    with st.expander("Preview matching rows", expanded=False):
        st.dataframe(preview_df[[TS_COL]].head(50))

# ========== RUN ON BUTTON CLICK ==========
if st.button("🔐 Start Upload to Council Connect"):
    if df["__TimestampParsed"].isna().all():
        st.error("Could not parse any dates in 'Timestamp'. Please check the format in the sheet.")
        st.stop()

    if preview_df.empty:
        bad = df.loc[df['__TimestampParsed'].isna(), [TS_COL]].head(10)
        if not bad.empty:
            st.warning("No matches. Some timestamps couldn't be parsed (showing a few):")
            st.dataframe(bad)
        else:
            st.warning("No entries match the selected date range.")
        st.stop()

    creds = get_credentials()
    if not creds:
        st.error("Login cancelled.")
    else:
        upload_to_council_connect(preview_df, creds, "msedgedriver.exe")
