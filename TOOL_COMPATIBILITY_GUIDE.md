# Tool Compatibility Guide for Claude Sonnet 4

## Overview

This guide documents compatibility issues and best practices for tools when using Claude Sonnet 4 (claude-sonnet-4-20250514) with the Hyperbolic AgentKit.

## Key Findings

### Working Tools (Single Required Parameter)
These tools work reliably with Claude Sonnet 4:
- `remote_shell` - 1 required parameter
- `remote_read_file` - 1 required parameter (+ 1 optional)
- `remote_list_directory` - 0 required parameters (1 optional)
- `remote_glob` - 1 required parameter (+ 2 optional)
- `remote_grep` - 1 required parameter (+ 5 optional)

### Problematic Tools (Multiple Required Parameters)
These tools may cause issues:
- `remote_write_file` - 2 required parameters
- `remote_replace` - 3 required parameters

## Best Practices for Tool Design

### 1. **Keep It Simple**
Follow the pattern from `remote_shell.py`:
```python
PROMPT = """
Brief description of what the tool does.

Input parameters:
- param1: Description of parameter
- param2: Description of optional parameter (optional)

Important notes:
- Note about prerequisites
- Note about behavior
"""
```

### 2. **Minimize Required Parameters**
- Single required parameter tools work best
- Use optional parameters with sensible defaults
- Consider combining parameters if multiple are always needed

### 3. **Clear, Concise Descriptions**
- Avoid JSON examples in prompts
- Don't use complex formatting
- Keep prompt under 500 characters if possible

### 4. **Field Descriptions**
Keep them simple:
```python
# Good
field: str = Field(..., description="The file path on the remote server")

# Avoid
field: str = Field(..., description="The file path (REQUIRED - must be provided!)")
```

## Workarounds for Multi-Parameter Tools

### Option 1: Alternative Single-Parameter Tool
Created `remote_create_file` as a workaround:
```python
# Instead of:
remote_write_file(file_path="script.py", content="code")

# Use:
remote_create_file(file_spec="script.py|||code")
```

### Option 2: Simplified Prompts
Updated `remote_write_file` to match the working pattern:
- Removed JSON examples
- Simplified to bullet points
- Kept it concise

## Testing New Tools

When adding new tools:
1. Test with single required parameter first
2. Add optional parameters one at a time
3. Keep prompts under 500 characters
4. Use the same format as `remote_shell`

## Future Considerations

1. **Monitor LangChain Updates**: This may be resolved in future versions
2. **Consider Tool Wrappers**: Create simplified versions of complex tools
3. **User Education**: Guide users to be explicit about all parameters in their prompts

## Example of a Well-Designed Tool

```python
PROMPT = """
Execute commands on the remote server.

Input parameters:
- command: The command to execute

Important notes:
- Requires active SSH connection
- Returns command output
"""

class ToolInput(BaseModel):
    command: str = Field(..., description="The command to execute")
```

This pattern has proven most reliable with Claude Sonnet 4.