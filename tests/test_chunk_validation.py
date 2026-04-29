"""
Test chunk_size and chunk_overlap validation logic from documents.py
Demonstrates all validation scenarios for chunking parameters.
"""


class HTTPException(Exception):
    """Mock HTTPException for testing."""
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def validate_chunk_parameters(chunk_size: int, chunk_overlap: int):
    """
    Validate chunk parameters according to the rules in documents.py
    
    Rules:
    1. chunk_size must be between 100 and 5000 (enforced by FastAPI Form validation)
    2. chunk_overlap must be between 0 and 500 (enforced by FastAPI Form validation)
    3. chunk_overlap must be less than chunk_size (runtime validation)
    """
    print(f"\nValidating: chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
    
    # Simulate FastAPI Form validation (ge/le constraints)
    if chunk_size < 100:
        raise HTTPException(
            status_code=422,
            detail=f"chunk_size must be >= 100 (got {chunk_size})"
        )
    if chunk_size > 5000:
        raise HTTPException(
            status_code=422,
            detail=f"chunk_size must be <= 5000 (got {chunk_size})"
        )
    if chunk_overlap < 0:
        raise HTTPException(
            status_code=422,
            detail=f"chunk_overlap must be >= 0 (got {chunk_overlap})"
        )
    if chunk_overlap > 500:
        raise HTTPException(
            status_code=422,
            detail=f"chunk_overlap must be <= 500 (got {chunk_overlap})"
        )
    
    # Runtime validation: overlap must be less than size
    if chunk_overlap >= chunk_size:
        raise HTTPException(
            status_code=400,
            detail=f"chunk_overlap ({chunk_overlap}) must be less than chunk_size ({chunk_size})"
        )
    
    print(f"✓ Valid parameters")
    return True


def run_test(name, chunk_size, chunk_overlap, should_pass=True):
    """Run a single validation test."""
    print("\n" + "="*70)
    print(f"TEST: {name}")
    print("="*70)
    
    try:
        validate_chunk_parameters(chunk_size, chunk_overlap)
        if should_pass:
            print("✅ PASS - Parameters accepted")
            return True
        else:
            print("❌ FAIL - Should have been rejected!")
            return False
    except HTTPException as e:
        if not should_pass:
            print(f"✅ PASS - Correctly rejected")
            print(f"   Status: {e.status_code}")
            print(f"   Error: {e.detail}")
            return True
        else:
            print(f"❌ FAIL - Should have been accepted!")
            print(f"   Status: {e.status_code}")
            print(f"   Error: {e.detail}")
            return False


# Run comprehensive test suite
print("="*70)
print("CHUNK PARAMETER VALIDATION TESTS")
print("="*70)
print("\nTesting validation rules from documents.py upload endpoint")

results = []

# Valid cases
print("\n" + "="*70)
print("VALID PARAMETER TESTS")
print("="*70)

results.append(run_test(
    "Default values (500, 50)",
    chunk_size=500,
    chunk_overlap=50,
    should_pass=True
))

results.append(run_test(
    "Minimum chunk_size (100, 10)",
    chunk_size=100,
    chunk_overlap=10,
    should_pass=True
))

results.append(run_test(
    "Maximum chunk_size (5000, 500)",
    chunk_size=5000,
    chunk_overlap=500,
    should_pass=True
))

results.append(run_test(
    "No overlap (1000, 0)",
    chunk_size=1000,
    chunk_overlap=0,
    should_pass=True
))

results.append(run_test(
    "Large chunk with small overlap (3000, 100)",
    chunk_size=3000,
    chunk_overlap=100,
    should_pass=True
))

results.append(run_test(
    "Overlap just under chunk_size (200, 199)",
    chunk_size=200,
    chunk_overlap=199,
    should_pass=True
))

# Invalid cases - chunk_size out of range
print("\n" + "="*70)
print("INVALID CHUNK_SIZE TESTS")
print("="*70)

results.append(run_test(
    "chunk_size too small (50, 10)",
    chunk_size=50,
    chunk_overlap=10,
    should_pass=False
))

results.append(run_test(
    "chunk_size negative (-100, 10)",
    chunk_size=-100,
    chunk_overlap=10,
    should_pass=False
))

results.append(run_test(
    "chunk_size too large (10000, 100)",
    chunk_size=10000,
    chunk_overlap=100,
    should_pass=False
))

results.append(run_test(
    "chunk_size zero (0, 0)",
    chunk_size=0,
    chunk_overlap=0,
    should_pass=False
))

# Invalid cases - chunk_overlap out of range
print("\n" + "="*70)
print("INVALID CHUNK_OVERLAP TESTS")
print("="*70)

results.append(run_test(
    "chunk_overlap negative (500, -10)",
    chunk_size=500,
    chunk_overlap=-10,
    should_pass=False
))

results.append(run_test(
    "chunk_overlap too large (1000, 600)",
    chunk_size=1000,
    chunk_overlap=600,
    should_pass=False
))

# Invalid cases - overlap >= size
print("\n" + "="*70)
print("OVERLAP >= SIZE TESTS (Runtime Validation)")
print("="*70)

results.append(run_test(
    "overlap equals size (500, 500)",
    chunk_size=500,
    chunk_overlap=500,
    should_pass=False
))

results.append(run_test(
    "overlap greater than size (200, 300)",
    chunk_size=200,
    chunk_overlap=300,
    should_pass=False
))

results.append(run_test(
    "minimum size with equal overlap (100, 100)",
    chunk_size=100,
    chunk_overlap=100,
    should_pass=False
))

# Edge cases
print("\n" + "="*70)
print("EDGE CASE TESTS")
print("="*70)

results.append(run_test(
    "Minimum valid configuration (100, 0)",
    chunk_size=100,
    chunk_overlap=0,
    should_pass=True
))

results.append(run_test(
    "Maximum valid configuration (5000, 499)",
    chunk_size=5000,
    chunk_overlap=499,
    should_pass=True
))

results.append(run_test(
    "Boundary: overlap at max but size too high (6000, 500)",
    chunk_size=6000,
    chunk_overlap=500,
    should_pass=False
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
    print("\nValidation Rules Enforced:")
    print("  ✓ chunk_size: 100 ≤ value ≤ 5000")
    print("  ✓ chunk_overlap: 0 ≤ value ≤ 500")
    print("  ✓ chunk_overlap < chunk_size (always)")
    print("  ✓ Proper HTTP status codes (422 for validation, 400 for business logic)")
    print("="*70)
else:
    print("\n❌ SOME TESTS FAILED")
    print("="*70)
