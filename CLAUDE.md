# ASIC Batch Payment Generator - Claude Context

## Project Overview

This is a Streamlit application that generates ABA (Australian Bankers Association) files for ASIC (Australian Securities and Investments Commission) payments. The app processes multiple ASIC statement PDFs and creates properly formatted batch payment files for CommBank processing.

## Key Components

### Main Application (`app.py`)
- **Streamlit interface** for file uploads and user input
- **PDF extraction logic** using pdfplumber and PyPDF2
- **ABA file generation** following CEMTEX standard (120 chars per record)
- **Batch processing** for multiple companies in single ABA file
- **Duplicate detection system** using SQLite database to prevent repeat payments
- **Password authentication** to secure access to financial data

### Core Functions
1. `extract_asic_data(pdf_file)` - Extracts payment details from ASIC PDFs
2. `generate_aba_file(asic_data_list, user_bsb, user_account, user_name, processing_date, apca_number)` - Creates CEMTEX-compliant ABA files
3. `format_aba_amount(amount_str)` - Converts dollar amounts to ABA cent format

### Database Functions
1. `init_database()` - Creates SQLite database for tracking processed statements
2. `check_duplicate_statement(file_hash, asic_reference, bpay_reference)` - Detects duplicate files/payments
3. `save_processed_statement(asic_data, file_hash, aba_filename, batch_id)` - Records processed statements
4. `get_processed_statements()` - Retrieves processing history

### Security Functions
1. `check_password()` - Handles password authentication and session management
2. Password protection requires ASIC_APP_PASSWORD environment variable (no hardcoded password)
3. Session state management for login/logout functionality

### ABA File Structure
- **Header Record (Type 0)**: File identification, user details, APCA number
- **Credit Records (Type 1)**: One per company, payments TO Reserve Bank of Australia
- **Debit Record (Type 1)**: Single balancing debit FROM user's account
- **Trailer Record (Type 7)**: File totals and record count

## Duplicate Detection System

The app includes a comprehensive duplicate detection system to prevent accidental repeat payments:

### Detection Methods
1. **File Hash Matching**: Uses SHA-256 hash to detect identical PDF files
2. **Payment Reference Matching**: Checks ASIC reference + BPay reference combinations
3. **Real-time Warnings**: Shows duplicate alerts during file upload

### Database Schema
- **processed_statements table**: Stores all processed payment details
- **Unique constraints**: Prevents duplicate file hashes from being saved
- **Audit trail**: Tracks when statements were processed and which ABA files were generated

### User Experience
- **Visual indicators**: Duplicate statements show with ⚠️ warning icons
- **Detailed warnings**: Shows when/how statement was previously processed
- **Processing prevention**: Only allows new statements to be included in ABA files
- **History sidebar**: Quick access to recently processed statements

## Important Details

### Bank Details (Hardcoded)
- **Destination**: Reserve Bank of Australia
- **BSB**: 093-003
- **Account**: 317118
- **Name**: ASIC, Official Administered Receipts Account

### User Inputs Required
- BSB, Account Number, Account Name
- APCA Number (defaults to 301500)
- Processing Date
- Multiple ASIC statement PDFs

### Data Extraction Patterns
- **Company Name**: `FOR\s+([A-Z][A-Z0-9\s&]+(?:PTY\s+LTD|LIMITED|LTD))`
- **ACN**: `ACN\s+(\d{3}\s+\d{3}\s+\d{3})`
- **Amount**: `Annual Review.*?\$(\d+\.\d{2})`
- **ASIC Reference**: `Annual Review.*?([A-Z0-9]{13}\s+[A-Z])`
- **BPay Reference**: Standalone 13-digit number after "Ref:" line

## Testing Files

- `test_app_functionality.py` - Tests single payment extraction and ABA generation
- `test_batch_functionality.py` - Tests multiple payment batch processing
- `test_core_logic.py` - Tests ABA formatting logic

## Deployment

- **Local**: `streamlit run app.py`
- **Streamlit Cloud**: Auto-deploys from GitHub main branch
- **Dependencies**: Listed in `requirements.txt`

## Common Issues & Solutions

1. **PDF Extraction Failures**: Use both pdfplumber and PyPDF2 as fallbacks
2. **Line Length Errors**: All ABA records must be exactly 120 characters
3. **Balance Issues**: Credit total must equal debit total in trailer
4. **APCA Number**: Must be correct 6-digit number for bank validation

## Security Considerations

### Authentication
- **Password Protection**: App requires password before showing any content
- **Environment Variables**: Password REQUIRED via `ASIC_APP_PASSWORD` (no hardcoded passwords)
- **Session Management**: Proper login/logout with session state clearing
- **Access Control**: All sensitive functionality protected behind authentication
- **Public Repository Safe**: No secrets stored in public GitHub repository

### Password Setup Instructions

**For Local Development:**
```bash
# Mac/Linux Terminal:
export ASIC_APP_PASSWORD="your_secure_password_here"
streamlit run app.py

# Windows Command Prompt:
set ASIC_APP_PASSWORD=your_secure_password_here
streamlit run app.py

# Windows PowerShell:
$env:ASIC_APP_PASSWORD="your_secure_password_here"
streamlit run app.py
```

**For Streamlit Cloud Deployment:**
1. Go to Streamlit Cloud dashboard
2. Click on app settings
3. Navigate to "Secrets" section
4. Add configuration:
```toml
ASIC_APP_PASSWORD = "your_secure_password_here"
```

**Using .env file (Local Only):**
Create `.env` file in project root:
```
ASIC_APP_PASSWORD=your_secure_password_here
```
Note: `.env` files are excluded from git via `.gitignore`

### Data Security
- **Local Processing**: All financial data processed locally, not on servers
- **Database Exclusion**: SQLite database excluded from git (.gitignore)
- **File Exclusion**: PDFs and ABA files excluded from version control
- **No Cloud Storage**: No sensitive data transmitted to external services

### Best Practices
- **Password Requirements**: Strong default password with special characters
- **Verification Required**: Users should verify ABA files before bank processing
- **Logout Functionality**: Clear session logout in sidebar
- **Public Access Prevention**: Password wall prevents public access to processed statements

## Development Notes

- Uses regex patterns for PDF text extraction
- Handles both single and batch payments
- Backward compatible function signatures
- Error handling for invalid PDFs
- Comprehensive test coverage