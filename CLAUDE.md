# ASIC Batch Payment Generator - Claude Context

## Project Overview

This is a Streamlit application that generates ABA (Australian Bankers Association) files for ASIC (Australian Securities and Investments Commission) payments. The app processes multiple ASIC statement PDFs and creates properly formatted batch payment files for CommBank processing.

## Key Components

### Main Application (`app.py`)
- **Streamlit interface** for file uploads and user input
- **PDF extraction logic** using pdfplumber and PyPDF2
- **ABA file generation** following CEMTEX standard (120 chars per record)
- **Batch processing** for multiple companies in single ABA file

### Core Functions
1. `extract_asic_data(pdf_file)` - Extracts payment details from ASIC PDFs
2. `generate_aba_file(asic_data_list, user_bsb, user_account, user_name, processing_date, apca_number)` - Creates CEMTEX-compliant ABA files
3. `format_aba_amount(amount_str)` - Converts dollar amounts to ABA cent format

### ABA File Structure
- **Header Record (Type 0)**: File identification, user details, APCA number
- **Credit Records (Type 1)**: One per company, payments TO Reserve Bank of Australia
- **Debit Record (Type 1)**: Single balancing debit FROM user's account
- **Trailer Record (Type 7)**: File totals and record count

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

- No data stored on servers
- PDFs and ABA files excluded from git (.gitignore)
- Financial data processed locally only
- Users should verify ABA files before bank processing

## Development Notes

- Uses regex patterns for PDF text extraction
- Handles both single and batch payments
- Backward compatible function signatures
- Error handling for invalid PDFs
- Comprehensive test coverage