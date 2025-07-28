#!/usr/bin/env python3

import sys
sys.path.append('.')

from app import generate_aba_file
from datetime import datetime

# Test multiple ASIC payments (simulated data)
print("Testing batch ASIC payment generation...")
print("-" * 60)

# Simulate multiple ASIC statements
batch_asic_data = [
    {
        'company_name': 'ZYH PTY LTD',
        'acn': '612433502',
        'amount': '321.00',
        'asic_reference': '4X9702542480BA',
        'bpay_reference': '2296124335029'
    },
    {
        'company_name': 'ABC CORP PTY LTD',
        'acn': '123456789',
        'amount': '450.00',
        'asic_reference': '5A8703653491CB',
        'bpay_reference': '3307135446140'
    },
    {
        'company_name': 'XYZ ENTERPRISES PTY LTD',
        'acn': '987654321',
        'amount': '275.50',
        'asic_reference': '6B9814764502DC',
        'bpay_reference': '4418246557251'
    }
]

print(f"Batch contains {len(batch_asic_data)} companies:")
total_amount = 0
for i, company in enumerate(batch_asic_data):
    print(f"  {i+1}. {company['company_name']} - ${company['amount']}")
    total_amount += float(company['amount'])

print(f"Total batch amount: ${total_amount:.2f}")
print()

# Generate batch ABA file
print("Generating batch ABA file...")
print("-" * 60)

aba_content = generate_aba_file(
    batch_asic_data,
    "063-245",
    "10758330", 
    "TT Accountancy P",
    datetime(2025, 7, 28),
    "301500"
)

print("Generated batch ABA file content:")
print("=" * 60)
lines = aba_content.split('\r\n')
for i, line in enumerate(lines):
    if line:
        print(f"Line {i+1} ({len(line)} chars): {line}")
print("=" * 60)

# Verify line lengths
print("\nLine length verification:")
for i, line in enumerate(lines):
    if line:
        expected = 120
        if len(line) == expected:
            print(f"✓ Line {i+1}: {len(line)} chars (correct)")
        else:
            print(f"✗ Line {i+1}: {len(line)} chars (expected {expected})")

print("\n" + "-" * 60)
print("Batch ABA file structure:")
print(f"- Header (Type 0): File information")
print(f"- Credit Details (Type 1): {len(batch_asic_data)} payments to ASIC")
print(f"- Debit Detail (Type 1): 1 balancing debit from user's account")
print(f"- Trailer (Type 7): Totals and record count")
print(f"\nBatch summary:")
print(f"- Total payments: {len(batch_asic_data)}")
print(f"- Total amount: ${total_amount:.2f}")
print(f"- Total records: {len(batch_asic_data) + 1} (balanced)")
print(f"- All payments to: Reserve Bank of Australia (093-003, 317118)")
print(f"- Single debit from: User account (063-245, 10758330)")