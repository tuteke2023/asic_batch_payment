#!/usr/bin/env python3

from app import format_aba_amount, generate_aba_file
from datetime import datetime

# Test data similar to what would be extracted from ASIC PDF
test_asic_data = {
    'company_name': 'ZYH PTY LTD',
    'acn': '612433502',
    'amount': '321.00',
    'asic_reference': '4X9702542480BA',
    'bpay_reference': '2296124335029'
}

# Test user details
user_bsb = "063-245"
user_account = "10758330"
user_name = "TT Accountancy P"
processing_date = datetime(2025, 7, 28)

# Generate ABA content
aba_content = generate_aba_file(
    test_asic_data,
    user_bsb,
    user_account,
    user_name,
    processing_date
)

print("Generated ABA File:")
print("-" * 50)
print(repr(aba_content))
print("-" * 50)
print("\nFormatted view:")
print(aba_content)

# Test amount formatting
print("\nAmount formatting tests:")
print(f"321.00 -> {format_aba_amount('321.00')}")
print(f"1096.85 -> {format_aba_amount('1096.85')}")
print(f"102.30 -> {format_aba_amount('102.30')}")