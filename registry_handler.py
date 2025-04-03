import winreg
import logging
import os
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

# Registry path for default sound scheme events
# This is typically where user-customized sounds are stored.
SOUNDS_REG_PATH = r"AppEvents\Schemes\Apps\.Default"

# Possible base keys - we'll primarily use HKEY_CURRENT_USER
# HKEY_LOCAL_MACHINE might contain default system sounds before user customization.
REG_BASE_KEYS = {
    "HKCU": winreg.HKEY_CURRENT_USER,
    "HKLM": winreg.HKEY_LOCAL_MACHINE,
}

def _get_full_sound_event_path(event_name: str) -> str:
    """Constructs the full registry path for a specific sound event."""
    # Example event_name: SystemAsterisk\.Current
    return f"{SOUNDS_REG_PATH}\\{event_name}"

def list_sound_events(base_key: str = "HKCU") -> Dict[str, Dict[str, Optional[str]]]:
    """Lists all sound events and their associated sound file paths from the registry.

    Args:
        base_key (str): The base registry key to query ('HKCU' or 'HKLM').

    Returns:
        Dict[str, Dict[str, Optional[str]]]: A dictionary where keys are event category names
                                           (e.g., 'SystemAsterisk') and values are dictionaries
                                           mapping sub-event names (e.g., '.Current') to
                                           sound file paths (or None if not set).
    """
    events = {}
    try:
        hkey_base = REG_BASE_KEYS[base_key]
        with winreg.OpenKey(hkey_base, SOUNDS_REG_PATH, 0, winreg.KEY_READ) as hkey_apps:
            index = 0
            while True:
                try:
                    event_category_name = winreg.EnumKey(hkey_apps, index)
                    event_category_path = f"{SOUNDS_REG_PATH}\\{event_category_name}"
                    events[event_category_name] = {}
                    with winreg.OpenKey(hkey_base, event_category_path, 0, winreg.KEY_READ) as hkey_category:
                        sub_index = 0
                        while True:
                            try:
                                sub_event_name = winreg.EnumKey(hkey_category, sub_index)
                                sub_event_path = f"{event_category_path}\\{sub_event_name}"
                                sound_file = get_sound_file_path(event_category_name, sub_event_name, base_key)
                                events[event_category_name][sub_event_name] = sound_file
                                sub_index += 1
                            except OSError:
                                # No more sub-keys (sub-events)
                                break 
                    index += 1
                except OSError:
                    # No more keys (event categories)
                    break
    except FileNotFoundError:
        logger.error(f"Registry path not found: {base_key}\\{SOUNDS_REG_PATH}")
    except PermissionError:
        logger.error(f"Permission denied accessing registry key: {base_key}\\{SOUNDS_REG_PATH}")
    except Exception as e:
        logger.error(f"Error listing sound events from registry: {e}", exc_info=True)
    return events

def get_sound_file_path(event_category: str, sub_event: str = ".Current", base_key: str = "HKCU") -> Optional[str]:
    """Gets the sound file path for a specific sound event from the registry.

    Args:
        event_category (str): The main event category (e.g., 'SystemAsterisk').
        sub_event (str): The specific sub-event (e.g., '.Current'). Defaults to '.Current'.
        base_key (str): The base registry key ('HKCU' or 'HKLM').

    Returns:
        Optional[str]: The full path to the sound file, or None if not found or not set.
    """
    full_path = f"{SOUNDS_REG_PATH}\\{event_category}\\{sub_event}"
    try:
        hkey_base = REG_BASE_KEYS[base_key]
        with winreg.OpenKey(hkey_base, full_path, 0, winreg.KEY_READ) as hkey_event:
            # The sound file path is typically stored in the default value of the key.
            # It might also be in a named value like 'sound' or similar, but default is common.
            value, reg_type = winreg.QueryValueEx(hkey_event, None) # Read default value
            if reg_type == winreg.REG_SZ or reg_type == winreg.REG_EXPAND_SZ:
                # Expand environment variables like %SystemRoot%
                return os.path.expandvars(value) if value else None
            else:
                logger.warning(f"Unexpected registry value type ({reg_type}) for {full_path}")
                return None
    except FileNotFoundError:
        # Key or default value might not exist, which is normal for unset sounds
        logger.debug(f"Registry key or default value not found for {base_key}\\{full_path}")
        return None
    except PermissionError:
        logger.error(f"Permission denied accessing registry key: {base_key}\\{full_path}")
        return None
    except Exception as e:
        logger.error(f"Error getting sound file path from registry for {full_path}: {e}", exc_info=True)
        return None

def set_sound_file_path(event_category: str, sound_file_path: str, sub_event: str = ".Current") -> bool:
    """Sets the sound file path for a specific sound event in the HKCU registry.

    Args:
        event_category (str): The main event category (e.g., 'SystemAsterisk').
        sound_file_path (str): The full path to the .wav file. Use an empty string to disable the sound.
        sub_event (str): The specific sub-event (e.g., '.Current'). Defaults to '.Current'.

    Returns:
        bool: True if successful, False otherwise.
    """
    if not os.path.exists(sound_file_path) and sound_file_path != "":
        logger.error(f"Sound file not found: {sound_file_path}. Cannot set registry.")
        # Optionally raise an error instead?
        # raise FileNotFoundError(f"Sound file not found: {sound_file_path}")
        return False
        
    if sound_file_path and not sound_file_path.lower().endswith('.wav'):
         logger.warning(f"Sound file does not end with .wav: {sound_file_path}. Windows might not play it.")
         # Allow setting anyway, but warn user.

    full_path = f"{SOUNDS_REG_PATH}\\{event_category}\\{sub_event}"
    try:
        # Ensure the key exists, creating it if necessary.
        # We only modify HKCU as changing HKLM requires higher privileges and affects all users.
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, full_path, 0, winreg.KEY_WRITE) as hkey_event:
            # Set the default value of the key to the sound file path.
            # Using REG_EXPAND_SZ allows using environment variables like %SystemRoot%.
            winreg.SetValueEx(hkey_event, None, 0, winreg.REG_EXPAND_SZ, sound_file_path)
            logger.info(f"Set sound for '{event_category}\\{sub_event}' to '{sound_file_path or '(None)'}'")
            # Notify Windows about the change (important for immediate effect)
            _broadcast_settings_change()
            return True
    except PermissionError:
        logger.error(f"Permission denied modifying registry key: HKCU\\{full_path}. Try running as administrator.")
        return False
    except Exception as e:
        logger.error(f"Error setting sound file path in registry for {full_path}: {e}", exc_info=True)
        return False

def _broadcast_settings_change():
    """Notifies Windows that system settings (including sounds) have changed."""
    try:
        import ctypes
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        # Using SPI_SETCURSORS or similar flags is a common practice to signal
        # a general settings change when a specific SPI flag for the exact setting
        # (like sounds) isn't available or reliable across Windows versions.
        SPI_SETCURSORS = 0x0057 # Often used, might need SPI_SETSOUNDS if available
        SMTO_ABORTIFHUNG = 0x0002

        # Using SendMessageTimeout with HWND_BROADCAST
        result = ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST,
            WM_SETTINGCHANGE,
            SPI_SETCURSORS, # Parameter indicating what changed (sounds specifically is tricky)
            "Window", # String indicating change area, can be "Sounds"
            SMTO_ABORTIFHUNG,
            5000, # Timeout in milliseconds
            None
        )
        if result == 0:
            # Getting the last error might provide more info if SendMessageTimeout fails
            error_code = ctypes.get_last_error()
            logger.warning(f"SendMessageTimeout failed to broadcast settings change. Error code: {error_code}")
        else:
            logger.debug("Successfully broadcasted WM_SETTINGCHANGE.")
            
        # Alternative / Additional method: SystemParametersInfo
        # SPI_SETSOUNDS = 1028 # This constant might not be defined everywhere or work reliably
        # try:
        #     SPI_SETDESKWALLPAPER = 20 # Example: changing wallpaper broadcasts widely
        #     ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, None, 3) # Force refresh
        #     logger.debug("Used SystemParametersInfoW as an alternative broadcast.")
        # except AttributeError:
        #      logger.warning("SPI_SETSOUNDS not found or SystemParametersInfoW failed.")
            
    except ImportError:
        logger.warning("ctypes module not available. Cannot broadcast settings change.")
    except Exception as e:
        logger.error(f"Error broadcasting settings change: {e}", exc_info=True)

# Example Usage (for testing, remove later)
# if __name__ == '__main__':
#     import sys
#     # Basic logging setup for testing
#     logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

#     print("Listing current user sound events:")
#     hkcu_events = list_sound_events("HKCU")
#     # for category, sub_events in hkcu_events.items():
#     #     print(f"  Category: {category}")
#     #     for sub_event, path in sub_events.items():
#     #         print(f"    {sub_event}: {path}")

#     test_event = "SystemNotification" # Choose a safe event to test
#     original_path = get_sound_file_path(test_event)
#     print(f"\nOriginal path for {test_event}: {original_path}")

#     test_sound_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Media', 'Windows Notify System Generic.wav')
#     print(f"Attempting to set {test_event} to: {test_sound_path}")
    
#     if not os.path.exists(test_sound_path):
#         print(f"Test sound file not found: {test_sound_path}, skipping set test.")
#     else:
#         if set_sound_file_path(test_event, test_sound_path):
#             print("Successfully set sound path.")
#             new_path = get_sound_file_path(test_event)
#             print(f"New path for {test_event}: {new_path}")
#             # Important: Wait a moment for the system to potentially react
#             input("Press Enter to restore original path...") 
#             if set_sound_file_path(test_event, original_path or ""):
#                 print("Successfully restored original path.")
#             else:
#                 print("Failed to restore original path.")
#         else:
#             print(f"Failed to set sound path for {test_event}. Check permissions or logs.") 