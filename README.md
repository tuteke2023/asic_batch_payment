# ASIC Batch Payment Generator

A Streamlit application that generates ABA files for ASIC payments. Upload multiple ASIC statement PDFs and the app will extract payment details and create a properly formatted ABA file for CommBank processing.

**Configured for TT Accountancy Pty Ltd** - Bank details are pre-filled for convenience.

⚠️ **Password Protected** - This application requires authentication to protect sensitive financial data.

## Features

- **Password Protection**: Secure authentication to protect financial data
- **Multiple File Upload**: Upload multiple ASIC PDF statements for batch processing
- **Duplicate Detection**: Prevents accidental repeat payments using database tracking
- **Automatic Data Extraction**: Extracts company details, amounts, and BPay references
- **Batch Payment Generation**: Creates single ABA file for multiple companies
- **CEMTEX Standard Compliant**: All records exactly 120 characters as required
- **Reserve Bank Integration**: Automatically uses RBA details for ASIC payments
- **Processing History**: View previously processed statements in sidebar
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

2. Set the password environment variable:
```bash
export ASIC_APP_PASSWORD="your_secure_password_here"
```

3. Run the app:
```bash
streamlit run app.py
```

**Note**: The app will not work without the `ASIC_APP_PASSWORD` environment variable set.

## Usage

1. **Login**: Enter the application password (contact TT Accountancy for access)
2. **Review**: Pre-filled bank details (BSB: 063245, Account: 10758330, APCA: 301500)  
3. **Upload**: One or more ASIC statement PDFs
4. **Check**: Review extracted information and duplicate warnings
5. **Generate**: Click "Generate Batch ABA File" to create the payment file
6. **Download**: Download the generated ABA file for CommBank processing
7. **Logout**: Use sidebar logout button when finished

## ABA File Structure

- **Header Record**: File identification and user details
- **Credit Records**: One per company payment to ASIC 
- **Debit Record**: Single balancing debit from your account
- **Trailer Record**: File totals and record count

## Security Features

- **Password Protection**: Application requires authentication to access
- **Session Management**: Automatic logout and session clearing
- **Local Processing**: Financial data processed locally, not on servers
- **Database Security**: SQLite database excluded from version control
- **Environment Variables**: Password MUST be configured via ASIC_APP_PASSWORD env var (not stored in code)

## Security Note

This app processes sensitive financial information. The password protection prevents unauthorized access to processed statements and payment history. Always verify the generated ABA file before processing payments.
