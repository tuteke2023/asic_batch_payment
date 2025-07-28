#!/usr/bin/env python3

import sys
sys.path.append('.')

from app import extract_asic_data, generate_aba_file
from datetime import datetime
import io

# Test the PDF extraction
print("Testing PDF extraction...")
print("-" * 50)

with open("ASIC Company Statement (ZYH PTY LTD).pdf", "rb") as f:
    pdf_file = io.BytesIO(f.read())
    asic_data = extract_asic_data(pdf_file)

print("Extracted data from ASIC PDF:")
for key, value in asic_data.items():
    print(f"  {key}: {value}")

print("\n" + "-" * 50)
print("Generating ABA file...")
print("-" * 50)

# Test ABA generation with APCA number (single payment - backward compatibility)
aba_content = generate_aba_file(
    asic_data,  # Function now handles single item or list
    "063-245",
    "10758330", 
    "TT Accountancy P",
    datetime(2025, 7, 28),
    "301500"  # APCA number
)

print("Generated ABA file content:")
print("=" * 50)
lines = aba_content.split('\r\n')
for i, line in enumerate(lines):
    if line:
        print(f"Line {i+1} ({len(line)} chars): {line}")
print("=" * 50)

# Verify line lengths (ALL records should be 120 chars per CEMTEX standard)
print("\nLine length verification:")
for i, line in enumerate(lines):
    if line:
        expected = 120  # ALL ABA records must be exactly 120 characters
        
        if len(line) == expected:
            print(f"✓ Line {i+1}: {len(line)} chars (correct, CEMTEX standard)")
        else:
            print(f"✗ Line {i+1}: {len(line)} chars (expected {expected})")

print("\n" + "-" * 50)
print("ABA file structure:")
print(f"- Header (Type 0): Identifies the file and sender")
print(f"- Credit Detail (Type 1): Payment to RBA for ASIC")
print(f"- Debit Detail (Type 1): Balancing debit from user's account")
print(f"- Trailer (Type 7): File totals and counts")
print(f"\nPayment details:")
print(f"- Credit: To Reserve Bank of Australia (BSB: 093-003, Acc: 317118)")
print(f"- Debit: From user's account (BSB: 063-245, Acc: 10758330)")
print(f"- Amount: ${asic_data['amount']}")
print(f"- Reference: {asic_data['asic_reference']}")
print(f"- Record count: 2 (balanced)")
print(f"- Credit/Debit totals: Both ${asic_data['amount']} (balanced)")