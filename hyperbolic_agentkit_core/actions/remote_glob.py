from collections.abc import Callable
from pydantic import BaseModel, Field
from hyperbolic_agentkit_core.actions.hyperbolic_action import HyperbolicAction
from hyperbolic_agentkit_core.actions.ssh_manager import ssh_manager

REMOTE_GLOB_PROMPT = """
This tool will find files matching glob patterns on the remote server.

It takes the following inputs:
- pattern: Glob pattern to match (e.g., *.py, **/*.txt, test_*.sh)
- path: Base directory to search from (optional, default: current directory)
- max_results: Maximum number of results to return (optional, default: 100)

Important notes:
- Requires an active SSH connection (use ssh_connect first)
- Supports standard glob patterns:
  - * matches any characters
  - ? matches single character
  - [abc] matches any of a, b, c
  - ** matches directories recursively
- Results are sorted alphabetically
- Use this before remote_read_many_files to preview matches
"""

class RemoteGlobInput(BaseModel):
    """Input argument schema for remote file globbing."""
    pattern: str = Field(..., description="Glob pattern to match files")
    path: str = Field(".", description="Base directory to search from")
    max_results: int = Field(100, description="Maximum number of results")

def glob_remote_files(pattern: str, path: str = ".", max_results: int = 100) -> str:
    """
    Find files matching glob patterns on the remote server.
    
    Args:
        pattern: Glob pattern
        path: Base search directory
        max_results: Result limit
    
    Returns:
        str: List of matching files or error message
    """
    # Verify SSH is connected
    if not ssh_manager.is_connected:
        return "Error: No active SSH connection. Please connect to a remote server first using ssh_connect."
    
    # Change to the base directory first
    cd_command = f"cd '{path}' 2>&1 && pwd"
    cd_result = ssh_manager.execute(cd_command)
    if "No such file or directory" in cd_result:
        return f"Error: Directory '{path}' not found"
    
    # Use find command for glob patterns
    if '**' in pattern:
        # Handle recursive glob
        simple_pattern = pattern.replace('**/', '*/')
        find_command = f"cd '{path}' && find . -type f -path './{simple_pattern}' 2>/dev/null | sort | head -{max_results}"
    else:
        # Use shell globbing for simple patterns
        find_command = f"cd '{path}' && find . -type f -name '{pattern}' 2>/dev/null | sort | head -{max_results}"
    
    # Execute find
    results = ssh_manager.execute(find_command)
    
    if not results.strip():
        # Try with ls for simple patterns
        ls_command = f"cd '{path}' && ls -la {pattern} 2>/dev/null | grep -v '^d' | awk '{{print $NF}}' | head -{max_results}"
        results = ssh_manager.execute(ls_command)
        
        if not results.strip():
            return f"No files found matching pattern '{pattern}' in {path}"
    
    # Count total matches
    count_command = find_command.replace(f"head -{max_results}", "wc -l")
    total_matches = ssh_manager.execute(count_command).strip()
    
    # Format results
    files = [f.strip() for f in results.strip().split('\n') if f.strip()]
    
    if not files:
        return f"No files found matching pattern '{pattern}' in {path}"
    
    # Build formatted output
    formatted_output = [f"Files matching '{pattern}' in {path}:"]
    formatted_output.append("-" * 60)
    
    for file in files:
        # Get file size
        size_command = f"cd '{path}' && stat -c '%s' '{file}' 2>/dev/null || stat -f '%z' '{file}' 2>/dev/null"
        size = ssh_manager.execute(size_command).strip()
        
        if size and size.isdigit():
            formatted_output.append(f"{file} ({size} bytes)")
        else:
            formatted_output.append(file)
    
    try:
        total = int(total_matches)
        shown = len(files)
        if total > shown:
            formatted_output.append(f"\n[Showing {shown} of {total} total matches]")
    except:
        pass
    
    return '\n'.join(formatted_output)

class RemoteGlobAction(HyperbolicAction):
    """Remote file globbing action."""
    
    name: str = "remote_glob"
    description: str = REMOTE_GLOB_PROMPT
    args_schema: type[BaseModel] = RemoteGlobInput
    func: Callable[..., str] = glob_remote_files