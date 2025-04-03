# Prompt: Create a Python System Sound Manager with MCP Support

## Task Description
Create a comprehensive Python script that can programmatically control Windows system sounds with Model Context Protocol (MCP) support. The script should be able to:

1. List all available system sounds
2. Play specific system sounds on demand
3. Change default system sounds by modifying Windows registry entries
4. Save and load user-defined sound profiles
5. Implement MCP for context-aware sound management

## Technical Requirements
- Must work on Windows 10/11
- Must handle permission requirements gracefully
- Use appropriate error handling throughout
- Include comprehensive docstrings and comments
- Implement proper logging
- Create a simple command-line interface for manual operation
- Support programmatic integration with other applications

## MCP Support Details
The script should implement Model Context Protocol support that enables:
- Context-aware sound selection based on active applications or system state
- Ability to define sound profiles that activate based on specific contexts
- Support for environment variables and system state detection
- Event-driven responses to system changes

## Code Structure Guidelines
- Modular design with clear separation of concerns
- Class-based architecture for the main functionality
- Utility functions for common operations
- Configuration management using JSON or YAML
- Proper type hinting throughout
- Asynchronous support where appropriate

## Sample Usage Examples
Include examples showing how the script would be used in different scenarios:
1. Command-line usage for manual sound switching
2. Programmatic usage from another Python application
3. Event-driven usage based on system context changes
4. Profile-based management for different user scenarios

## Security Considerations
- Address how the script handles registry modifications safely
- Include validation for all user inputs
- Incorporate proper error handling for permission issues
- Discuss potential security implications and mitigations

## Additional Features
- Volume control integration
- Audio device switching capabilities
- Sound testing functionality
- Profile export/import features
- Scheduled sound profile changes