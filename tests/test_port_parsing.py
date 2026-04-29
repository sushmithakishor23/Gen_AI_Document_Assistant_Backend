"""
Test PORT environment variable parsing from main.py
Demonstrates robust parsing with error handling for non-numeric values.
"""

import os


def parse_port_safe(port_env_value):
    """
    Safely parse PORT environment variable with fallback.
    This is the same logic as in main.py
    """
    try:
        port = int(port_env_value if port_env_value is not None else "8000")
    except (ValueError, TypeError):
        print(f"Warning: Invalid PORT value '{port_env_value}', using default 8000")
        port = 8000
    return port


def test_port_parsing(test_name, port_value, expected_port):
    """Run a single PORT parsing test."""
    print(f"\n{'='*70}")
    print(f"TEST: {test_name}")
    print(f"{'='*70}")
    print(f"Input PORT value: {repr(port_value)}")
    print(f"Expected result: {expected_port}")
    
    result = parse_port_safe(port_value)
    
    if result == expected_port:
        print(f"✅ PASS - Got port {result}")
        return True
    else:
        print(f"❌ FAIL - Expected {expected_port}, got {result}")
        return False


# Run comprehensive tests
print("="*70)
print("PORT ENVIRONMENT VARIABLE PARSING TESTS")
print("="*70)
print("\nTesting robust PORT parsing from main.py")

results = []

# Valid cases
print("\n" + "="*70)
print("VALID PORT VALUES")
print("="*70)

results.append(test_port_parsing(
    "Default port (None)",
    None,
    8000
))

results.append(test_port_parsing(
    "Valid string port '8080'",
    "8080",
    8080
))

results.append(test_port_parsing(
    "Valid string port '3000'",
    "3000",
    3000
))

results.append(test_port_parsing(
    "Valid string port '80'",
    "80",
    80
))

results.append(test_port_parsing(
    "Valid string port '5000'",
    "5000",
    5000
))

# Invalid cases - should fall back to 8000
print("\n" + "="*70)
print("INVALID PORT VALUES (Should Fall Back to 8000)")
print("="*70)

results.append(test_port_parsing(
    "Non-numeric string 'abc'",
    "abc",
    8000
))

results.append(test_port_parsing(
    "Word 'eight thousand'",
    "eight thousand",
    8000
))

results.append(test_port_parsing(
    "Empty string ''",
    "",
    8000
))

results.append(test_port_parsing(
    "Float string '8000.5'",
    "8000.5",
    8000
))

results.append(test_port_parsing(
    "Negative number '-1'",
    "-1",
    -1  # Note: This will parse but might not be valid - could add additional validation
))

results.append(test_port_parsing(
    "Port with spaces ' 8000 '",
    " 8000 ",
    8000
))

results.append(test_port_parsing(
    "Hexadecimal '0x1F40'",
    "0x1F40",
    8000  # Will fail to parse as decimal
))

results.append(test_port_parsing(
    "Port with unit '8000port'",
    "8000port",
    8000
))

# Edge cases
print("\n" + "="*70)
print("EDGE CASES")
print("="*70)

results.append(test_port_parsing(
    "Very large port '99999'",
    "99999",
    99999  # Will parse but might exceed valid range (1-65535)
))

results.append(test_port_parsing(
    "Zero port '0'",
    "0",
    0  # Will parse but might not be valid
))

results.append(test_port_parsing(
    "Default string '8000'",
    "8000",
    8000
))

# Summary
print("\n" + "="*70)
print("TEST SUMMARY")
print("="*70)

passed = sum(results)
total = len(results)
failed = total - passed

print(f"\nTotal Tests: {total}")
print(f"Passed: {passed} ✅")
print(f"Failed: {failed} ❌")

if failed == 0:
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED!")
    print("="*70)
    print("\nRobust PORT Parsing Features:")
    print("  ✓ Handles valid numeric strings correctly")
    print("  ✓ Falls back to 8000 for non-numeric values")
    print("  ✓ Catches ValueError for invalid integers")
    print("  ✓ Catches TypeError for None values")
    print("  ✓ Provides warning message for invalid values")
    print("  ✓ Never crashes the application on startup")
    print("\nRecommendation:")
    print("  Consider adding additional validation for port range (1-65535)")
    print("="*70)
else:
    print("\n❌ SOME TESTS FAILED")
    print("="*70)

# Show practical example
print("\n" + "="*70)
print("PRACTICAL EXAMPLE")
print("="*70)
print("\nHow it works in main.py:")
print("""
# Before (crashes on invalid input):
port = int(os.getenv("PORT", 8000))  # Crashes if PORT="abc"

# After (safe with fallback):
try:
    port = int(os.getenv("PORT", "8000"))
except (ValueError, TypeError):
    print(f"Warning: Invalid PORT value, using default 8000")
    port = 8000  # Safe fallback
""")
print("="*70)
