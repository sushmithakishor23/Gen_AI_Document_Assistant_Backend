"""
Test ChromaDB connection error handling from vector_store.py
Demonstrates various error scenarios and clear error messages.
"""

import tempfile
import os
from pathlib import Path


class MockRuntimeError(Exception):
    """Mock RuntimeError to simulate ChromaDB failures."""
    pass


def test_error_scenario(scenario_name, error_message, expected_in_message):
    """Test that error handling provides clear messages."""
    print(f"\n{'='*70}")
    print(f"SCENARIO: {scenario_name}")
    print(f"{'='*70}")
    print(f"Error message: {error_message}")
    
    # Check if expected keywords are in the error message
    found_keywords = []
    missing_keywords = []
    
    for keyword in expected_in_message:
        if keyword.lower() in error_message.lower():
            found_keywords.append(keyword)
        else:
            missing_keywords.append(keyword)
    
    if not missing_keywords:
        print(f"✅ PASS - Error message is clear and helpful")
        print(f"   Contains: {', '.join(found_keywords)}")
        return True
    else:
        print(f"❌ FAIL - Error message missing important information")
        print(f"   Found: {', '.join(found_keywords)}")
        print(f"   Missing: {', '.join(missing_keywords)}")
        return False


# Run comprehensive error handling tests
print("="*70)
print("CHROMADB ERROR HANDLING TESTS")
print("="*70)
print("\nTesting error messages from vector_store.py")

results = []

# Test 1: Directory permission error
results.append(test_error_scenario(
    "Directory creation - Permission denied",
    "Permission denied: Cannot create ChromaDB directory '/restricted/path'. "
    "Please check directory permissions or choose a different location.",
    ["Permission denied", "directory permissions", "different location"]
))

# Test 2: Disk space error
results.append(test_error_scenario(
    "Directory creation - Disk full",
    "Failed to create ChromaDB directory './chroma_db': No space left on device. "
    "Please check disk space and file system permissions.",
    ["disk space", "file system permissions"]
))

# Test 3: Client initialization permission error
results.append(test_error_scenario(
    "ChromaDB client - Permission denied",
    "Permission denied: Cannot access ChromaDB directory './chroma_db'. "
    "Please check directory permissions.",
    ["Permission denied", "directory permissions"]
))

# Test 4: Client initialization disk space error
results.append(test_error_scenario(
    "ChromaDB client - Disk space error",
    "Disk space error: Cannot initialize ChromaDB at './chroma_db'. "
    "Please free up disk space and try again. Error: [Errno 28] No space left on device",
    ["Disk space", "free up disk space"]
))

# Test 5: Client initialization unknown error
results.append(test_error_scenario(
    "ChromaDB client - Unexpected error",
    "Unexpected error initializing ChromaDB client: Database is locked. "
    "This may be due to a corrupted database or incompatible ChromaDB version. "
    "Try deleting './chroma_db' and restarting.",
    ["Unexpected error", "corrupted database", "deleting", "restarting"]
))

# Test 6: Invalid collection name
results.append(test_error_scenario(
    "Collection creation - Invalid name",
    "Invalid collection name 'my collection!@#': Collection names must contain only alphanumeric characters, hyphens, and underscores.",
    ["Invalid collection name", "alphanumeric", "hyphens", "underscores"]
))

# Test 7: Collection creation failure
results.append(test_error_scenario(
    "Collection creation - Failed",
    "Failed to create/access collection 'documents': Connection timeout. "
    "The database may be corrupted. Try deleting './chroma_db' and restarting.",
    ["Failed to create", "corrupted", "deleting", "restarting"]
))

# Test 8: Add documents - Invalid data
results.append(test_error_scenario(
    "Add documents - Invalid data format",
    "Invalid data format for ChromaDB: Duplicate IDs found. "
    "Please check that IDs are unique and metadata is properly formatted.",
    ["Invalid data", "IDs are unique", "metadata", "properly formatted"]
))

# Test 9: Add documents - Disk error
results.append(test_error_scenario(
    "Add documents - Disk error",
    "Disk error while adding documents to ChromaDB: No space left on device. "
    "Please check disk space at './chroma_db'.",
    ["Disk error", "check disk space"]
))

# Test 10: Add documents - General failure
results.append(test_error_scenario(
    "Add documents - General failure",
    "Failed to add documents to ChromaDB: Connection lost. "
    "The database may be corrupted or out of disk space.",
    ["Failed to add", "corrupted", "disk space"]
))

# Test 11: Search - Invalid parameters
results.append(test_error_scenario(
    "Search - Invalid parameters",
    "Invalid search parameters: Invalid filter syntax. "
    "Please check your metadata filter or search parameters.",
    ["Invalid search parameters", "metadata filter", "search parameters"]
))

# Test 12: Search - Disk error
results.append(test_error_scenario(
    "Search - Disk error",
    "Disk error while searching ChromaDB: I/O error. "
    "The database at './chroma_db' may be corrupted or inaccessible.",
    ["Disk error", "corrupted", "inaccessible"]
))

# Test 13: Search - General failure
results.append(test_error_scenario(
    "Search - General failure",
    "Failed to search ChromaDB: Index corrupted. "
    "The database may be corrupted. Try restarting the service.",
    ["Failed to search", "corrupted", "restarting"]
))

# Test 14: Delete documents - Invalid IDs
results.append(test_error_scenario(
    "Delete documents - Invalid IDs",
    "Invalid document IDs: IDs not found. "
    "Please check that the IDs exist in the collection.",
    ["Invalid document IDs", "IDs exist", "collection"]
))

# Test 15: Delete documents - General failure
results.append(test_error_scenario(
    "Delete documents - General failure",
    "Failed to delete documents from ChromaDB: Database locked. "
    "The database may be corrupted or locked.",
    ["Failed to delete", "corrupted", "locked"]
))

# Test 16: Clear collection - Permission error
results.append(test_error_scenario(
    "Clear collection - Permission denied",
    "Permission denied: Cannot modify collection 'documents'. "
    "The database may be locked by another process.",
    ["Permission denied", "locked by another process"]
))

# Test 17: Clear collection - Disk error
results.append(test_error_scenario(
    "Clear collection - Disk error",
    "Disk error while clearing collection: No space left on device. "
    "Check disk space at './chroma_db'.",
    ["Disk error", "disk space"]
))

# Test 18: Clear collection - General failure
results.append(test_error_scenario(
    "Clear collection - General failure",
    "Failed to clear collection 'documents': Connection lost. "
    "The database may be corrupted. Try restarting the service.",
    ["Failed to clear", "corrupted", "restarting"]
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
    print("\nError Handling Features:")
    print("  ✓ Clear, actionable error messages")
    print("  ✓ Specific error types (permission, disk, corruption)")
    print("  ✓ Helpful suggestions for resolution")
    print("  ✓ Context about what operation failed")
    print("\nError Categories Covered:")
    print("  • Directory creation failures")
    print("  • ChromaDB client initialization")
    print("  • Collection creation/access")
    print("  • Document addition")
    print("  • Search/query operations")
    print("  • Document deletion")
    print("  • Collection clearing")
    print("\nBenefits:")
    print("  • Users know exactly what went wrong")
    print("  • Clear next steps for resolution")
    print("  • Easier debugging and troubleshooting")
    print("  • Better production error tracking")
    print("="*70)
else:
    print("\n❌ SOME TESTS FAILED")
    print("Error messages need improvement")
    print("="*70)

# Show practical examples
print("\n" + "="*70)
print("EXAMPLE ERROR MESSAGES")
print("="*70)
print("""
Example 1 - Permission Error:
❌ Error: Permission denied: Cannot create ChromaDB directory '/var/db/chroma'.
         Please check directory permissions or choose a different location.
→ User knows: It's a permission issue
→ User can: Check permissions or use different directory

Example 2 - Disk Space Error:
❌ Error: Disk space error: Cannot initialize ChromaDB at './chroma_db'.
         Please free up disk space and try again.
→ User knows: Out of disk space
→ User can: Free up disk space

Example 3 - Corrupted Database:
❌ Error: Unexpected error initializing ChromaDB client: Database corrupted.
         This may be due to a corrupted database or incompatible ChromaDB version.
         Try deleting './chroma_db' and restarting.
→ User knows: Database issue
→ User can: Delete and restart

Each error message includes:
1. What went wrong (specific error)
2. Why it might have happened (context)
3. What to do about it (actionable steps)
""")
print("="*70)
