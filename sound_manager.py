import logging
from typing import Dict, Optional, List, Tuple

# Import functions from our modules
from registry_handler import list_sound_events, get_sound_file_path, set_sound_file_path
from sound_operations import play_system_sound, play_wav_file
from profile_manager import save_profile, load_profile, apply_profile, list_profiles, delete_profile
# REMOVED: from mcp_handler import MCPHandler # Keep MCP import if CLI uses it directly
# Import new audio control functions
from audio_control import (
    get_master_volume, set_master_volume,
    get_master_mute_status, set_master_mute,
    list_audio_devices, set_default_audio_device
)

logger = logging.getLogger(__name__)

class SoundManager:
    """Provides a high-level interface for managing Windows system sounds and profiles."""

    def __init__(self):
        """Initializes the SoundManager."""
        logger.info("SoundManager initialized.")
        # Potential future state initialization (e.g., loading config)
        pass

    # --- Core Sound Operations --- 

    def list_system_sounds(self) -> Dict[str, Dict[str, Optional[str]]]:
        """Lists all currently configured system sounds (from HKCU)."""
        logger.debug("Listing system sounds via SoundManager.")
        # Currently hardcoded to HKCU as that's what we primarily modify
        return list_sound_events("HKCU")

    def get_sound_for_event(self, event_category: str, sub_event: str = ".Current") -> Optional[str]:
        """Gets the WAV file path associated with a specific sound event."""
        logger.debug(f"Getting sound file for event: {event_category}\\{sub_event}")
        return get_sound_file_path(event_category, sub_event, "HKCU")

    def set_sound_for_event(self, event_category: str, sound_file_path: str, sub_event: str = ".Current") -> bool:
        """Sets the WAV file path for a specific sound event.

        Args:
            event_category (str): The main event category (e.g., 'SystemAsterisk').
            sound_file_path (str): The full path to the .wav file. Use an empty string to disable.
            sub_event (str): The specific sub-event (e.g., '.Current').

        Returns:
            bool: True if successful, False otherwise.
        """
        logger.debug(f"Setting sound file for event '{event_category}\\{sub_event}' to '{sound_file_path}'")
        return set_sound_file_path(event_category, sound_file_path, sub_event)

    def play_sound_for_event(self, event_category: str, sub_event: str = ".Current", async_play: bool = True) -> bool:
        """Plays the sound currently associated with a system event."""
        logger.debug(f"Playing sound for event: {event_category}\\{sub_event}")
        return play_system_sound(event_category, sub_event, async_play)

    def play_sound_file(self, file_path: str, async_play: bool = True) -> bool:
        """Plays a specific WAV file directly."""
        logger.debug(f"Playing specific WAV file: {file_path}")
        return play_wav_file(file_path, async_play)

    # --- Profile Management --- 

    def save_current_profile(self, profile_name: str) -> bool:
        """Saves the current sound settings as a named profile."""
        logger.debug(f"Saving current settings to profile: {profile_name}")
        return save_profile(profile_name)

    def load_sound_profile(self, profile_name: str) -> bool:
        """Loads and applies a sound profile to the system."""
        logger.debug(f"Loading and applying profile: {profile_name}")
        # apply_profile already handles loading internally
        return apply_profile(profile_name)

    def get_available_profiles(self) -> List[str]:
        """Returns a list of names of saved sound profiles."""
        logger.debug("Listing available profiles.")
        return list_profiles()

    def remove_profile(self, profile_name: str) -> bool:
        """Deletes a saved sound profile."""
        logger.debug(f"Deleting profile: {profile_name}")
        return delete_profile(profile_name)

    # --- Audio Control --- 
    
    def get_volume(self) -> Optional[float]:
        """Gets the master system volume (0.0 to 1.0)."""
        logger.debug("Getting master volume.")
        return get_master_volume()
            
    def set_volume(self, level: float) -> bool:
        """Sets the master system volume (0.0 to 1.0)."""
        logger.debug(f"Setting master volume to {level}")
        return set_master_volume(level)

    def get_mute(self) -> Optional[bool]:
        """Gets the master system mute status."""
        logger.debug("Getting master mute status.")
        return get_master_mute_status()
            
    def set_mute(self, mute: bool) -> bool:
        """Sets the master system mute status."""
        logger.debug(f"Setting master mute to {mute}")
        return set_master_mute(mute)

    def get_audio_devices(self, device_type: str = 'output') -> List[Tuple[str, str]]:
        """Lists available audio devices.
        
        Args:
            device_type (str): 'output' or 'input'.
            
        Returns:
            List[Tuple[str, str]]: List of (name, id) tuples.
        """
        logger.debug(f"Listing {device_type} audio devices.")
        return list_audio_devices(device_type)
            
    def set_active_audio_device(self, device_id: str, device_type: str = 'output') -> bool:
        """Sets the default audio device (EXPERIMENTAL)."""
        logger.warning(f"Attempting to set default {device_type} device to {device_id} (unreliable operation).")
        return set_default_audio_device(device_id, device_type)

# Example Usage (for testing within this file, remove later)
# if __name__ == '__main__':
#     import sys
#     import time
#     # Add project root to sys.path if needed

#     from logging_config import setup_logging
#     setup_logging() # Initialize logging

#     manager = SoundManager()

#     print("\n--- Sound Manager Tests ---")

#     # List sounds
#     print("\nCurrent System Sounds (first 5 categories):")
#     sounds = manager.list_system_sounds()
#     count = 0
#     for category, sub_events in sounds.items():
#         print(f"  Category: {category}")
#         # for sub, path in sub_events.items():
#         #     print(f"    {sub}: {path}")
#         count += 1
#         if count >= 5: 
#             print("  ...")
#             break
            
#     # Play a sound event
#     event_to_play = "SystemNotification"
#     print(f"\nPlaying '{event_to_play}' event sound (sync)...")
#     manager.play_sound_for_event(event_to_play, async_play=False)
#     print("Done playing.")

#     # Profile Operations
#     test_profile = "SoundManager Test Backup"
#     print(f"\nSaving current sounds to profile: '{test_profile}'")
#     manager.save_current_profile(test_profile)

#     print("\nAvailable profiles:", manager.get_available_profiles())

#     # Example: Temporarily disable a sound (use with caution!)
#     # print(f"\nAttempting to disable '{event_to_play}' sound...")
#     # original_path = manager.get_sound_for_event(event_to_play)
#     # if manager.set_sound_for_event(event_to_play, ""):
#     #     print(f"Disabled sound for '{event_to_play}'. Try triggering the event.")
#     #     input("Press Enter to try restoring...")
#     #     if manager.load_sound_profile(test_profile):
#     #         print(f"Restored profile '{test_profile}'. Sound should be back.")
#     #     else:
#     #         print(f"Failed to restore profile '{test_profile}'. You may need to restore manually or set path to: {original_path}")
#     # else:
#     #     print(f"Failed to disable sound for '{event_to_play}'.")

#     print(f"\nAttempting to reload profile '{test_profile}' (shouldn't change much if no manual changes were made)")
#     if manager.load_sound_profile(test_profile):
#         print(f"Reloaded profile '{test_profile}'")
#     else:
#          print(f"Failed to reload profile '{test_profile}'")

#     print(f"\nDeleting test profile: '{test_profile}'")
#     manager.remove_profile(test_profile)
#     print("Remaining profiles:", manager.get_available_profiles())

#     print("\nSound Manager tests complete.") 