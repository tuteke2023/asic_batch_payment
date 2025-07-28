# ASIC Batch Payment Generator

A Streamlit application that generates ABA files for ASIC payments. Upload multiple ASIC statement PDFs and the app will extract payment details and create a properly formatted ABA file for CommBank processing.

## Features

- **Multiple File Upload**: Upload multiple ASIC PDF statements for batch processing
- **Automatic Data Extraction**: Extracts company details, amounts, and BPay references
- **Batch Payment Generation**: Creates single ABA file for multiple companies
- **CEMTEX Standard Compliant**: All records exactly 120 characters as required
- **Reserve Bank Integration**: Automatically uses RBA details for ASIC payments
- **User-friendly Interface**: Clean Streamlit interface with progress tracking

## Bank Details Used

The app automatically uses the following RBA details for ASIC payments:
- **Bank name**: Reserve Bank of Australia
- **BSB**: 093-003
- **Account number**: 317118
- **Account name**: ASIC, Official Administered Receipts Account

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the app:
```bash
streamlit run app.py
```

## Usage

1. Enter your bank details (BSB, Account Number, Account Name, APCA Number)
2. Upload one or more ASIC statement PDFs
3. Review the extracted information for each company
4. Click "Generate Batch ABA File" to create the payment file
5. Download the generated ABA file for CommBank processing

## ABA File Structure

- **Header Record**: File identification and user details
- **Credit Records**: One per company payment to ASIC 
- **Debit Record**: Single balancing debit from your account
- **Trailer Record**: File totals and record count

## Security Note

This app processes financial information locally. No data is stored on servers. Always verify the generated ABA file before processing payments.
