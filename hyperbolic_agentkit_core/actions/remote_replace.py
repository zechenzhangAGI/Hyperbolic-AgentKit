from collections.abc import Callable
from pydantic import BaseModel, Field
from hyperbolic_agentkit_core.actions.hyperbolic_action import HyperbolicAction
from hyperbolic_agentkit_core.actions.ssh_manager import ssh_manager
import base64

REMOTE_REPLACE_PROMPT = """
This tool will replace text in a file on the remote server (in-place modification).

It takes the following inputs:
- file_path: The file to modify
- search_text: The exact text to search for
- replace_text: The text to replace with
- occurrence: Which occurrence to replace - 'first', 'last', 'all', or a number (optional, default: 'all')

Important notes:
- Requires an active SSH connection (use ssh_connect first)
- Creates a backup before modification
- Search text must match exactly (including whitespace)
- Use 'all' to replace all occurrences
- Use a number (1, 2, etc.) to replace specific occurrence
"""

class RemoteReplaceInput(BaseModel):
    """Input argument schema for remote file replacement."""
    file_path: str = Field(..., description="The file to modify on the remote server")
    search_text: str = Field(..., description="The exact text to search for")
    replace_text: str = Field(..., description="The text to replace with")
    occurrence: str = Field("all", description="Which occurrence to replace: 'first', 'last', 'all', or a number")

def replace_in_remote_file(file_path: str, search_text: str, replace_text: str, occurrence: str = "all") -> str:
    """
    Replace text in a file on the remote server.
    
    Args:
        file_path: The file to modify
        search_text: Text to search for
        replace_text: Text to replace with
        occurrence: Which occurrence(s) to replace
    
    Returns:
        str: Success message with count or error
    """
    # Verify SSH is connected
    if not ssh_manager.is_connected:
        return "Error: No active SSH connection. Please connect to a remote server first using ssh_connect."
    
    # Check if file exists and is writable
    check_command = f"test -f '{file_path}' && test -w '{file_path}' && echo 'OK' || echo 'ERROR'"
    if ssh_manager.execute(check_command).strip() != 'OK':
        return f"Error: File '{file_path}' not found or not writable"
    
    # Create backup
    backup_command = f"cp '{file_path}' '{file_path}.bak' 2>&1"
    backup_result = ssh_manager.execute(backup_command)
    if backup_result.strip() and "Permission denied" in backup_result:
        return f"Error: Cannot create backup of '{file_path}'"
    
    # Encode search and replace text to handle special characters
    search_b64 = base64.b64encode(search_text.encode('utf-8')).decode('ascii')
    replace_b64 = base64.b64encode(replace_text.encode('utf-8')).decode('ascii')
    
    # Build sed command based on occurrence
    if occurrence.lower() == "all":
        sed_flags = "g"
    elif occurrence.lower() == "first":
        sed_flags = ""
    elif occurrence.lower() == "last":
        # For last occurrence, we need a different approach
        sed_command = f"""
        search_text=$(echo '{search_b64}' | base64 -d)
        replace_text=$(echo '{replace_b64}' | base64 -d)
        tac '{file_path}' | sed "0,/\\Q${{search_text}}\\E/s//\\Q${{replace_text}}\\E/" | tac > '{file_path}.tmp' && mv '{file_path}.tmp' '{file_path}'
        """
        result = ssh_manager.execute(sed_command)
        if result.strip():
            return f"Error during replacement: {result}"
    else:
        # Numeric occurrence
        try:
            occ_num = int(occurrence)
            sed_command = f"""
            search_text=$(echo '{search_b64}' | base64 -d)
            replace_text=$(echo '{replace_b64}' | base64 -d)
            sed -i "0,/\\Q${{search_text}}\\E/{{{occ_num}s//\\Q${{replace_text}}\\E/}}" '{file_path}' 2>&1
            """
            result = ssh_manager.execute(sed_command)
            if result.strip():
                return f"Error during replacement: {result}"
        except ValueError:
            return f"Error: Invalid occurrence value '{occurrence}'. Use 'all', 'first', 'last', or a number"
    
    # For all and first, use standard sed
    if occurrence.lower() in ["all", "first"]:
        sed_command = f"""
        search_text=$(echo '{search_b64}' | base64 -d)
        replace_text=$(echo '{replace_b64}' | base64 -d)
        sed -i 's/\\Q'"$search_text"'\\E/'"$replace_text"'/{sed_flags}' '{file_path}' 2>&1
        """
        result = ssh_manager.execute(sed_command)
        if result.strip():
            return f"Error during replacement: {result}"
    
    # Count replacements made
    diff_command = f"diff '{file_path}.bak' '{file_path}' | grep -c '^<' 2>/dev/null || echo '0'"
    change_count = ssh_manager.execute(diff_command).strip()
    
    try:
        changes = int(change_count)
        if changes == 0:
            return f"No occurrences of search text found in '{file_path}'"
        else:
            return f"Successfully replaced {changes} occurrence(s) in '{file_path}' (backup saved as '{file_path}.bak')"
    except:
        return f"Replacement completed in '{file_path}' (backup saved as '{file_path}.bak')"

class RemoteReplaceAction(HyperbolicAction):
    """Remote file text replacement action."""
    
    name: str = "remote_replace"
    description: str = REMOTE_REPLACE_PROMPT
    args_schema: type[BaseModel] = RemoteReplaceInput
    func: Callable[..., str] = replace_in_remote_file