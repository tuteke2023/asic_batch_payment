import streamlit as st
import pandas as pd
import re
from datetime import datetime
import io
import PyPDF2
import pdfplumber
import sqlite3
import hashlib
import os

# Authentication function
def check_password():
    """Returns True if the user has entered the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        # SECURITY: Password must be set via environment variable
        correct_password = os.getenv("ASIC_APP_PASSWORD")
        
        if not correct_password:
            st.error("🚨 Security Error: Password not configured. Contact administrator.")
            st.session_state["password_correct"] = False
            return
            
        if st.session_state["password"] == correct_password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password
        st.text_input(
            "🔐 Enter Password", 
            type="password", 
            on_change=password_entered, 
            key="password",
            help="Contact TT Accountancy for the secure access password"
        )
        st.info("🔒 This application is password protected to secure financial data.")
        st.warning("⚠️ Password must be configured by administrator via environment variable.")
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error
        st.text_input(
            "🔐 Enter Password", 
            type="password", 
            on_change=password_entered, 
            key="password",
            help="Contact TT Accountancy for the secure access password"
        )
        st.error("😞 Password incorrect. Contact TT Accountancy for the correct password.")
        return False
    else:
        # Password correct
        return True

# Database functions
def init_database():
    """Initialize SQLite database for tracking processed statements"""
    conn = sqlite3.connect('asic_statements.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_statements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            acn TEXT NOT NULL,
            asic_reference TEXT NOT NULL,
            bpay_reference TEXT NOT NULL,
            amount REAL NOT NULL,
            file_hash TEXT NOT NULL UNIQUE,
            processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            aba_filename TEXT,
            batch_id TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def get_file_hash(file_content):
    """Generate SHA-256 hash of file content"""
    return hashlib.sha256(file_content).hexdigest()

def check_duplicate_statement(file_hash, asic_reference, bpay_reference):
    """Check if statement has already been processed"""
    conn = sqlite3.connect('asic_statements.db')
    cursor = conn.cursor()
    
    # Check by file hash first (exact same file)
    cursor.execute('''
        SELECT company_name, processed_date, aba_filename 
        FROM processed_statements 
        WHERE file_hash = ?
    ''', (file_hash,))
    
    file_duplicate = cursor.fetchone()
    
    # Check by ASIC reference and BPay reference (same payment)
    cursor.execute('''
        SELECT company_name, processed_date, aba_filename 
        FROM processed_statements 
        WHERE asic_reference = ? AND bpay_reference = ?
    ''', (asic_reference, bpay_reference))
    
    payment_duplicate = cursor.fetchone()
    
    conn.close()
    
    return {
        'file_duplicate': file_duplicate,
        'payment_duplicate': payment_duplicate
    }

def save_processed_statement(asic_data, file_hash, aba_filename, batch_id):
    """Save processed statement to database"""
    conn = sqlite3.connect('asic_statements.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO processed_statements 
            (company_name, acn, asic_reference, bpay_reference, amount, file_hash, aba_filename, batch_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            asic_data['company_name'],
            asic_data['acn'],
            asic_data['asic_reference'],
            asic_data['bpay_reference'],
            float(asic_data['amount']),
            file_hash,
            aba_filename,
            batch_id
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_processed_statements():
    """Get all processed statements from database"""
    conn = sqlite3.connect('asic_statements.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT company_name, acn, asic_reference, amount, processed_date, aba_filename
        FROM processed_statements 
        ORDER BY processed_date DESC
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    return results

def extract_asic_data(pdf_file):
    """Extract relevant data from ASIC statement PDF"""
    text = ""
    
    # Try pdfplumber first for better text extraction
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
    except:
        # Fallback to PyPDF2
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    
    # Extract company details - look for pattern "FOR [COMPANY NAME]" after ACN
    company_name_match = re.search(r'FOR\s+([A-Z][A-Z0-9\s&]+(?:PTY\s+LTD|LIMITED|LTD))', text)
    if company_name_match:
        company_name = company_name_match.group(1).strip()
    else:
        company_name = "Unknown Company"
    
    # Extract ACN
    acn_match = re.search(r'ACN\s+(\d{3}\s+\d{3}\s+\d{3})', text)
    acn = acn_match.group(1).replace(' ', '') if acn_match else ""
    
    # Extract payment amount
    amount_match = re.search(r'Annual Review.*?\$(\d+\.\d{2})', text)
    amount = amount_match.group(1) if amount_match else "0.00"
    
    # Extract ASIC reference
    ref_match = re.search(r'Annual Review.*?([A-Z0-9]{13}\s+[A-Z])', text)
    asic_reference = ref_match.group(1).replace(' ', '') if ref_match else ""
    
    # Extract BPay reference - look for 13-digit number that appears after "Ref:" line
    # First try to find the standalone 13-digit number
    bpay_ref_match = re.search(r'^\s*(\d{13})\s*$', text, re.MULTILINE)
    if bpay_ref_match:
        bpay_ref = bpay_ref_match.group(1)
    else:
        # Fallback: look for the number in the barcode-like line with asterisks
        barcode_match = re.search(r'\*\d+\s+(\d{13})\s+\d+\s+\*', text)
        if barcode_match:
            bpay_ref = barcode_match.group(1)
        else:
            # Final fallback to the spaced pattern
            bpay_fallback = re.search(r'Ref:\s+(\d{4}\s+\d{4}\s+\d{4}\s+\d{3})', text)
            bpay_ref = bpay_fallback.group(1).replace(' ', '') if bpay_fallback else ""
    
    return {
        'company_name': company_name,
        'acn': acn,
        'amount': amount,
        'asic_reference': asic_reference,
        'bpay_reference': bpay_ref
    }

def format_aba_amount(amount_str):
    """Convert amount string to ABA format (cents, 10 digits, zero-padded)"""
    try:
        amount = float(amount_str)
        cents = int(amount * 100)
        return f"{cents:010d}"
    except:
        return "0000000000"

def generate_aba_file(asic_data_list, user_bsb, user_account, user_name, processing_date, apca_number="301500"):
    """Generate ABA file content for multiple ASIC payments following CEMTEX standard"""
    
    # Handle single item case (backward compatibility)
    if not isinstance(asic_data_list, list):
        asic_data_list = [asic_data_list]
    
    # RBA bank details (destination)
    rba_bsb = "093-003"
    rba_account = "317118"
    
    # Format processing date as DDMMYY
    date_str = processing_date.strftime("%d%m%y")
    
    # Clean BSB format
    user_bsb_clean = user_bsb.replace("-", "").replace(" ", "")
    
    # Ensure BSB has hyphen for trace record
    if "-" not in user_bsb:
        user_bsb_with_hyphen = f"{user_bsb_clean[:3]}-{user_bsb_clean[3:6]}"
    else:
        user_bsb_with_hyphen = user_bsb
    
    # Calculate total amount for all payments
    total_amount = sum(float(asic_data['amount']) for asic_data in asic_data_list)
    total_amount_aba = format_aba_amount(str(total_amount))
    
    # Descriptive Record (Type 0) - exactly 120 chars per CEMTEX standard
    header = (
        "0"                                      # Pos 1: Record type (1)
        + " " * 17                               # Pos 2-18: Blank (17)
        + "01"                                   # Pos 19-20: Reel sequence (2)
        + "CBA"                                  # Pos 21-23: Financial institution (3)
        + " " * 7                                # Pos 24-30: Blank (7)
        + f"{user_name[:26]:<26}"               # Pos 31-56: User name (26)
        + apca_number                            # Pos 57-62: User ID/APCA number (6)
        + f"{'ASIC':<12}"                       # Pos 63-74: Entry description (12)
        + date_str                               # Pos 75-80: Processing date DDMMYY (6)
        + " " * 40                               # Pos 81-120: Blank (40)
    )
    
    # Generate credit detail records for each ASIC payment
    credit_details = []
    for asic_data in asic_data_list:
        amount_aba = format_aba_amount(asic_data['amount'])
        
        credit_detail = (
            "1"                                                      # Pos 1: Record type (1)
            + rba_bsb                                                # Pos 2-8: BSB with hyphen (7)
            + f"{rba_account:>9}"                                   # Pos 9-17: Account number (9)
            + "N"                                                    # Pos 18: Indicator (1)
            + "53"                                                   # Pos 19-20: Transaction code 53 for pay (2)
            + amount_aba                                             # Pos 21-30: Amount in cents (10)
            + f"{'ASIC':<32}"                                       # Pos 31-62: Account title - always ASIC (32)
            + f"{asic_data['bpay_reference'][:18]:<18}"            # Pos 63-80: Lodgement reference - BPay ref (18)
            + user_bsb_with_hyphen                                   # Pos 81-87: Trace BSB (7)
            + f"{user_account[:9]:>9}"                              # Pos 88-96: Trace account (9)
            + f"{user_name[:16]:<16}"                               # Pos 97-112: Remitter name (16)
            + "00000000"                                             # Pos 113-120: Withholding tax (8)
        )
        credit_details.append(credit_detail)
    
    # Single balancing debit record for the total amount
    debit_detail = (
        "1"                                                      # Pos 1: Record type (1)
        + user_bsb_with_hyphen                                   # Pos 2-8: User's BSB with hyphen (7)
        + f"{user_account[:9]:>9}"                              # Pos 9-17: User's account number (9)
        + " "                                                    # Pos 18: Space (1)
        + "13"                                                   # Pos 19-20: Transaction code 13 for debit (2)
        + total_amount_aba                                       # Pos 21-30: Total amount in cents (10)
        + f"{'Business':<32}"                                   # Pos 31-62: Description (32)
        + f"{date_str[:2]}{processing_date.strftime('%B')[:4]}{date_str[4:6]}"[:18].ljust(18)  # Pos 63-80: Reference (18)
        + user_bsb_with_hyphen                                   # Pos 81-87: Trace BSB (7)
        + f"{user_account[:9]:>9}"                              # Pos 88-96: Trace account (9)
        + f"{user_name[:16]:<16}"                               # Pos 97-112: Remitter name (16)
        + "00000000"                                             # Pos 113-120: Withholding tax (8)
    )
    
    # Calculate record count (credit records + 1 debit record)
    record_count = len(asic_data_list) + 1
    
    # File Total Record (Type 7) - exactly 120 chars per CEMTEX standard
    trailer = (
        "7"                           # Pos 1: Record type (1)
        + "999-999"                   # Pos 2-8: BSB filler (7)
        + " " * 12                    # Pos 9-20: Blank (12)
        + "0" * 10                    # Pos 21-30: Net total (10)
        + total_amount_aba            # Pos 31-40: Credit total (10)
        + total_amount_aba            # Pos 41-50: Debit total (10)
        + " " * 24                    # Pos 51-74: Blank (24)
        + f"{record_count:06d}"       # Pos 75-80: Record count (6)
        + " " * 40                    # Pos 81-120: Blank (40)
    )
    
    # Build the complete ABA file
    aba_content = header + "\r\n"
    for credit_detail in credit_details:
        aba_content += credit_detail + "\r\n"
    aba_content += debit_detail + "\r\n"
    aba_content += trailer + "\r\n"
    
    return aba_content

def main():
    st.set_page_config(page_title="ASIC ABA File Generator", page_icon="🏦")
    
    st.title("🏦 ASIC ABA File Generator")
    st.markdown("Generate ABA files for ASIC payments from uploaded statements")
    
    # Check password first - return early if not authenticated
    if not check_password():
        st.stop()
    
    # Only show content after authentication
    st.success("✅ Access granted - Welcome to TT Accountancy's ASIC Payment System")
    st.info("ℹ️ Configured for TT Accountancy Pty Ltd - fields are pre-filled with your details")
    
    # Initialize database after authentication
    init_database()
    
    # Add sidebar for processed statements
    with st.sidebar:
        st.header("👤 User Menu")
        if st.button("🔓 Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.divider()
        st.header("📋 Processed Statements")
        if st.button("View Processed Statements"):
            st.session_state.show_processed = True
        
        if st.session_state.get('show_processed', False):
            processed = get_processed_statements()
            if processed:
                st.subheader("Recently Processed")
                for stmt in processed[:10]:  # Show last 10
                    st.text(f"• {stmt[0]} - ${stmt[3]:.2f}")
                    st.caption(f"  {stmt[2]} | {stmt[4][:10]}")
            else:
                st.text("No statements processed yet")
    
    # User bank details input
    st.header("Your Bank Details")
    col1, col2 = st.columns(2)
    
    with col1:
        user_bsb = st.text_input("BSB", value="063245", help="Your bank BSB number")
        user_account = st.text_input("Account Number", value="10758330", help="Your bank account number")
        apca_number = st.text_input("APCA Number", value="301500", help="Your APCA User ID (6 digits)")
    
    with col2:
        user_name = st.text_input("Account Name", value="TT Accountancy Pty Ltd", help="Your account name")
        processing_date = st.date_input("Processing Date", datetime.now())
    
    # File upload
    st.header("Upload ASIC Statements")
    uploaded_files = st.file_uploader(
        "Choose ASIC PDF files", 
        type=['pdf'], 
        accept_multiple_files=True,
        help="You can upload multiple ASIC statements to create a batch payment"
    )
    
    if uploaded_files:
        # Process all PDFs with duplicate checking
        asic_data_list = []
        duplicates_found = []
        total_amount = 0
        
        with st.spinner(f"Extracting data from {len(uploaded_files)} PDF(s)..."):
            for i, uploaded_file in enumerate(uploaded_files):
                try:
                    # Get file content for hashing
                    file_content = uploaded_file.read()
                    uploaded_file.seek(0)  # Reset file pointer
                    file_hash = get_file_hash(file_content)
                    
                    # Extract ASIC data
                    asic_data = extract_asic_data(uploaded_file)
                    
                    # Check for duplicates
                    duplicate_check = check_duplicate_statement(
                        file_hash, 
                        asic_data['asic_reference'], 
                        asic_data['bpay_reference']
                    )
                    
                    # Add duplicate status to data
                    asic_data['is_duplicate'] = duplicate_check['file_duplicate'] is not None or duplicate_check['payment_duplicate'] is not None
                    asic_data['duplicate_info'] = duplicate_check
                    asic_data['file_hash'] = file_hash
                    asic_data['filename'] = uploaded_file.name
                    
                    asic_data_list.append(asic_data)
                    
                    if asic_data['is_duplicate']:
                        duplicates_found.append(asic_data)
                    else:
                        total_amount += float(asic_data['amount'])
                        
                except Exception as e:
                    st.error(f"Error processing {uploaded_file.name}: {str(e)}")
        
        if asic_data_list:
            # Display summary
            valid_statements = [data for data in asic_data_list if not data['is_duplicate']]
            
            if duplicates_found:
                st.warning(f"⚠️ Found {len(duplicates_found)} duplicate statement(s)")
                st.success(f"✅ {len(valid_statements)} new statement(s) ready for processing")
            else:
                st.success(f"✅ Data extracted from {len(asic_data_list)} statement(s)!")
            
            # Show duplicate warnings first
            if duplicates_found:
                st.subheader("🚨 Duplicate Statements Detected")
                for dup_data in duplicates_found:
                    with st.expander(f"⚠️ DUPLICATE: {dup_data['company_name']} - ${dup_data['amount']}", expanded=True):
                        st.error("This statement has already been processed!")
                        
                        if dup_data['duplicate_info']['file_duplicate']:
                            st.write("**Exact same file processed on:**", dup_data['duplicate_info']['file_duplicate'][1][:19])
                            st.write("**Original ABA file:**", dup_data['duplicate_info']['file_duplicate'][2])
                        
                        if dup_data['duplicate_info']['payment_duplicate']:
                            st.write("**Same payment processed on:**", dup_data['duplicate_info']['payment_duplicate'][1][:19])
                            st.write("**Original ABA file:**", dup_data['duplicate_info']['payment_duplicate'][2])
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Company", dup_data['company_name'])
                            st.metric("ACN", dup_data['acn'])
                            st.metric("Amount", f"${dup_data['amount']}")
                        with col2:
                            st.metric("ASIC Reference", dup_data['asic_reference'])
                            st.metric("BPay Reference", dup_data['bpay_reference'])
            
            # Total amount summary (excluding duplicates)
            if valid_statements:
                st.metric("Total Batch Amount", f"${total_amount:.2f}", help="Total amount for new ASIC payments (excluding duplicates)")
                
                # Display each new statement
                st.subheader("New ASIC Statements")
                for i, asic_data in enumerate(valid_statements):
                    status_icon = "✅"
                    with st.expander(f"{status_icon} Statement {i+1}: {asic_data['company_name']} - ${asic_data['amount']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Company", asic_data['company_name'])
                            st.metric("ACN", asic_data['acn'])
                            st.metric("Amount", f"${asic_data['amount']}")
                        with col2:
                            st.metric("ASIC Reference", asic_data['asic_reference'])
                            st.metric("BPay Reference", asic_data['bpay_reference'])
        
            # Bank details reminder
            st.info("""
            **Batch payments will be made to:**
            - Bank: Reserve Bank of Australia
            - BSB: 093-003
            - Account: 317118
            - Name: ASIC, Official Administered Receipts Account
            """)
            
            # Generate ABA file (only for non-duplicate statements)
            if valid_statements and st.button("Generate Batch ABA File", type="primary", disabled=len(valid_statements)==0):
                if user_bsb and user_account and user_name and apca_number:
                    # Generate ABA content for valid statements only
                    aba_content = generate_aba_file(
                        valid_statements, 
                        user_bsb, 
                        user_account, 
                        user_name,
                        processing_date,
                        apca_number
                    )
                    
                    # Create filename with date and company count
                    filename = f"ASIC_Batch_{len(valid_statements)}companies_{processing_date.strftime('%Y%m%d')}.ABA"
                    batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    
                    # Save processed statements to database
                    saved_count = 0
                    for asic_data in valid_statements:
                        if save_processed_statement(asic_data, asic_data['file_hash'], filename, batch_id):
                            saved_count += 1
                    
                    st.download_button(
                        label="📥 Download Batch ABA File",
                        data=aba_content,
                        file_name=filename,
                        mime="text/plain"
                    )
                    
                    # Show batch summary
                    st.success(f"✅ ABA file generated for {len(valid_statements)} companies with total amount ${total_amount:.2f}")
                    st.info(f"💾 {saved_count} statements saved to database to prevent future duplicates")
                    
                    # Show preview
                    st.subheader("ABA File Preview")
                    st.code(aba_content, language="text")
                    
                    # Show batch details
                    st.subheader("Batch Payment Summary")
                    batch_df = []
                    for i, asic_data in enumerate(valid_statements):
                        batch_df.append({
                            "Company": asic_data['company_name'],
                            "ACN": asic_data['acn'],
                            "Amount": f"${asic_data['amount']}",
                            "BPay Ref": asic_data['bpay_reference'],
                            "Status": "✅ Processed"
                        })
                    st.dataframe(batch_df, use_container_width=True)
                else:
                    st.error("Please fill in all your bank details including APCA number")
            
            elif not valid_statements:
                st.warning("No new statements to process. All uploaded statements are duplicates.")

if __name__ == "__main__":
    main()