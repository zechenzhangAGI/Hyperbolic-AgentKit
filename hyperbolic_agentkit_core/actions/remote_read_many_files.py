from collections.abc import Callable
from pydantic import BaseModel, Field
from hyperbolic_agentkit_core.actions.hyperbolic_action import HyperbolicAction
from hyperbolic_agentkit_core.actions.ssh_manager import ssh_manager
from typing import List, Union

REMOTE_READ_MANY_FILES_PROMPT = """
This tool will read contents of multiple files or files matching glob patterns on the remote server.

It takes the following inputs:
- file_patterns: List of file paths or glob patterns to read
- max_lines_per_file: Maximum lines to read per file (optional, default: 100)
- max_files: Maximum number of files to read (optional, default: 10)

Important notes:
- Requires an active SSH connection (use ssh_connect first)
- Supports glob patterns like *.py, **/*.txt
- Each file's content is labeled with its path
- Large result sets are truncated
- Use remote_glob first to preview matches
"""

class RemoteReadManyFilesInput(BaseModel):
    """Input argument schema for reading multiple remote files."""
    file_patterns: List[str] = Field(..., description="List of file paths or glob patterns to read")
    max_lines_per_file: int = Field(100, description="Maximum lines to read per file")
    max_files: int = Field(10, description="Maximum number of files to read")

def read_many_remote_files(file_patterns: List[str], max_lines_per_file: int = 100, max_files: int = 10) -> str:
    """
    Read contents of multiple files on the remote server.
    
    Args:
        file_patterns: List of file paths or glob patterns
        max_lines_per_file: Maximum lines per file
        max_files: Maximum number of files
    
    Returns:
        str: Combined file contents or error message
    """
    # Verify SSH is connected
    if not ssh_manager.is_connected:
        return "Error: No active SSH connection. Please connect to a remote server first using ssh_connect."
    
    all_files = []
    
    # Expand each pattern
    for pattern in file_patterns:
        # Use find for glob patterns
        if '*' in pattern or '?' in pattern or '[' in pattern:
            find_command = f"find . -type f -name '{pattern}' 2>/dev/null | head -20"
            find_result = ssh_manager.execute(find_command)
            files = [f.strip() for f in find_result.strip().split('\n') if f.strip()]
            all_files.extend(files)
        else:
            # Direct file path
            all_files.append(pattern)
    
    # Remove duplicates and limit
    all_files = list(dict.fromkeys(all_files))[:max_files]
    
    if not all_files:
        return "No files found matching the specified patterns"
    
    # Read each file
    results = []
    files_read = 0
    
    for file_path in all_files:
        # Check if file exists
        check_command = f"test -f '{file_path}' && echo 'OK' || echo 'ERROR'"
        if ssh_manager.execute(check_command).strip() != 'OK':
            results.append(f"\n{'='*60}\nFile: {file_path}\nError: File not found\n")
            continue
        
        # Read file content
        read_command = f"head -n {max_lines_per_file} '{file_path}' 2>&1"
        content = ssh_manager.execute(read_command)
        
        # Get line count
        line_count_command = f"wc -l < '{file_path}' 2>&1"
        total_lines = ssh_manager.execute(line_count_command).strip()
        
        # Format output
        results.append(f"\n{'='*60}\nFile: {file_path}")
        
        try:
            total_lines_int = int(total_lines)
            if total_lines_int > max_lines_per_file:
                results.append(f"(Showing first {max_lines_per_file} of {total_lines_int} lines)")
        except:
            pass
        
        results.append(f"{'='*60}\n{content}")
        
        files_read += 1
        if files_read >= max_files:
            results.append(f"\n\n[Reached maximum of {max_files} files]")
            break
    
    return '\n'.join(results)

class RemoteReadManyFilesAction(HyperbolicAction):
    """Remote multiple file reading action."""
    
    name: str = "remote_read_many_files"
    description: str = REMOTE_READ_MANY_FILES_PROMPT
    args_schema: type[BaseModel] = RemoteReadManyFilesInput
    func: Callable[..., str] = read_many_remote_files