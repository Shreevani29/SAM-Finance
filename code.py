import streamlit as st
import google.generativeai as genai
import pdfplumber
import io
import pandas as pd
from io import StringIO
import os

# Secure API key handling
api_key = "AIzaSyDHMJy2qhQwPA9Qsrhgmfvl_VHTkStuSmA"  # Recommended way to handle API keys

if not api_key:
    st.error("Missing API Key. Please add it to Streamlit secrets.")
else:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

st.title("PDF & Image Extraction")

# Upload multiple PDF files
uploaded_files = st.file_uploader("Upload PDFs", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    all_data = []

    for uploaded_file in uploaded_files:
        file_type = uploaded_file.type
        st.write(f"Uploaded file: {uploaded_file.name} with type: {file_type}")

        if file_type == "application/pdf":
            with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
                extracted_text = "\n".join([page.extract_text() or "" for page in pdf.pages])

            if extracted_text.strip():
                prompt = """Extract the following details from the image document and return them in a clean CSV format:
 
 
Invoice Number (Ensure it is extracted in plain text).
Invoice Date (Format it as 'YYYY-MM-DD').
Due Date (Format it as 'YYYY-MM-DD', if the Due Date is represented as Net 60 extract that also in plain text format,if due date as due date show that also, if there is date other that invoice data fetch that also).
Client Name (Extract the full name of the client as it appears, it will be select the name of the compnay that sends out the bill and not the one who recieves, it should not be Samcorporate and YUSUF).
Description (Extract the product or service description, it should display product description, contract and month details).
Quantity (Qty) (Ensure it is extracted as a number).
Unit Price (USD) (Extract only the numeric value).
Net Amount (USD) (Extract only the numeric value).
VAT % (Extract the percentage as a number).
VAT Amount (Ensure it is extracted as a numeric value).
Total Amount without VAT (Extract total amount).
Total Amount with VAT (Extract total amount, only for VAT % 5).
Currency.
TRN No (VAT exemption number).
Ensure each field is placed in a separate column with appropriate headers. Return 'null' for any missing or unclear data. The CSV should be correctly formatted with commas as delimiters, without extra spaces or formatting errors."""

                response = model.generate_content([prompt, extracted_text])
                csv_content = response.text.strip()

                # Ensure CSV content is valid
                valid_lines = [line for line in csv_content.split("\n") if "," in line]
                valid_csv = "\n".join(valid_lines)

                try:
                    # Read CSV content into DataFrame
                    df = pd.read_csv(StringIO(valid_csv))

                    # Add an additional column for the file name to identify the source of each row
                    df['Source File'] = uploaded_file.name

                    # Append data to all_data list
                    all_data.append(df)

                except Exception as e:
                    st.error(f"Error processing CSV from file {uploaded_file.name}: {e}")
                    st.write("Raw Output:", csv_content)

    if all_data:
        # Concatenate all data into a single DataFrame
        final_df = pd.concat(all_data, ignore_index=True)

        # Save the data to an Excel file
        output_excel_path = "extracted_data.xlsx"
        final_df.to_excel(output_excel_path, index=False)

        st.success(f"Data successfully extracted from {len(uploaded_files)} PDF(s) and saved to {output_excel_path}")
        st.dataframe(final_df)
    else:
        st.error("No valid data was extracted from the uploaded PDFs.")
