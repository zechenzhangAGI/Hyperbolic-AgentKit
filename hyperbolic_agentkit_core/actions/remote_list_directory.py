from collections.abc import Callable
from pydantic import BaseModel, Field
from hyperbolic_agentkit_core.actions.hyperbolic_action import HyperbolicAction
from hyperbolic_agentkit_core.actions.ssh_manager import ssh_manager
import json

REMOTE_LIST_DIRECTORY_PROMPT = """
This tool will list contents of a directory on the remote server via SSH.

It takes the following inputs:
- path: The directory path to list (optional, default: current directory)

Important notes:
- Requires an active SSH connection (use ssh_connect first)
- Returns formatted directory listing with file types and permissions
- Hidden files (starting with .) are included
- Use absolute paths or paths relative to home directory
"""

class RemoteListDirectoryInput(BaseModel):
    """Input argument schema for remote directory listing."""
    path: str = Field(".", description="The directory path to list on the remote server")

def list_remote_directory(path: str = ".") -> str:
    """
    List contents of a directory on the remote server.
    
    Args:
        path: The directory path to list
    
    Returns:
        str: Formatted directory listing or error message
    """
    # Verify SSH is connected
    if not ssh_manager.is_connected:
        return "Error: No active SSH connection. Please connect to a remote server first using ssh_connect."
    
    # Build command for detailed listing
    command = f"ls -la {path} 2>&1 | head -100"
    
    # Execute command
    result = ssh_manager.execute(command)
    
    # Check for errors
    if "No such file or directory" in result:
        return f"Error: Directory '{path}' not found"
    
    # Format the output
    lines = result.strip().split('\n')
    if len(lines) < 2:
        return f"Directory: {path}\n(empty)"
    
    # Parse ls output for better formatting
    formatted_output = [f"Directory: {path}"]
    formatted_output.append("-" * 50)
    
    for line in lines[1:]:  # Skip total line
        if line.strip():
            parts = line.split(None, 8)
            if len(parts) >= 9:
                permissions = parts[0]
                size = parts[4]
                name = parts[8]
                
                # Determine file type
                if permissions.startswith('d'):
                    file_type = "[DIR] "
                elif permissions.startswith('l'):
                    file_type = "[LINK]"
                else:
                    file_type = "[FILE]"
                
                formatted_output.append(f"{file_type} {name} ({size} bytes)")
    
    return "\n".join(formatted_output)

class RemoteListDirectoryAction(HyperbolicAction):
    """Remote directory listing action."""
    
    name: str = "remote_list_directory"
    description: str = REMOTE_LIST_DIRECTORY_PROMPT
    args_schema: type[BaseModel] = RemoteListDirectoryInput
    func: Callable[..., str] = list_remote_directory