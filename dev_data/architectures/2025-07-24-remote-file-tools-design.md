# Remote File Manipulation Tools Design

**Date**: 2025-07-24
**Author**: Claude (AI Assistant)
**Status**: Implemented

## Overview

Added comprehensive file manipulation tools for remote SSH sessions, allowing agents to read, write, search, and manage files on GPU compute nodes.

## New Tools

### 1. **remote_list_directory**
Lists contents of directories on remote server.
- Shows file types (FILE/DIR/LINK)
- Displays file sizes
- Handles errors gracefully

### 2. **remote_read_file**
Reads single file content from remote server.
- Checks if file is binary
- Limits output to prevent overwhelming responses
- Shows truncation notice for large files

### 3. **remote_write_file**
Writes content to files on remote server.
- Creates directories if needed
- Supports append mode
- Uses base64 encoding for special characters
- Creates file with proper permissions

### 4. **remote_read_many_files**
Reads multiple files or glob patterns.
- Supports wildcards and glob patterns
- Limits files and lines per file
- Shows clear separation between files

### 5. **remote_replace**
In-place text replacement in files.
- Creates backup before modification
- Supports first/last/all/nth occurrence
- Handles special characters properly
- Reports number of replacements

### 6. **remote_grep**
Searches for patterns in files.
- Supports regex patterns
- Recursive search option
- Case sensitivity control
- Shows line numbers

### 7. **remote_glob**
Finds files matching glob patterns.
- Supports ** for recursive matching
- Shows file sizes
- Useful for previewing before bulk operations

## Design Decisions

### 1. **Error Handling**
- All tools check SSH connection first
- Clear error messages for common issues
- Graceful degradation (e.g., partial results)

### 2. **Safety Features**
- Backup creation before modifications
- File type checking (avoid binary files)
- Size limits to prevent overwhelming output
- Permission checks before operations

### 3. **Special Character Handling**
- Base64 encoding for write operations
- Proper escaping for shell commands
- Handles newlines, quotes, special chars

### 4. **Output Formatting**
- Consistent format across tools
- Clear headers and separators
- Truncation notices when applicable
- File metadata (size, type) where relevant

## Usage Examples

### Example 1: Exploring Project Structure
```
Agent: remote_list_directory(path="/home/ubuntu/project")
Agent: remote_glob(pattern="**/*.py", path="/home/ubuntu/project")
Agent: remote_read_file(file_path="/home/ubuntu/project/main.py")
```

### Example 2: Modifying Configuration
```
Agent: remote_read_file(file_path="config.yaml")
Agent: remote_replace(file_path="config.yaml", 
                      search_text="batch_size: 32", 
                      replace_text="batch_size: 64")
```

### Example 3: Creating Experiment Script
```
Agent: remote_write_file(
    file_path="experiment.py",
    content="import torch\n# Experiment code..."
)
Agent: remote_shell(command="python experiment.py")
```

### Example 4: Searching Codebase
```
Agent: remote_grep(pattern="def train", path=".", recursive=True)
Agent: remote_read_many_files(file_patterns=["train.py", "model.py"])
```

## Integration with Existing Tools

These tools complement the existing remote_shell tool:
- Use remote_shell for execution
- Use file tools for inspection/modification
- Combine for complete remote development

## Security Considerations

1. **Path Traversal**: Tools use relative paths from SSH session
2. **Permission Checks**: Operations fail gracefully on permission errors
3. **Size Limits**: Prevent DoS from large file operations
4. **Backup Creation**: Replace operations create backups

## Future Enhancements

1. **File Upload/Download**: SCP integration for binary files
2. **Compression Support**: Handle .tar.gz, .zip files
3. **Diff Tool**: Show changes before/after modifications
4. **File Monitoring**: Watch files for changes