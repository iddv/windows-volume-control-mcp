import logging
import time
import json
import re
import os
import sys
import threading
import ctypes
from typing import Optional, Dict, List, Any

# Need pywin32 for active window detection
try:
    import win32gui
    import win32process
    import psutil # Using psutil to get process name easily
except ImportError:
    print("MCP Handler requires 'pywin32' and 'psutil'. Please install them: pip install pywin32 psutil")
    # Allow module to load but disable functionality if imports fail
    win32gui = None
    win32process = None
    psutil = None 

# Ensure project root is discoverable
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sound_manager import SoundManager

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = "config.json"
DEFAULT_MONITOR_INTERVAL = 10 # seconds

class MCPHandler:
    """Handles Model Context Protocol (MCP) for context-aware sound profile switching."""

    def __init__(self, sound_manager: SoundManager, config_path: str = DEFAULT_CONFIG_PATH):
        """Initializes the MCP Handler.

        Args:
            sound_manager (SoundManager): An instance of the SoundManager.
            config_path (str): Path to the configuration file (JSON).
        """
        if not all([win32gui, win32process, psutil]):
             raise ImportError("MCP dependencies (pywin32, psutil) are missing.")
             
        self.sound_manager = sound_manager
        self.config_path = config_path
        self.config: Dict[str, Any] = self._load_config()
        self.mcp_config: Dict[str, Any] = self.config.get("mcp_profiles", {})
        self.contexts: List[Dict[str, str]] = self.mcp_config.get("contexts", [])
        self.default_profile: Optional[str] = self.mcp_config.get("default_profile")
        self.monitor_interval: int = self.mcp_config.get("monitor_interval_seconds", DEFAULT_MONITOR_INTERVAL)
        
        self.current_profile: Optional[str] = None # Track the currently active profile
        self.last_active_window_title: Optional[str] = None
        
        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None
        
        logger.info("MCP Handler initialized.")
        logger.debug(f"Context rules loaded: {len(self.contexts)}")
        logger.debug(f"Default profile: {self.default_profile}")
        logger.debug(f"Monitor interval: {self.monitor_interval}s")

    def _load_config(self) -> Dict:
        """Loads the configuration from the JSON file."""
        if not os.path.exists(self.config_path):
            logger.error(f"Configuration file not found: {self.config_path}")
            return {}
        try:
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
            return config_data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from {self.config_path}: {e}", exc_info=True)
            return {}
        except IOError as e:
            logger.error(f"Failed to read config file {self.config_path}: {e}", exc_info=True)
            return {}

    def _get_active_window_info(self) -> Optional[Dict[str, Any]]:
        """Gets information about the currently active foreground window.
        
        Uses win32gui to get the window handle (HWND) and title, and
        win32process/psutil to get the associated process ID and name.
        Returns None if no foreground window is found or on error.
        """
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None
                
            title = win32gui.GetWindowText(hwnd)
            
            # Get process ID
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid == 0: # Sometimes fails for system processes
                 process_name = "Unknown"
            else:
                try:
                    process = psutil.Process(pid)
                    process_name = process.name()
                    # exe_path = process.exe() # Could be useful context too
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                     process_name = "Unknown/Access Denied"
                     
            return {"hwnd": hwnd, "title": title, "pid": pid, "process_name": process_name}
            
        except Exception as e:
            # Potential errors if window disappears during query, or permissions
            logger.error(f"Error getting active window info: {e}", exc_info=False) # Avoid spamming logs
            return None

    def _match_context(self, active_window_info: Optional[Dict[str, Any]]) -> Optional[str]:
        """Matches the current context (active window) against configured rules.

        Returns:
            Optional[str]: The name of the profile to apply, or None if no match.
        """
        if not active_window_info or not self.contexts:
            # No window info or no rules configured
            return None

        current_title = active_window_info.get("title", "")
        # current_process = active_window_info.get("process_name", "")

        for context_rule in self.contexts:
            rule_type = context_rule.get("type")
            pattern_str = context_rule.get("pattern")
            profile_name = context_rule.get("profile")

            if not all([rule_type, pattern_str, profile_name]):
                logger.warning(f"Skipping invalid context rule: {context_rule}")
                continue

            if rule_type == "active_window_title":
                try:
                    # Perform a case-insensitive regex search
                    if re.search(pattern_str, current_title, re.IGNORECASE):
                        logger.debug(f"Matched window title '{current_title}' with pattern '{pattern_str}' -> profile '{profile_name}'")
                        return profile_name
                except re.error as e:
                     logger.error(f"Invalid regex pattern '{pattern_str}' in context rule: {e}")
            
            # Add other rule types here (e.g., process_name, system_idle)
            # elif rule_type == "process_name":
            #     if re.search(pattern_str, current_process, re.IGNORECASE):
            #          logger.debug(f"Matched process '{current_process}'...")
            #          return profile_name
            else:
                 logger.warning(f"Unsupported context rule type: {rule_type}")

        # No specific context matched
        return None

    def _monitor_loop(self):
        """The main loop that runs in a separate thread to monitor context."""
        logger.info("MCP monitor thread started.")
        while not self._stop_event.is_set():
            # Get the current foreground window info
            active_info = self._get_active_window_info()
            
            # Optimize: Only proceed if the active window title has changed since last check
            if active_info and active_info["title"] == self.last_active_window_title:
                 # No change in active window, sleep and continue
                 time.sleep(self.monitor_interval)
                 continue
                 
            self.last_active_window_title = active_info["title"] if active_info else None
            logger.debug(f"Active window changed: {self.last_active_window_title}")
            
            # Match the current context against configured rules
            matched_profile = self._match_context(active_info)
            # Determine the target profile: the matched one, or the default if no match
            target_profile = matched_profile or self.default_profile

            # Only apply if the target profile is different from the currently active one
            if target_profile != self.current_profile:
                if target_profile:
                    logger.info(f"Context change detected. Applying profile: '{target_profile}'")
                    # Use the SoundManager to apply the profile
                    success = self.sound_manager.load_sound_profile(target_profile)
                    if success:
                        self.current_profile = target_profile
                        logger.info(f"Successfully applied profile: '{target_profile}'")
                    else:
                         logger.error(f"Failed to apply profile '{target_profile}'. Check SoundManager logs.")
                         # Should we retry? Revert to default? For now, just log.
                         # We keep self.current_profile as is, indicating the desired state wasn't reached.
                else:
                    # No specific match and no default profile defined.
                    # We don't change the current profile in this case.
                    logger.info("No specific context matched and no default profile set. No profile applied.")
                    # Explicitly set current_profile to None if we were previously on a specific one?
                    # self.current_profile = None 
                    pass # Do nothing
            else:
                 logger.debug(f"Target profile ('{target_profile}') already active. No change needed.")
                 
            # Wait for the next interval
            self._stop_event.wait(self.monitor_interval)
            
        logger.info("MCP monitor thread stopped.")

    def start_monitoring(self):
        """Starts the context monitoring thread."""
        if not self.mcp_config:
            logger.warning("MCP configuration not found or empty. Monitoring disabled.")
            return
            
        if self._monitor_thread and self._monitor_thread.is_alive():
            logger.warning("MCP monitoring thread is already running.")
            return

        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self):
        """Stops the context monitoring thread."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            logger.info("Stopping MCP monitor thread...")
            self._stop_event.set()
            self._monitor_thread.join(timeout=self.monitor_interval + 2) # Wait for thread to finish
            if self._monitor_thread.is_alive():
                 logger.warning("MCP monitor thread did not stop gracefully.")
            self._monitor_thread = None
        else:
            logger.info("MCP monitor thread is not running.")

    # --- Potentially add methods to dynamically add/remove context rules ---
    # def add_context_rule(...)
    # def remove_context_rule(...)

# Example Usage (Can be integrated into CLI or run standalone)
# if __name__ == '__main__':
#     from logging_config import setup_logging
#     setup_logging()

#     try:
#         manager = SoundManager()
#         mcp_handler = MCPHandler(manager)
        
#         print("Starting MCP monitoring. Switch between apps (e.g., Notepad, VSCode) to test.")
#         print("Press Ctrl+C to stop.")
#         mcp_handler.start_monitoring()
        
#         try:
#             while True:
#                 time.sleep(1) # Keep main thread alive
#         except KeyboardInterrupt:
#             print("\nCtrl+C received. Stopping monitoring...")
#             mcp_handler.stop_monitoring()
#             print("Monitoring stopped.")
            
#     except ImportError as e:
#          print(f"Error: {e}")
#     except Exception as e:
#         logger.critical(f"MCP Handler failed to run: {e}", exc_info=True)
#         print(f"An error occurred: {e}") 