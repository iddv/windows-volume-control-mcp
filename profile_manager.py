import os
import json
import logging
import re
from typing import Dict, Optional, List

# Assuming registry_handler is in the same directory or accessible via PYTHONPATH
from registry_handler import list_sound_events, set_sound_file_path

logger = logging.getLogger(__name__)

PROFILE_DIR = "profiles"
PROFILE_EXT = ".json"

# Ensure the profile directory exists
if not os.path.exists(PROFILE_DIR):
    try:
        os.makedirs(PROFILE_DIR)
        logger.info(f"Created profile directory: {PROFILE_DIR}")
    except OSError as e:
        logger.error(f"Failed to create profile directory '{PROFILE_DIR}': {e}", exc_info=True)
        # Decide how to handle this - maybe raise an exception?
        # For now, functions will likely fail if the dir doesn't exist.

def _is_valid_profile_name(name: str) -> bool:
    """Checks if a profile name is valid (filesystem-safe)."""
    if not name: 
        return False
    # Basic check: avoid empty names, hidden files, and common problematic chars
    # Allow letters, numbers, spaces, underscores, hyphens.
    # Disallow path separators, control characters, etc.
    if re.match(r"^[a-zA-Z0-9_\- ]+$", name) and not name.startswith('.'):
        return True
    logger.warning(f"Invalid profile name: '{name}'. Use letters, numbers, spaces, underscores, hyphens.")
    return False

def _get_profile_path(profile_name: str) -> Optional[str]:
    """Returns the full path for a profile name, validating the name first."""
    if not _is_valid_profile_name(profile_name):
        return None
    return os.path.join(PROFILE_DIR, f"{profile_name}{PROFILE_EXT}")

def save_profile(profile_name: str) -> bool:
    """Saves the current system sound configuration (HKCU) to a named profile.

    Args:
        profile_name (str): The name for the profile (filesystem-safe).

    Returns:
        bool: True if the profile was saved successfully, False otherwise.
    """
    profile_path = _get_profile_path(profile_name)
    if not profile_path:
        return False # Invalid name

    logger.info(f"Saving current sound settings to profile: '{profile_name}'")
    try:
        # Get current sounds from the user's registry hive
        current_sounds = list_sound_events("HKCU")
        
        # Structure for the profile file
        profile_data = {
            "name": profile_name,
            "sounds": current_sounds
            # Could add metadata later, like creation date
        }

        with open(profile_path, 'w') as f:
            json.dump(profile_data, f, indent=4)
        
        logger.info(f"Profile '{profile_name}' saved successfully to {profile_path}")
        return True
    except IOError as e:
        logger.error(f"Failed to write profile file {profile_path}: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred while saving profile '{profile_name}': {e}", exc_info=True)
    
    return False

def load_profile(profile_name: str) -> Optional[Dict]:
    """Loads a sound profile from a file.

    Args:
        profile_name (str): The name of the profile to load.

    Returns:
        Optional[Dict]: The loaded profile data as a dictionary, or None if loading fails.
    """
    profile_path = _get_profile_path(profile_name)
    if not profile_path or not os.path.exists(profile_path):
        logger.error(f"Profile '{profile_name}' not found at {profile_path}")
        return None

    logger.debug(f"Loading profile: '{profile_name}' from {profile_path}")
    try:
        with open(profile_path, 'r') as f:
            profile_data = json.load(f)
        # Basic validation (can be expanded)
        if isinstance(profile_data, dict) and "name" in profile_data and "sounds" in profile_data:
             if profile_data["name"] != profile_name:
                 logger.warning(f"Profile name in file ('{profile_data['name']}') does not match filename ('{profile_name}').")
             logger.info(f"Profile '{profile_name}' loaded successfully.")
             return profile_data
        else:
            logger.error(f"Invalid profile format in file: {profile_path}")
            return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from profile file {profile_path}: {e}", exc_info=True)
    except IOError as e:
        logger.error(f"Failed to read profile file {profile_path}: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading profile '{profile_name}': {e}", exc_info=True)
    
    return None

def apply_profile(profile_name: str) -> bool:
    """Loads a profile and applies its sound settings to the system (HKCU).

    Args:
        profile_name (str): The name of the profile to apply.

    Returns:
        bool: True if the profile was applied completely successfully, False otherwise.
              Note: This is best-effort; some sounds might fail to apply.
    """
    profile_data = load_profile(profile_name)
    if not profile_data:
        return False # Loading failed
        
    logger.info(f"Applying profile: '{profile_name}'")
    sounds_to_apply = profile_data.get("sounds", {})
    if not isinstance(sounds_to_apply, dict):
         logger.error("Invalid 'sounds' data in profile.")
         return False
         
    success_count = 0
    fail_count = 0
    total_sounds = 0

    # Iterate through categories (e.g., 'SystemAsterisk')
    for category, sub_events in sounds_to_apply.items():
        if not isinstance(sub_events, dict):
            logger.warning(f"Skipping invalid sub-event data for category '{category}' in profile '{profile_name}'.")
            continue
        # Iterate through sub-events (e.g., '.Current')
        for sub_event, sound_file_path in sub_events.items():
            total_sounds += 1
            # Registry handler expects empty string for no sound, JSON uses null/None
            path_to_set = sound_file_path if sound_file_path is not None else ""
            
            # Validate path type before passing to registry handler
            if not isinstance(path_to_set, str):
                logger.error(f"Invalid sound file path type ('{type(path_to_set)}') for '{category}\\{sub_event}' in profile '{profile_name}'. Expected string or null.")
                fail_count += 1
                continue
                
            # Use the registry handler to set the sound
            if set_sound_file_path(category, path_to_set, sub_event):
                success_count += 1
            else:
                fail_count += 1
                # Logged within set_sound_file_path

    logger.info(f"Profile '{profile_name}' application finished.")
    logger.info(f"Applied: {success_count}/{total_sounds}, Failed: {fail_count}/{total_sounds}")
    
    if fail_count > 0:
        logger.warning(f"Some sounds failed to apply for profile '{profile_name}'. Check logs for details.")
        return False # Indicate partial failure
    elif total_sounds == 0:
        logger.info(f"Profile '{profile_name}' contained no sounds to apply.")
        return True # Technically successful, though nothing happened
    else:
        logger.info(f"Profile '{profile_name}' applied successfully.")
        return True # All succeeded

def list_profiles() -> List[str]:
    """Lists the names of all available sound profiles.

    Returns:
        List[str]: A list of profile names.
    """
    profiles = []
    if not os.path.exists(PROFILE_DIR):
        logger.warning(f"Profile directory '{PROFILE_DIR}' does not exist.")
        return profiles
        
    try:
        for filename in os.listdir(PROFILE_DIR):
            if filename.lower().endswith(PROFILE_EXT):
                profile_name = filename[:-len(PROFILE_EXT)] # Remove extension
                # Optionally, could do a quick load test here to verify format
                profiles.append(profile_name)
        logger.debug(f"Found profiles: {profiles}")
    except OSError as e:
        logger.error(f"Failed to list profiles in directory '{PROFILE_DIR}': {e}", exc_info=True)
    return profiles

def delete_profile(profile_name: str) -> bool:
    """Deletes a sound profile file.

    Args:
        profile_name (str): The name of the profile to delete.

    Returns:
        bool: True if deletion was successful, False otherwise.
    """
    profile_path = _get_profile_path(profile_name)
    if not profile_path: 
        return False # Invalid name

    if not os.path.exists(profile_path):
        logger.error(f"Profile '{profile_name}' does not exist, cannot delete.")
        return False

    logger.warning(f"Attempting to delete profile: '{profile_name}' from {profile_path}")
    try:
        os.remove(profile_path)
        logger.info(f"Profile '{profile_name}' deleted successfully.")
        return True
    except OSError as e:
        logger.error(f"Failed to delete profile file {profile_path}: {e}", exc_info=True)
        return False

# Example Usage (for testing, remove later)
# if __name__ == '__main__':
#     import sys
#     # Add project root to sys.path if needed

#     from logging_config import setup_logging
#     setup_logging()

#     print("\n--- Profile Management Tests ---")
#     test_profile_name = "Test Profile - Backup"
#     default_profile_name = "Windows Default - Backup"

#     # 1. Save current settings (might be customized)
#     print(f"\nAttempting to save current settings as '{test_profile_name}'")
#     if save_profile(test_profile_name):
#         print(f"Saved profile '{test_profile_name}'")
#     else:
#         print(f"Failed to save profile '{test_profile_name}'")

#     # 2. List profiles
#     print("\nAvailable profiles:")
#     profiles = list_profiles()
#     if profiles:
#         for p in profiles:
#             print(f"- {p}")
#     else:
#         print("(No profiles found)")

#     # 3. Try to apply a known default profile (if it exists or we create one)
#     # For a real test, you might manually create a 'default.json' profile
#     # or save the current state first if it's the desired default.
#     print(f"\nAttempting to apply profile '{default_profile_name}' (if it exists)")
#     if default_profile_name in profiles:
#         if apply_profile(default_profile_name):
#             print(f"Applied profile '{default_profile_name}'")
#             print("Check system sounds to verify changes.")
#         else:
#             print(f"Failed to apply profile '{default_profile_name}'")
#     else:
#         print(f"Profile '{default_profile_name}' not found, skipping apply test.")
#         # You could save the current state as the default backup here:
#         # save_profile(default_profile_name)
    
#     input(f"Press Enter to attempt restoring '{test_profile_name}'...")

#     # 4. Apply the saved profile
#     print(f"\nAttempting to apply profile '{test_profile_name}'")
#     if apply_profile(test_profile_name):
#         print(f"Applied profile '{test_profile_name}'")
#         print("Check if sounds reverted to the saved state.")
#     else:
#         print(f"Failed to apply profile '{test_profile_name}'")

#     # 5. Delete the test profile
#     print(f"\nAttempting to delete profile '{test_profile_name}'")
#     if delete_profile(test_profile_name):
#         print(f"Deleted profile '{test_profile_name}'")
#         print("Remaining profiles:", list_profiles())
#     else:
#         print(f"Failed to delete profile '{test_profile_name}'") 