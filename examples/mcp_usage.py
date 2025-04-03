"""
Example demonstrating MCP (Model Context Protocol) usage for context-aware sound profiles.

This script starts the MCP monitor which watches the active window title.
Based on rules defined in config.json, it will automatically load different
sound profiles (e.g., when switching to Notepad or VS Code).

Prerequisites:
1. Ensure 'pywin32' and 'psutil' are installed (`pip install pywin32 psutil`).
2. Have sound profiles saved in the 'profiles/' directory that match the names
   used in 'config.json' (e.g., "Quiet Profile Example", "Coding Focus", 
   "Windows Default - Backup"). You can create these using the CLI:
   `python cli.py save-profile "Profile Name"`
3. Modify `config.json` to match the applications and profiles you want to use.
"""

import sys
import os
import logging
import time
import json

# Adjust the path to import from the root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from sound_manager import SoundManager
    from mcp_handler import MCPHandler, DEFAULT_CONFIG_PATH
    from logging_config import setup_logging
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Ensure the script is run from the project root or the root is in the Python path.")
    print("Also ensure pywin32 and psutil are installed.")
    sys.exit(1)

# --- Initialization ---
setup_logging(level=logging.INFO) # Configure logging
logger = logging.getLogger(__name__)

def check_required_profiles(manager: SoundManager, config_path: str = DEFAULT_CONFIG_PATH):
    """Checks if profiles mentioned in the MCP config exist."""
    logger.info("Checking if required sound profiles exist...")
    required_profiles = set()
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            mcp_config = config.get("mcp_profiles", {})
            if mcp_config.get("default_profile"):
                required_profiles.add(mcp_config["default_profile"])
            for context in mcp_config.get("contexts", []):
                if context.get("profile"):
                    required_profiles.add(context["profile"])
    except Exception as e:
        logger.error(f"Could not read MCP config '{config_path}' to check profiles: {e}")
        return False # Assume failure if config can't be read

    if not required_profiles:
        logger.warning("No profiles are configured in the MCP section of the config file.")
        return True # Technically no profiles are *missing*
        
    available_profiles = manager.get_available_profiles()
    missing_profiles = required_profiles - set(available_profiles)

    if missing_profiles:
        logger.error("The following sound profiles required by MCP config are missing:")
        for profile in missing_profiles:
            logger.error(f"  - {profile}")
        logger.error("Please create these profiles using 'python cli.py save-profile \\\"<Profile Name>\\\"'")
        return False
    else:
        logger.info("All required sound profiles found.")
        return True

def run_mcp_example():
    """Runs the MCP monitoring example."""
    logger.info("--- Starting MCP Handler Example ---")

    try:
        manager = SoundManager()
        
        # Check if profiles needed by config exist before starting
        if not check_required_profiles(manager):
             logger.error("MCP Handler cannot function correctly without the required profiles. Exiting.")
             return

        mcp_handler = MCPHandler(manager) # Uses config.json by default

        logger.info("Starting MCP monitoring...")
        mcp_handler.start_monitoring()

        print("\n" + "*" * 60)
        print("* MCP Monitoring Active!")
        print("* Switch focus between different applications (e.g., Notepad, VS Code, others)." )
        print("* Check the console output to see if sound profiles are being switched based")
        print("* on the rules in config.json.")
        print("* Press Ctrl+C to stop monitoring.")
        print("*")
        print("*" * 60 + "\n")

        # Keep the script running while the monitor thread works
        while True:
            time.sleep(1)

    except ImportError as e:
         # This might happen if deps were missing despite initial check
        logger.error(f"Import error during MCP initialization: {e}") 
        logger.error("Please ensure pywin32 and psutil are installed.")
    except KeyboardInterrupt:
        logger.info("Ctrl+C detected. Stopping MCP monitoring...")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        # Ensure monitoring is stopped on exit
        if 'mcp_handler' in locals() and mcp_handler:
            logger.info("Cleaning up: Stopping monitor thread.")
            mcp_handler.stop_monitoring()
        logger.info("--- MCP Handler Example Finished ---")

if __name__ == "__main__":
    run_mcp_example() 