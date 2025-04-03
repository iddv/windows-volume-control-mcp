"""
Example demonstrating profile-based management for different scenarios.

This script shows how to:
1. Define hypothetical sound configurations for different scenarios (e.g., Work, Gaming).
2. Create sound profiles based on these configurations if they don't exist.
3. Manually load different profiles to switch the system sound scheme.
4. Clean up the created profiles.
"""

import sys
import os
import logging
import time

# Adjust the path to import from the root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from sound_manager import SoundManager
    from logging_config import setup_logging
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Ensure the script is run from the project root or the root is in the Python path.")
    sys.exit(1)

# --- Configuration ---

# Define profile names
PROFILE_WORK = "Scenario - Work"
PROFILE_GAMING = "Scenario - Gaming"
PROFILE_DEFAULT_BACKUP = "Scenario - Default Backup"

# Define sounds for each profile (using common event names)
# Use empty string "" to disable a sound.
# Ensure WAV paths are valid on your system or use standard ones.
WORK_SOUNDS = {
    "SystemNotification": "", # Silent notifications for work
    "SystemAsterisk": "C:\\Windows\\Media\\Windows Background.wav", 
    "CalendarReminder": "C:\\Windows\\Media\\Windows Notify Calendar.wav"
}

GAMING_SOUNDS = {
    "SystemNotification": "C:\\Windows\\Media\\Windows Notify Messaging.wav", # Louder/different notification
    "SystemAsterisk": "C:\\Windows\\Media\\chord.wav",
    "LowBatteryAlarm": "C:\\Windows\\Media\\Windows Alarm 01.wav" # Ensure battery alerts are audible
}

# Sound event to test after loading a profile
TEST_EVENT = "SystemNotification"

# --- Initialization ---
setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)
manager = SoundManager()

def create_profile_if_not_exists(profile_name: str, sound_settings: dict):
    """Sets specific sounds and saves them as a profile if it doesn't exist."""
    if profile_name in manager.get_available_profiles():
        logger.info(f"Profile '{profile_name}' already exists. Skipping creation.")
        return True
        
    logger.info(f"Profile '{profile_name}' not found. Creating it...")
    logger.info("Saving current state first as a baseline for the new profile...")
    # Save current state to start modifying from a full set
    if not manager.save_current_profile(profile_name):
        logger.error(f"Failed to save initial baseline for '{profile_name}'. Cannot create profile.")
        return False
        
    logger.info(f"Applying specific sounds for '{profile_name}':")
    success_count = 0
    fail_count = 0
    for event, sound_file in sound_settings.items():
        # Check if the sound file exists unless disabling the sound
        if sound_file and not os.path.exists(sound_file):
            logger.warning(f"  - Sound file not found: '{sound_file}' for event '{event}'. Skipping.")
            fail_count += 1
            continue
            
        logger.info(f"  - Setting '{event}' to '{"Disabled" if not sound_file else sound_file}'")
        if manager.set_sound_for_event(event, sound_file):
            success_count += 1
        else:
            logger.error(f"  - Failed to set sound for '{event}'. Check permissions or logs.")
            fail_count += 1
            
    if fail_count > 0:
        logger.warning(f"Finished applying sounds for '{profile_name}' with {fail_count} errors.")
    else:
        logger.info(f"Successfully applied {success_count} specific sound(s) for '{profile_name}'.")

    # Save the modified settings back to the profile
    logger.info(f"Re-saving profile '{profile_name}' with custom sounds...")
    if manager.save_current_profile(profile_name):
        logger.info(f"Profile '{profile_name}' created and saved successfully.")
        return True
    else:
        logger.error(f"Failed to save modified profile '{profile_name}'. It might be incomplete.")
        # Optionally delete the potentially corrupt profile here?
        # manager.remove_profile(profile_name)
        return False

def run_profile_switching_example():
    """Runs the profile switching demonstration."""
    logger.info("--- Starting Profile Switching Example ---")
    profiles_to_cleanup = []

    try:
        # 1. Backup Current Settings
        logger.info(f"\n1. Backing up current sound settings to '{PROFILE_DEFAULT_BACKUP}'")
        if manager.save_current_profile(PROFILE_DEFAULT_BACKUP):
            logger.info("Backup successful.")
            profiles_to_cleanup.append(PROFILE_DEFAULT_BACKUP)
        else:
            logger.error("Failed to back up current settings. Aborting example.")
            return

        # 2. Create Scenario Profiles (if they don't exist)
        logger.info("\n2. Creating scenario profiles if they don't exist...")
        created_work = create_profile_if_not_exists(PROFILE_WORK, WORK_SOUNDS)
        if created_work:
            profiles_to_cleanup.append(PROFILE_WORK)
            
        created_gaming = create_profile_if_not_exists(PROFILE_GAMING, GAMING_SOUNDS)
        if created_gaming:
            profiles_to_cleanup.append(PROFILE_GAMING)

        # Ensure we have profiles to switch between
        if not (created_work or (PROFILE_WORK in manager.get_available_profiles())) or \
           not (created_gaming or (PROFILE_GAMING in manager.get_available_profiles())):
            logger.error("Could not create or find the necessary scenario profiles. Aborting switching tests.")
            return

        # 3. Demonstrate Switching
        logger.info("\n3. Demonstrating profile switching:")
        available_profiles = manager.get_available_profiles()
        logger.info(f"Available profiles: {available_profiles}")

        # Load Work Profile
        logger.info(f"\n--> Loading WORK profile: '{PROFILE_WORK}'")
        if manager.load_sound_profile(PROFILE_WORK):
            logger.info(f"'{PROFILE_WORK}' loaded.")
            work_sound = manager.get_sound_for_event(TEST_EVENT)
            logger.info(f"Sound for '{TEST_EVENT}' is now: {'Disabled' if not work_sound else work_sound}")
            # Optionally play the sound
            # if work_sound:
            #     logger.info("Playing test sound...")
            #     manager.play_sound_for_event(TEST_EVENT, async_play=False)
            # else:
            #     logger.info("Test sound is disabled in this profile.")
            time.sleep(1) # Pause for effect
        else:
            logger.error(f"Failed to load profile '{PROFILE_WORK}'.")

        # Load Gaming Profile
        logger.info(f"\n--> Loading GAMING profile: '{PROFILE_GAMING}'")
        if manager.load_sound_profile(PROFILE_GAMING):
            logger.info(f"'{PROFILE_GAMING}' loaded.")
            gaming_sound = manager.get_sound_for_event(TEST_EVENT)
            logger.info(f"Sound for '{TEST_EVENT}' is now: {'Disabled' if not gaming_sound else gaming_sound}")
            # Optionally play the sound
            # logger.info("Playing test sound...")
            # manager.play_sound_for_event(TEST_EVENT, async_play=False)
            time.sleep(1) # Pause for effect
        else:
            logger.error(f"Failed to load profile '{PROFILE_GAMING}'.")
            
        # 4. Restore Default Backup
        logger.info(f"\n4. Restoring original settings from backup: '{PROFILE_DEFAULT_BACKUP}'")
        if manager.load_sound_profile(PROFILE_DEFAULT_BACKUP):
            logger.info("Original settings restored.")
            original_sound = manager.get_sound_for_event(TEST_EVENT)
            logger.info(f"Sound for '{TEST_EVENT}' is back to: {'Disabled' if not original_sound else original_sound}")
        else:
             logger.error(f"Failed to restore backup profile '{PROFILE_DEFAULT_BACKUP}'. Please check manually.")
             
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        # 5. Cleanup
        logger.info("\n5. Cleaning up created profiles...")
        # Use set to avoid duplicates if creation failed but profile existed
        profiles_to_delete = set(profiles_to_cleanup)
        
        if not profiles_to_delete:
             logger.info("No profiles to clean up.")
        else:
            logger.info(f"Attempting to delete: {list(profiles_to_delete)}")
            deleted_count = 0
            failed_count = 0
            for profile in profiles_to_delete:
                if manager.remove_profile(profile):
                    logger.info(f"  - Deleted '{profile}'")
                    deleted_count += 1
                else:
                    logger.warning(f"  - Failed to delete '{profile}'")
                    failed_count += 1
            logger.info(f"Cleanup finished. Deleted: {deleted_count}, Failed: {failed_count}")
            logger.info(f"Remaining profiles: {manager.get_available_profiles()}")

    logger.info("--- Profile Switching Example Finished ---")

if __name__ == "__main__":
    run_profile_switching_example() 