#!/usr/bin/env python3

from datetime import datetime

def format_aba_amount(amount_str):
    """Convert amount string to ABA format (cents, 10 digits, zero-padded)"""
    try:
        amount = float(amount_str)
        cents = int(amount * 100)
        return f"{cents:010d}"
    except:
        return "0000000000"

def generate_aba_file(asic_data, user_bsb, user_account, user_name, processing_date):
    """Generate ABA file content based on ASIC data"""
    
    # RBA bank details (destination)
    rba_bsb = "093-003"
    rba_account = "317118"
    rba_name = "ASIC Official Receipts"
    
    # Format dates
    date_str = processing_date.strftime("%d%m%y")
    
    # Clean BSB format
    user_bsb_clean = user_bsb.replace("-", "").replace(" ", "")
    rba_bsb_clean = rba_bsb.replace("-", "").replace(" ", "")
    
    # Header record (Type 0)
    header = f"0{' ' * 17}01CBA       {user_name[:26]:<26}{user_bsb[:6]:<6}{date_str}{date_str}{' ' * 40}\r\n"
    
    # Detail record (Type 1)
    amount_aba = format_aba_amount(asic_data['amount'])
    
    # Transaction details
    detail = (
        f"1"
        f"{rba_bsb_clean:>7}-"
        f"{rba_account:>9} "
        f"N"
        f"50"
        f"{amount_aba}"
        f"{asic_data['company_name'][:32]:<32}"
        f"{asic_data['asic_reference'][:18]:<18}"
        f"{user_bsb_clean:>7}-"
        f"{user_account:>9}"
        f"{user_name[:16]:<16}"
        f"00000000\r\n"
    )
    
    # Trailer record (Type 7)
    trailer = (
        f"7"
        f"999-999{' ' * 12}"
        f"{amount_aba}"
        f"{amount_aba}"
        f"{' ' * 24}"
        f"000001{' ' * 40}\r\n"
    )
    
    return header + detail + trailer

# Test data
test_asic_data = {
    'company_name': 'ZYH PTY LTD',
    'acn': '612433502',
    'amount': '321.00',
    'asic_reference': '4X9702542480BA',
    'bpay_reference': '2296124335029'
}

# Generate test ABA
aba_content = generate_aba_file(
    test_asic_data,
    "063-245",
    "10758330",
    "TT Accountancy P",
    datetime(2025, 7, 28)
)

print("Generated ABA content:")
for line in aba_content.split('\r\n'):
    if line:
        print(f"Line {len(line)} chars: {repr(line)}")

# Compare with original ABA format
print("\nOriginal ABA format reference:")
original = """0                 01CBA       TT Accountancy Pty Ltd    30150025July25    280725                                        
1013-423169833067N500001096852Frontline Philippines Pty Ltd   INV-12709         063-245 10758330TT Accountancy P00000000
1063-014 10581708N500000010230Shi Tay                         ExpReim21Jul25    063-245 10758330TT Accountancy P00000000
1063-245 10758330 130001107082Business                        25July25          063-245 10758330TT Accountancy P00000000
7999-999            000000000000011070820001107082                        000003                                        """

for i, line in enumerate(original.split('\n')):
    if line:
        print(f"Original line {i+1}, {len(line)} chars")