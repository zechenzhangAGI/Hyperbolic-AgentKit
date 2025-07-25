from collections.abc import Callable
from pydantic import BaseModel, Field
from hyperbolic_agentkit_core.actions.hyperbolic_action import HyperbolicAction
from hyperbolic_agentkit_core.actions.ssh_manager import ssh_manager
import base64

REMOTE_WRITE_FILE_PROMPT = """
This tool will write content to a file on the remote server via SSH.

It takes the following inputs:
- file_path: The path where to write the file on the remote server
- content: The content to write to the file
- append: Whether to append to existing file instead of overwriting (optional, default: false)

Important notes:
- Requires an active SSH connection (use ssh_connect first)
- Creates parent directories if they don't exist
- The content parameter must contain the complete file contents
- Use append=true to add content to existing files
"""

class RemoteWriteFileInput(BaseModel):
    """Input argument schema for remote file writing."""
    file_path: str = Field(..., description="The path where to write the file on the remote server")
    content: str = Field(..., description="The content to write to the file")
    append: bool = Field(False, description="Whether to append to existing file instead of overwriting")

def write_remote_file(file_path: str, content: str, append: bool = False) -> str:
    """
    Write content to a file on the remote server.
    
    Args:
        file_path: The path where to write the file
        content: The content to write
        append: Whether to append instead of overwrite
    
    Returns:
        str: Success message or error
    """
    # Verify SSH is connected
    if not ssh_manager.is_connected:
        return "Error: No active SSH connection. Please connect to a remote server first using ssh_connect."
    
    # Create directory if it doesn't exist
    dir_path = file_path.rsplit('/', 1)[0] if '/' in file_path else '.'
    if dir_path and dir_path != '.':
        mkdir_command = f"mkdir -p '{dir_path}' 2>&1"
        mkdir_result = ssh_manager.execute(mkdir_command)
        if "Permission denied" in mkdir_result:
            return f"Error: Permission denied creating directory '{dir_path}'"
    
    # For large content, use base64 encoding to avoid shell escaping issues
    if len(content) > 1000 or '\n' in content or '"' in content or "'" in content:
        # Encode content as base64
        encoded_content = base64.b64encode(content.encode('utf-8')).decode('ascii')
        
        # Write using base64 decode
        if append:
            write_command = f"echo '{encoded_content}' | base64 -d >> '{file_path}' 2>&1"
        else:
            write_command = f"echo '{encoded_content}' | base64 -d > '{file_path}' 2>&1"
    else:
        # For small content, use echo directly
        escaped_content = content.replace("'", "'\"'\"'")
        if append:
            write_command = f"echo '{escaped_content}' >> '{file_path}' 2>&1"
        else:
            write_command = f"echo '{escaped_content}' > '{file_path}' 2>&1"
    
    # Execute write command
    result = ssh_manager.execute(write_command)
    
    if result.strip():
        if "Permission denied" in result:
            return f"Error: Permission denied writing to '{file_path}'"
        else:
            return f"Error writing file: {result}"
    
    # Verify file was written
    verify_command = f"test -f '{file_path}' && wc -c < '{file_path}' 2>&1"
    size_result = ssh_manager.execute(verify_command).strip()
    
    try:
        file_size = int(size_result)
        action = "appended to" if append else "written to"
        return f"Successfully {action} '{file_path}' ({file_size} bytes)"
    except:
        return f"File written but could not verify: {size_result}"

class RemoteWriteFileAction(HyperbolicAction):
    """Remote file writing action."""
    
    name: str = "remote_write_file"
    description: str = REMOTE_WRITE_FILE_PROMPT
    args_schema: type[BaseModel] = RemoteWriteFileInput
    func: Callable[..., str] = write_remote_file