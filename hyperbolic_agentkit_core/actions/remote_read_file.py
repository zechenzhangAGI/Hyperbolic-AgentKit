from collections.abc import Callable
from pydantic import BaseModel, Field
from hyperbolic_agentkit_core.actions.hyperbolic_action import HyperbolicAction
from hyperbolic_agentkit_core.actions.ssh_manager import ssh_manager

REMOTE_READ_FILE_PROMPT = """
This tool will read contents of a file on the remote server via SSH.

It takes the following inputs:
- file_path: The path to the file to read
- max_lines: Maximum number of lines to read (optional, default: 1000)

Important notes:
- Requires an active SSH connection (use ssh_connect first)
- Large files are truncated to max_lines
- Binary files will show as unreadable
- Use absolute paths or paths relative to home directory
"""

class RemoteReadFileInput(BaseModel):
    """Input argument schema for remote file reading."""
    file_path: str = Field(..., description="The path to the file to read on the remote server")
    max_lines: int = Field(1000, description="Maximum number of lines to read")

def read_remote_file(file_path: str, max_lines: int = 1000) -> str:
    """
    Read contents of a file on the remote server.
    
    Args:
        file_path: The path to the file to read
        max_lines: Maximum number of lines to read
    
    Returns:
        str: File contents or error message
    """
    # Verify SSH is connected
    if not ssh_manager.is_connected:
        return "Error: No active SSH connection. Please connect to a remote server first using ssh_connect."
    
    # Check if file exists and is readable
    check_command = f"test -f '{file_path}' && test -r '{file_path}' && echo 'OK' || echo 'ERROR'"
    check_result = ssh_manager.execute(check_command).strip()
    
    if check_result != 'OK':
        # Try to get more specific error
        ls_command = f"ls -la '{file_path}' 2>&1"
        ls_result = ssh_manager.execute(ls_command)
        if "No such file or directory" in ls_result:
            return f"Error: File '{file_path}' not found"
        elif "Permission denied" in ls_result:
            return f"Error: Permission denied reading '{file_path}'"
        else:
            return f"Error: Cannot read file '{file_path}'"
    
    # Check if it's a binary file
    file_type_command = f"file -b '{file_path}' 2>&1"
    file_type = ssh_manager.execute(file_type_command).strip()
    
    if "text" not in file_type.lower() and "empty" not in file_type.lower():
        return f"Error: File '{file_path}' appears to be binary ({file_type})"
    
    # Read the file with line limit
    read_command = f"head -n {max_lines} '{file_path}' 2>&1"
    content = ssh_manager.execute(read_command)
    
    # Check if file was truncated
    line_count_command = f"wc -l < '{file_path}' 2>&1"
    total_lines = ssh_manager.execute(line_count_command).strip()
    
    try:
        total_lines_int = int(total_lines)
        if total_lines_int > max_lines:
            content += f"\n\n[File truncated. Showing first {max_lines} of {total_lines_int} lines]"
    except:
        pass
    
    return content

class RemoteReadFileAction(HyperbolicAction):
    """Remote file reading action."""
    
    name: str = "remote_read_file"
    description: str = REMOTE_READ_FILE_PROMPT
    args_schema: type[BaseModel] = RemoteReadFileInput
    func: Callable[..., str] = read_remote_file