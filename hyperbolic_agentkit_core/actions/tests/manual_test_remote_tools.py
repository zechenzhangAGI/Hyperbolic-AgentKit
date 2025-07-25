#!/usr/bin/env python3
"""
Manual testing script for remote file tools.
This script helps test the tools with a real SSH connection.

Usage:
    python manual_test_remote_tools.py <host> <username> <port>

Example:
    python manual_test_remote_tools.py gpu-instance.example.com ubuntu 22
"""

import sys
import os
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from hyperbolic_agentkit_core.actions.ssh_access import connect_ssh
from hyperbolic_agentkit_core.actions.remote_shell import execute_remote_command
from hyperbolic_agentkit_core.actions.remote_list_directory import list_remote_directory
from hyperbolic_agentkit_core.actions.remote_read_file import read_remote_file
from hyperbolic_agentkit_core.actions.remote_write_file import write_remote_file
from hyperbolic_agentkit_core.actions.remote_read_many_files import read_many_remote_files
from hyperbolic_agentkit_core.actions.remote_replace import replace_in_remote_file
from hyperbolic_agentkit_core.actions.remote_grep import grep_remote_files
from hyperbolic_agentkit_core.actions.remote_glob import glob_remote_files


def print_test(test_name, result, expected_substring=None):
    """Pretty print test results."""
    status = "✓ PASS" if (expected_substring is None or expected_substring in result) else "✗ FAIL"
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"STATUS: {status}")
    print(f"RESULT:\n{result[:500]}{'...' if len(result) > 500 else ''}")
    if expected_substring and expected_substring not in result:
        print(f"EXPECTED TO CONTAIN: {expected_substring}")
    print('='*60)
    return status == "✓ PASS"


def run_all_tests(host, username, port=22):
    """Run comprehensive tests on all remote file tools."""
    print(f"\n🚀 Starting Remote File Tools Test Suite")
    print(f"Target: {username}@{host}:{port}")
    print(f"Time: {datetime.now()}")
    
    passed = 0
    failed = 0
    
    # Test 1: SSH Connection
    print("\n" + "="*60)
    print("PHASE 1: SSH CONNECTION")
    print("="*60)
    
    result = connect_ssh(host, username, port=port)
    if print_test("SSH Connection", result, "Successfully connected"):
        passed += 1
    else:
        failed += 1
        print("\n❌ Cannot proceed without SSH connection!")
        return
    
    # Create test directory
    test_dir = f"/tmp/remote_tools_test_{int(time.time())}"
    result = execute_remote_command(f"mkdir -p {test_dir}")
    
    # Test 2: List Directory
    print("\n" + "="*60)
    print("PHASE 2: DIRECTORY OPERATIONS")
    print("="*60)
    
    result = list_remote_directory(test_dir)
    if print_test("List Empty Directory", result, "(empty)"):
        passed += 1
    else:
        failed += 1
    
    # Test 3: Write File
    print("\n" + "="*60)
    print("PHASE 3: FILE WRITE OPERATIONS")
    print("="*60)
    
    test_content = "Hello, World!\nThis is a test file.\nLine 3 with special chars: $@#'\"!"
    result = write_remote_file(f"{test_dir}/test1.txt", test_content)
    if print_test("Write Simple File", result, "Successfully written"):
        passed += 1
    else:
        failed += 1
    
    # Test 4: Write with special characters
    special_content = """#!/bin/bash
echo "Testing 'quotes' and \"double quotes\""
VAR=$HOME
echo ${VAR}
# Comment with special chars: <>&|;
"""
    result = write_remote_file(f"{test_dir}/script.sh", special_content)
    if print_test("Write File with Special Characters", result, "Successfully written"):
        passed += 1
    else:
        failed += 1
    
    # Test 5: Append to file
    result = write_remote_file(f"{test_dir}/test1.txt", "\nAppended line 4", append=True)
    if print_test("Append to File", result, "Successfully appended"):
        passed += 1
    else:
        failed += 1
    
    # Test 6: Read File
    print("\n" + "="*60)
    print("PHASE 4: FILE READ OPERATIONS")
    print("="*60)
    
    result = read_remote_file(f"{test_dir}/test1.txt")
    if print_test("Read File", result, "Hello, World!") and "Appended line 4" in result:
        passed += 1
    else:
        failed += 1
    
    # Test 7: Create multiple files for testing
    for i in range(5):
        execute_remote_command(f"echo 'Test file {i}' > {test_dir}/file{i}.txt")
    execute_remote_command(f"echo 'def test_function():' > {test_dir}/test.py")
    execute_remote_command(f"echo '    return True' >> {test_dir}/test.py")
    
    # Test 8: List directory with files
    result = list_remote_directory(test_dir)
    if print_test("List Directory with Files", result, "[FILE]"):
        passed += 1
    else:
        failed += 1
    
    # Test 9: Glob files
    print("\n" + "="*60)
    print("PHASE 5: GLOB AND SEARCH OPERATIONS")
    print("="*60)
    
    result = glob_remote_files("*.txt", test_dir)
    if print_test("Glob .txt Files", result, "file0.txt"):
        passed += 1
    else:
        failed += 1
    
    # Test 10: Read many files
    result = read_many_remote_files([f"{test_dir}/file0.txt", f"{test_dir}/file1.txt"])
    if print_test("Read Multiple Files", result, "Test file 0") and "Test file 1" in result:
        passed += 1
    else:
        failed += 1
    
    # Test 11: Grep search
    result = grep_remote_files("Test", test_dir)
    if print_test("Grep Search", result, "Test file"):
        passed += 1
    else:
        failed += 1
    
    # Test 12: Replace in file
    print("\n" + "="*60)
    print("PHASE 6: FILE MODIFICATION OPERATIONS")
    print("="*60)
    
    result = replace_in_remote_file(f"{test_dir}/test1.txt", "World", "Universe", "all")
    if print_test("Replace Text in File", result, "Successfully replaced"):
        passed += 1
    else:
        failed += 1
    
    # Verify replacement
    result = read_remote_file(f"{test_dir}/test1.txt")
    if print_test("Verify Replacement", result, "Universe"):
        passed += 1
    else:
        failed += 1
    
    # Test 13: Edge cases
    print("\n" + "="*60)
    print("PHASE 7: EDGE CASES AND ERROR HANDLING")
    print("="*60)
    
    # Non-existent file
    result = read_remote_file(f"{test_dir}/nonexistent.txt")
    if print_test("Read Non-existent File", result, "Error"):
        passed += 1
    else:
        failed += 1
    
    # Permission test (try to write to root)
    result = write_remote_file("/root/test.txt", "test")
    if print_test("Write to Protected Directory", result, "Error"):
        passed += 1
    else:
        failed += 1
    
    # Large content test
    large_content = "A" * 10000 + "\n" + "B" * 10000
    result = write_remote_file(f"{test_dir}/large.txt", large_content)
    if print_test("Write Large File", result, "Successfully written"):
        passed += 1
    else:
        failed += 1
    
    # Test 14: Cleanup
    print("\n" + "="*60)
    print("PHASE 8: CLEANUP")
    print("="*60)
    
    result = execute_remote_command(f"rm -rf {test_dir}")
    if print_test("Cleanup Test Directory", result, ""):
        passed += 1
    else:
        failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {passed + failed}")
    print(f"✓ Passed: {passed}")
    print(f"✗ Failed: {failed}")
    print(f"Success Rate: {(passed/(passed+failed)*100):.1f}%")
    print("="*60)
    
    return passed, failed


def main():
    """Main function to run tests."""
    if len(sys.argv) < 3:
        print("Usage: python manual_test_remote_tools.py <host> <username> [port]")
        print("Example: python manual_test_remote_tools.py gpu-instance.example.com ubuntu 22")
        sys.exit(1)
    
    host = sys.argv[1]
    username = sys.argv[2]
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 22
    
    # Set SSH key path if needed
    if 'SSH_PRIVATE_KEY_PATH' not in os.environ:
        os.environ['SSH_PRIVATE_KEY_PATH'] = os.path.expanduser('~/.ssh/id_rsa')
    
    try:
        passed, failed = run_all_tests(host, username, port)
        sys.exit(0 if failed == 0 else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()