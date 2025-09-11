import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz

st.set_page_config(page_title="Product Name Matcher", layout="wide")

st.title("🔎 Product Matching Tool")
st.write("Upload an Excel file, select any two sheets and columns, and find fuzzy product matches.")

# File upload
file = st.file_uploader("Upload Excel file", type=["xlsx"])

if file:
    # Read all sheet names
    xls = pd.ExcelFile(file)
    sheet_names = xls.sheet_names

    # Select two sheets
    sheet1_name = st.selectbox("Select first sheet", sheet_names, index=0)
    sheet2_name = st.selectbox("Select second sheet", sheet_names, index=1 if len(sheet_names) > 1 else 0)

    # Load the selected sheets
    sheet1 = pd.read_excel(file, sheet_name=sheet1_name)
    sheet2 = pd.read_excel(file, sheet_name=sheet2_name)

    # ✅ Only show column names, not all product values
    col1 = st.selectbox(f"Select product column from {sheet1_name}", sheet1.columns.tolist())
    col2 = st.selectbox(f"Select product column from {sheet2_name}", sheet2.columns.tolist())

    # Match threshold
    threshold = st.slider("Minimum Match Score", 50, 100, 80)

    if st.button("Find Matches"):
        products1 = sheet1[col1].dropna().astype(str).tolist()
        products2 = sheet2[col2].dropna().astype(str).tolist()

        matches = []
        for p in products1:
            match = process.extractOne(p, products2, scorer=fuzz.token_sort_ratio)
            if match and match[1] >= threshold:
                matches.append([p, match[0], match[1]])
            else:
                matches.append([p, None, None])

        result = pd.DataFrame(matches, columns=[f"Product from {sheet1_name}",
                                                f"Matched Product from {sheet2_name}",
                                                "Score"])

        st.subheader("📊 Match Results")
        st.dataframe(result, use_container_width=True)

        # Download option
        csv = result.to_csv(index=False).encode("utf-8")
        st.download_button("Download Results as CSV", csv, "matched_products.csv", "text/csv")
