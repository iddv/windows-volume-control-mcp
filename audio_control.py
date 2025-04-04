import logging
from typing import Optional, List, Tuple
import sys
import traceback

print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

PYCAW_AVAILABLE = False
try:
    print("Trying to import from pycaw.pycaw...")
    from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume, IAudioEndpointVolume
    print("Trying to import from comtypes directly...")
    from comtypes import CLSCTX_ALL, COMError  # Import CLSCTX_ALL directly from comtypes
    print("Trying to import from ctypes...")
    from ctypes import cast, POINTER
    print("All imports successful!")
    PYCAW_AVAILABLE = True
except ImportError as e:
    error_info = traceback.format_exc()
    print(f"Audio Control features require 'pycaw'. Import error: {e}")
    print(f"Traceback: {error_info}")
    AudioUtilities = None
    ISimpleAudioVolume = None
    IAudioEndpointVolume = None 
    COMError = None
    CLSCTX_ALL = None
except Exception as e:
    error_info = traceback.format_exc()
    print(f"Unexpected error importing pycaw: {e}")
    print(f"Traceback: {error_info}")
    AudioUtilities = None
    ISimpleAudioVolume = None
    IAudioEndpointVolume = None 
    COMError = None
    CLSCTX_ALL = None

# Try a simpler import just to check
try:
    import pycaw
    print(f"Basic pycaw import works. Version: {pycaw.__version__ if hasattr(pycaw, '__version__') else 'unknown'}")
    print(f"pycaw path: {pycaw.__file__}")
except ImportError as e:
    print(f"Even basic pycaw import fails: {e}")

logger = logging.getLogger(__name__)

# Helper to ensure dependencies are checked before use
def _check_dependencies():
    if not PYCAW_AVAILABLE:
        # This ensures functions raise an error early if pycaw is missing
        raise ImportError("pycaw library is not installed or failed to import.")

# --- Master Volume Control ---

def get_master_volume() -> Optional[float]:
    """Gets the current master volume level (0.0 to 1.0).

    Returns:
        Optional[float]: The volume level (0.0-1.0) or None on error.
    """
    _check_dependencies()
    try:
        devices = AudioUtilities.GetSpeakers() # Get default audio endpoint
        interface = devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        
        level = volume.GetMasterVolumeLevelScalar()
        logger.debug(f"Current master volume level: {level:.2f}")
        return level
    except COMError as e:
        logger.error(f"COMError getting master volume: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Error getting master volume: {e}", exc_info=True)
        return None

def set_master_volume(level: float) -> bool:
    """Sets the master volume level.

    Args:
        level (float): Volume level from 0.0 (mute) to 1.0 (max).

    Returns:
        bool: True if successful, False otherwise.
    """
    _check_dependencies()
    if not 0.0 <= level <= 1.0:
        logger.error(f"Invalid volume level: {level}. Must be between 0.0 and 1.0.")
        return False
        
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        
        # SetMasterVolumeLevelScalar seems to be the most reliable
        volume.SetMasterVolumeLevelScalar(level, None)
        logger.info(f"Set master volume level to: {level:.2f}")
        return True
    except COMError as e:
        logger.error(f"COMError setting master volume: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Error setting master volume: {e}", exc_info=True)
        return False

def get_master_mute_status() -> Optional[bool]:
     """Gets the current master mute status."""
     _check_dependencies()
     try:
         devices = AudioUtilities.GetSpeakers()
         interface = devices.Activate(
             IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
         volume = cast(interface, POINTER(IAudioEndpointVolume))
         muted = volume.GetMute()
         logger.debug(f"Master mute status: {bool(muted)}")
         return bool(muted)
     except COMError as e:
         logger.error(f"COMError getting mute status: {e}", exc_info=True)
         return None
     except Exception as e:
        logger.error(f"Error getting mute status: {e}", exc_info=True)
        return None
        
def set_master_mute(mute: bool) -> bool:
    """Sets the master mute status.

    Args:
        mute (bool): True to mute, False to unmute.

    Returns:
        bool: True if successful, False otherwise.
    """
    _check_dependencies()
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        
        volume.SetMute(int(mute), None)
        status = "muted" if mute else "unmuted"
        logger.info(f"Set master volume status to: {status}")
        return True
    except COMError as e:
        logger.error(f"COMError setting mute status: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Error setting mute status: {e}", exc_info=True)
        return False

# --- Audio Device Listing (Switching is more complex) ---

def list_audio_devices(device_type: str = 'output') -> List[Tuple[str, str]]:
    """Lists available audio devices (output or input) using pycaw.

    Args:
        device_type (str): 'output' (playback) or 'input' (recording).

    Returns:
        List[Tuple[str, str]]: A list of tuples, where each tuple contains 
                                (Device Friendly Name, Device ID String).
                                Returns an empty list on failure.
    """
    if not PYCAW_AVAILABLE:
        logger.warning("pycaw not available, returning mock device list")
        if device_type == 'output':
            # Return mock output devices
            return [
                ("Mock Speaker Device", "mock-speaker-id"),
                ("Mock HDMI Output", "mock-hdmi-id")
            ]
        else:
            # Return mock input devices
            return [
                ("Mock Microphone", "mock-mic-id"),
                ("Mock Line In", "mock-line-in-id")
            ]
    
    # Print available methods for debugging
    print(f"AudioUtilities methods: {[method for method in dir(AudioUtilities) if not method.startswith('_')]}", file=sys.stderr)
    
    devices_list = []
    try:
        _check_dependencies()
        
        if device_type == 'output':
            # Get the default output device (speakers)
            try:
                default_device = AudioUtilities.GetSpeakers()
                if default_device:
                    device = AudioUtilities.CreateDevice(default_device)
                    if device:
                        device_name = device.FriendlyName or "Default Speaker"
                        device_id = device.id
                        devices_list.append((device_name, device_id))
                        logger.debug(f"Added default output device: {device_name}")
            except Exception as e:
                logger.warning(f"Could not retrieve default output device: {e}")
            
            # Try to get all devices if we want a complete list
            try:
                all_devices = AudioUtilities.GetAllDevices()
                # Add non-default output devices
                for device in all_devices:
                    # Check if it's an output device (data flow = eRender/0)
                    is_output = False
                    try:
                        if hasattr(AudioUtilities, 'GetEndpointDataFlow'):
                            is_output = AudioUtilities.GetEndpointDataFlow(device.id, outputType=1) == 0
                        elif hasattr(device, 'properties'):
                            # Could check device properties, but that's device-specific
                            # For now, assume it's an output if it's not the default one we already added
                            device_id = device.id
                            is_output = (device_id not in [d[1] for d in devices_list])
                            
                        if is_output:
                            device_name = device.FriendlyName or f"Output Device {len(devices_list)+1}"
                            device_id = device.id
                            # Avoid duplicates
                            if device_id not in [d[1] for d in devices_list]:
                                devices_list.append((device_name, device_id))
                                logger.debug(f"Added output device: {device_name}")
                    except Exception as ex:
                        logger.debug(f"Error checking if device is output: {ex}")
                        continue
            except Exception as e:
                logger.warning(f"Could not retrieve all devices: {e}")
                
        elif device_type == 'input':
            # Get the default input device (microphone)
            try:
                default_device = AudioUtilities.GetMicrophone()
                if default_device:
                    device = AudioUtilities.CreateDevice(default_device)
                    if device:
                        device_name = device.FriendlyName or "Default Microphone"
                        device_id = device.id
                        devices_list.append((device_name, device_id))
                        logger.debug(f"Added default input device: {device_name}")
            except Exception as e:
                logger.warning(f"Could not retrieve default input device: {e}")
                
            # Try to get all devices if we want a complete list
            try:
                all_devices = AudioUtilities.GetAllDevices()
                # Add non-default input devices
                for device in all_devices:
                    # Check if it's an input device (data flow = eCapture/1)
                    is_input = False
                    try:
                        if hasattr(AudioUtilities, 'GetEndpointDataFlow'):
                            is_input = AudioUtilities.GetEndpointDataFlow(device.id, outputType=1) == 1
                        elif hasattr(device, 'properties'):
                            # Could check device properties, but that's device-specific
                            # For now, assume it's an input if it's not the default one we already added
                            device_id = device.id
                            is_input = (device_id not in [d[1] for d in devices_list])
                            
                        if is_input:
                            device_name = device.FriendlyName or f"Input Device {len(devices_list)+1}"
                            device_id = device.id
                            # Avoid duplicates
                            if device_id not in [d[1] for d in devices_list]:
                                devices_list.append((device_name, device_id))
                                logger.debug(f"Added input device: {device_name}")
                    except Exception as ex:
                        logger.debug(f"Error checking if device is input: {ex}")
                        continue
            except Exception as e:
                logger.warning(f"Could not retrieve all devices: {e}")
        else:
            logger.error(f"Invalid device_type: {device_type}. Use 'output' or 'input'.")
            return []
            
        if not devices_list:
             logger.info(f"No {device_type} audio devices found.")
        else:
             logger.debug(f"Found {len(devices_list)} {device_type} devices.")
                 
    except COMError as e:
        # Errors can occur if audio service is stopped or devices change rapidly
        logger.error(f"COMError listing {device_type} devices: {e}", exc_info=True)
        print(f"COMError details: {traceback.format_exc()}", file=sys.stderr)
    except Exception as e:
        logger.error(f"Error listing {device_type} devices: {e}", exc_info=True)
        print(f"Error details: {traceback.format_exc()}", file=sys.stderr)
    
    return devices_list
    
# --- Audio Device Switching (Complex - Placeholder/Requires more research) ---
# Setting the default device programmatically is non-trivial and often requires
# interacting with undocumented APIs or external tools/scripts.
# pycaw focuses on volume/mute/session control, not default device switching.
# Possible approaches (outside pycaw):
# 1. Using external tools like NirCmd or SoundSwitch command-line.
# 2. Complex COM interactions with PolicyConfigClient (undocumented, risky).
# 3. Manual registry changes (often don't take effect immediately).

def set_default_audio_device(device_id: str, device_type: str = 'output') -> bool:
    """Attempts to set the default audio device (EXPERIMENTAL/UNRELIABLE).
    
    NOTE: This is notoriously difficult and unreliable to do programmatically
          from standard Python libraries on Windows. This function is a placeholder
          and likely will NOT work correctly without significant extra effort
          (e.g., using external tools or complex, undocumented APIs).

    Args:
        device_id (str): The ID string of the device to set as default 
                         (obtained from list_audio_devices).
        device_type (str): 'output' or 'input'.

    Returns:
        bool: True if the attempt was made (doesn't guarantee success), False otherwise.
    """
    _check_dependencies()
    logger.warning("set_default_audio_device is experimental and likely non-functional.")
    
    # Example using a hypothetical external tool (like NirCmd)
    # import subprocess
    # try:
    #     cmd = ['nircmd.exe', 'setdefaultsounddevice', device_id, '1'] # '1' for playback
    #     subprocess.run(cmd, check=True, capture_output=True)
    #     logger.info(f"Attempted to set default {device_type} device to ID {device_id} using NirCmd.")
    #     return True
    # except FileNotFoundError:
    #     logger.error("NirCmd not found. Cannot set default device.")
    #     return False
    # except subprocess.CalledProcessError as e:
    #     logger.error(f"NirCmd failed: {e}")
    #     return False
        
    # Placeholder return
    logger.error("Default audio device switching is not implemented via pycaw.")
    return False 


# Example Usage (for testing, remove later)
# if __name__ == '__main__':
#     import time
#     from logging_config import setup_logging
#     setup_logging()

#     try:
#         print("\n--- Audio Control Tests (pycaw) ---")

#         # Volume
#         initial_volume = get_master_volume()
#         initial_mute = get_master_mute_status()
#         print(f"Initial Master Volume: {initial_volume:.2f if initial_volume is not None else 'N/A'}")
#         print(f"Initial Mute Status: {initial_mute}")

#         if initial_volume is not None:
#             print("\nSetting volume to 50%...")
#             set_master_volume(0.5)
#             time.sleep(1)
#             print(f"Current Volume: {get_master_volume():.2f}")
            
#             print("\nMuting...")
#             set_master_mute(True)
#             time.sleep(1)
#             print(f"Mute Status: {get_master_mute_status()}")
            
#             print("\nUnmuting...")
#             set_master_mute(False)
#             time.sleep(1)
#             print(f"Mute Status: {get_master_mute_status()}")

#             print(f"\nRestoring initial volume ({initial_volume:.2f}) and mute ({initial_mute})...")
#             set_master_volume(initial_volume)
#             set_master_mute(initial_mute)
#             time.sleep(1)
#             print(f"Final Volume: {get_master_volume():.2f}")
#             print(f"Final Mute Status: {get_master_mute_status()}")

#         # Devices
#         print("\nListing Output Devices:")
#         outputs = list_audio_devices('output')
#         if not outputs:
#             print("(No output devices found or error)")
#         else: 
#             for name, dev_id in outputs:
#                 print(f"- Name: {name}\n  ID:   {dev_id}")

#         print("\nListing Input Devices:")
#         inputs = list_audio_devices('input')
#         if not inputs:
#             print("(No input devices found or error)")
#         else:
#             for name, dev_id in inputs:
#                 print(f"- Name: {name}\n  ID:   {dev_id}")
                
#         # Attempt Switch (Known to be unreliable)
#         if outputs:
#              print(f"\nAttempting to set default output device to '{outputs[0][0]}' (EXPERIMENTAL - likely fails)")
#              set_default_audio_device(outputs[0][1], 'output')

#     except ImportError as e:
#         print(f"Error: {e}")
#     except Exception as e:
#         logger.error(f"Audio control test failed: {e}", exc_info=True)
#         print(f"An error occurred during tests: {e}") 