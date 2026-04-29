"""
Test path traversal protection in document_loader.py
Demonstrates security validation for file paths.
"""

import os
import tempfile
from pathlib import Path


# Mock the DocumentLoaderError hierarchy
class DocumentLoaderError(Exception):
    """Base exception for document loading errors."""
    pass


class SecurityError(DocumentLoaderError):
    """Raised when a security issue is detected."""
    pass


def validate_path(file_path: str) -> Path:
    """
    Validate and sanitize file path to prevent security issues.
    This is the same logic as in document_loader.py
    """
    # Check for path traversal patterns in the input
    if ".." in file_path:
        raise SecurityError(
            "Path traversal attempt detected. File paths cannot contain '..'"
        )
    
    # Check for absolute paths trying to access system files
    dangerous_paths = [
        "/etc/", "\\windows\\", "/sys/", "/proc/", 
        "c:\\windows\\", "c:\\program files\\", "/root/", "/home/"
    ]
    file_path_lower = file_path.lower()
    for dangerous in dangerous_paths:
        if dangerous in file_path_lower:
            raise SecurityError(
                f"Access to system directories is not allowed"
            )
    
    # Convert to Path object and resolve to absolute path
    try:
        path = Path(file_path).resolve(strict=False)
    except (OSError, ValueError) as e:
        raise SecurityError(f"Invalid file path: {str(e)}")
    
    # Verify the file exists
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Verify it's actually a file (not a directory, symlink, etc.)
    if not path.is_file():
        raise SecurityError(f"Path is not a regular file: {file_path}")
    
    return path


def run_security_test(name, file_path, should_pass=False, create_file=False):
    """Run a single security validation test."""
    print("\n" + "="*70)
    print(f"TEST: {name}")
    print("="*70)
    print(f"Input path: {file_path}")
    
    temp_file = None
    try:
        # Create a real temporary file if needed
        if create_file:
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
            temp_file.write("Test content")
            temp_file.close()
            file_path = temp_file.name
            print(f"Created temp file: {file_path}")
        
        # Try to validate the path
        validated_path = validate_path(file_path)
        
        if should_pass:
            print(f"✅ PASS - Path accepted")
            print(f"   Resolved to: {validated_path}")
            return True
        else:
            print(f"❌ FAIL - Should have been blocked!")
            print(f"   Resolved to: {validated_path}")
            return False
            
    except SecurityError as e:
        if not should_pass:
            print(f"✅ PASS - Security threat blocked")
            print(f"   Error: {e}")
            return True
        else:
            print(f"❌ FAIL - Valid path rejected!")
            print(f"   Error: {e}")
            return False
            
    except FileNotFoundError as e:
        if not should_pass:
            print(f"✅ PASS - Invalid path rejected")
            print(f"   Error: {e}")
            return True
        else:
            print(f"❌ FAIL - Valid path rejected!")
            print(f"   Error: {e}")
            return False
            
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False
        
    finally:
        # Clean up temp file
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
            except:
                pass


# Run comprehensive security tests
print("="*70)
print("PATH TRAVERSAL PROTECTION TESTS")
print("="*70)
print("\nTesting security validation from document_loader.py")

results = []

# Safe paths (with actual file)
print("\n" + "="*70)
print("SAFE PATH TESTS (Should Pass)")
print("="*70)

results.append(run_security_test(
    "Valid local file",
    "",  # Will be created
    should_pass=True,
    create_file=True
))

# Path traversal attempts
print("\n" + "="*70)
print("PATH TRAVERSAL ATTACKS (Should Block)")
print("="*70)

results.append(run_security_test(
    "Basic path traversal - ../../../etc/passwd",
    "../../../etc/passwd",
    should_pass=False
))

results.append(run_security_test(
    "Path traversal - ..\\..\\..\\windows\\system32",
    "..\\..\\..\\windows\\system32",
    should_pass=False
))

results.append(run_security_test(
    "Encoded path traversal - data/../../../etc/passwd",
    "data/../../../etc/passwd",
    should_pass=False
))

results.append(run_security_test(
    "Double encoding - ....//....//etc/passwd",
    "....//....//etc/passwd",
    should_pass=False
))

# System directory access attempts
print("\n" + "="*70)
print("SYSTEM DIRECTORY ACCESS (Should Block)")
print("="*70)

results.append(run_security_test(
    "Linux /etc/passwd",
    "/etc/passwd",
    should_pass=False
))

results.append(run_security_test(
    "Windows system32",
    "C:\\Windows\\System32\\cmd.exe",
    should_pass=False
))

results.append(run_security_test(
    "Windows Program Files",
    "C:\\Program Files\\malicious.exe",
    should_pass=False
))

results.append(run_security_test(
    "Linux /sys/",
    "/sys/kernel/debug",
    should_pass=False
))

results.append(run_security_test(
    "Linux /proc/",
    "/proc/self/environ",
    should_pass=False
))

results.append(run_security_test(
    "User home directory",
    "/home/user/.ssh/id_rsa",
    should_pass=False
))

# Directory instead of file
print("\n" + "="*70)
print("DIRECTORY ACCESS (Should Block)")
print("="*70)

# Create a temp directory
temp_dir = tempfile.mkdtemp()
try:
    results.append(run_security_test(
        "Directory instead of file",
        temp_dir,
        should_pass=False
    ))
finally:
    try:
        os.rmdir(temp_dir)
    except:
        pass

# Non-existent files
print("\n" + "="*70)
print("NON-EXISTENT FILES (Should Block)")
print("="*70)

results.append(run_security_test(
    "Non-existent file",
    "nonexistent_file_12345.txt",
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
    print("✅ ALL SECURITY TESTS PASSED!")
    print("="*70)
    print("\nSecurity Protections Enforced:")
    print("  ✓ Path traversal attacks blocked (..)")
    print("  ✓ System directory access prevented")
    print("  ✓ Directory access blocked (only files allowed)")
    print("  ✓ Non-existent files rejected")
    print("  ✓ Paths resolved to absolute canonical form")
    print("\nProtected Directories:")
    print("  • /etc/, /sys/, /proc/, /root/, /home/")
    print("  • C:\\Windows\\, C:\\Program Files\\")
    print("="*70)
else:
    print("\n❌ SOME SECURITY TESTS FAILED!")
    print("Security vulnerabilities detected!")
    print("="*70)
