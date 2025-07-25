from collections.abc import Callable
from pydantic import BaseModel, Field
from hyperbolic_agentkit_core.actions.hyperbolic_action import HyperbolicAction
from hyperbolic_agentkit_core.actions.ssh_manager import ssh_manager
from typing import Optional

REMOTE_GREP_PROMPT = """
This tool will search for patterns in files on the remote server using grep.

It takes the following inputs:
- pattern: The search pattern (supports regex)
- path: File or directory to search in (optional, default: current directory)
- recursive: Whether to search recursively in directories (optional, default: True)
- case_sensitive: Whether search is case sensitive (optional, default: True)
- show_line_numbers: Whether to show line numbers (optional, default: True)
- max_results: Maximum number of results to return (optional, default: 100)

Important notes:
- Requires an active SSH connection (use ssh_connect first)
- Supports regular expressions
- Use recursive=True to search in subdirectories
- Results show filename:line_number:content format
"""

class RemoteGrepInput(BaseModel):
    """Input argument schema for remote file searching."""
    pattern: str = Field(..., description="The search pattern (regex supported)")
    path: str = Field(".", description="File or directory to search in")
    recursive: bool = Field(True, description="Search recursively in directories")
    case_sensitive: bool = Field(True, description="Case sensitive search")
    show_line_numbers: bool = Field(True, description="Show line numbers in results")
    max_results: int = Field(100, description="Maximum number of results")

def grep_remote_files(
    pattern: str,
    path: str = ".",
    recursive: bool = True,
    case_sensitive: bool = True,
    show_line_numbers: bool = True,
    max_results: int = 100
) -> str:
    """
    Search for patterns in files on the remote server.
    
    Args:
        pattern: Search pattern
        path: Where to search
        recursive: Search subdirectories
        case_sensitive: Case sensitivity
        show_line_numbers: Include line numbers
        max_results: Result limit
    
    Returns:
        str: Search results or error message
    """
    # Verify SSH is connected
    if not ssh_manager.is_connected:
        return "Error: No active SSH connection. Please connect to a remote server first using ssh_connect."
    
    # Build grep command
    grep_flags = []
    
    if recursive:
        grep_flags.append("-r")
    if not case_sensitive:
        grep_flags.append("-i")
    if show_line_numbers:
        grep_flags.append("-n")
    
    # Always show filename when searching multiple files
    grep_flags.append("-H")
    
    # Escape special characters in pattern
    escaped_pattern = pattern.replace("'", "'\"'\"'")
    
    # Build full command
    grep_command = f"grep {' '.join(grep_flags)} '{escaped_pattern}' {path} 2>/dev/null | head -{max_results}"
    
    # Execute search
    results = ssh_manager.execute(grep_command)
    
    if not results.strip():
        return f"No matches found for pattern '{pattern}' in {path}"
    
    # Count total matches
    count_command = f"grep {' '.join(grep_flags)} '{escaped_pattern}' {path} 2>/dev/null | wc -l"
    total_matches = ssh_manager.execute(count_command).strip()
    
    # Format results
    lines = results.strip().split('\n')
    formatted_results = [f"Search results for '{pattern}' in {path}:"]
    formatted_results.append("-" * 60)
    
    for line in lines:
        formatted_results.append(line)
    
    try:
        total = int(total_matches)
        shown = len(lines)
        if total > shown:
            formatted_results.append(f"\n[Showing {shown} of {total} total matches]")
    except:
        pass
    
    return '\n'.join(formatted_results)

class RemoteGrepAction(HyperbolicAction):
    """Remote file search action."""
    
    name: str = "remote_grep"
    description: str = REMOTE_GREP_PROMPT
    args_schema: type[BaseModel] = RemoteGrepInput
    func: Callable[..., str] = grep_remote_files