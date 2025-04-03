"""
Example demonstrating programmatic usage of the SoundManager.
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
    from audio_control import list_audio_devices # For device listing example
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Ensure the script is run from the project root or the root is in the Python path.")
    sys.exit(1)

# --- Configuration ---
PROFILE_NAME = "ProgrammaticTestProfile"
SOUND_EVENT_TO_TEST = "SystemNotification" # A common sound event
# Use a standard Windows sound for setting example, ensure it exists
EXAMPLE_SOUND_FILE = "C:\\Windows\\Media\\Windows Notify System Generic.wav" 
if not os.path.exists(EXAMPLE_SOUND_FILE):
    # Fallback if the specific sound is missing
    EXAMPLE_SOUND_FILE = "C:\\Windows\\Media\\tada.wav" 
    if not os.path.exists(EXAMPLE_SOUND_FILE):
        EXAMPLE_SOUND_FILE = None # Skip setting sound if no example found

VOLUME_LEVEL_TEST = 0.6 # 60% volume
DEVICE_TYPE_TO_LIST = 'output' # 'output' or 'input'

# --- Initialization ---
setup_logging(level=logging.INFO) # Configure logging
logger = logging.getLogger(__name__)
manager = SoundManager()

def run_examples():
    """Runs through various programmatic examples."""
    logger.info("--- Starting Programmatic Sound Manager Examples ---")

    # 1. List System Sounds (subset)
    try:
        logger.info("\n1. Listing available system sounds (first 5 categories):")
        sounds = manager.list_system_sounds()
        count = 0
        for category, sub_events in sounds.items():
            logger.info(f"  Category: {category}")
            # Log one example path per category if available
            for sub, path in sub_events.items():
                if path:
                    logger.info(f"    {sub}: {path}")
                    break 
            count += 1
            if count >= 5:
                logger.info("  ...")
                break
    except Exception as e:
        logger.error(f"Error listing sounds: {e}")

    # 2. Play a System Sound Event
    try:
        logger.info(f"\n2. Playing sound for event: '{SOUND_EVENT_TO_TEST}'")
        if not manager.play_sound_for_event(SOUND_EVENT_TO_TEST, async_play=False):
            logger.warning(f"Could not play sound for event '{SOUND_EVENT_TO_TEST}'. Is a sound configured?")
        else:
            logger.info(f"Played '{SOUND_EVENT_TO_TEST}' synchronously.")
            time.sleep(0.5) # Give it time to play
    except Exception as e:
        logger.error(f"Error playing sound event: {e}")

    # 3. Play a specific WAV file (if example found)
    if EXAMPLE_SOUND_FILE:
        try:
            logger.info(f"\n3. Playing specific WAV file: {EXAMPLE_SOUND_FILE}")
            if not manager.play_sound_file(EXAMPLE_SOUND_FILE, async_play=False):
                logger.warning(f"Could not play WAV file '{EXAMPLE_SOUND_FILE}'.")
            else:
                logger.info(f"Played '{EXAMPLE_SOUND_FILE}' synchronously.")
                time.sleep(0.5) # Give it time to play
        except Exception as e:
            logger.error(f"Error playing WAV file: {e}")
    else:
         logger.warning("\n3. Skipping playing specific WAV file (example file not found).")


    # --- Profile Management ---
    original_sound = None
    profile_created = False
    try:
        logger.info("\n--- Profile Management Examples ---")
        
        # Get original sound to restore later if we change it
        original_sound = manager.get_sound_for_event(SOUND_EVENT_TO_TEST)
        logger.info(f"Original sound for '{SOUND_EVENT_TO_TEST}': {original_sound}")

        # 4. Save current settings to a profile
        logger.info(f"\n4. Saving current sound settings to profile: '{PROFILE_NAME}'")
        if manager.save_current_profile(PROFILE_NAME):
            logger.info(f"Profile '{PROFILE_NAME}' saved successfully.")
            profile_created = True
        else:
            logger.error(f"Failed to save profile '{PROFILE_NAME}'. Check permissions or logs.")
            return # Stop if saving failed

        # 5. List available profiles
        logger.info("\n5. Listing available profiles:")
        profiles = manager.get_available_profiles()
        logger.info(f"Available profiles: {profiles}")
        if PROFILE_NAME not in profiles:
             logger.warning(f"Profile '{PROFILE_NAME}' was saved but not listed immediately?")

        # 6. Modify a sound setting (if example sound exists)
        if EXAMPLE_SOUND_FILE:
            logger.info(f"\n6. Changing sound for '{SOUND_EVENT_TO_TEST}' to '{EXAMPLE_SOUND_FILE}'")
            if manager.set_sound_for_event(SOUND_EVENT_TO_TEST, EXAMPLE_SOUND_FILE):
                logger.info(f"Sound for '{SOUND_EVENT_TO_TEST}' changed. Playing new sound...")
                time.sleep(0.2)
                manager.play_sound_for_event(SOUND_EVENT_TO_TEST, async_play=False)
                time.sleep(0.5)
            else:
                logger.error(f"Failed to set sound for '{SOUND_EVENT_TO_TEST}'. Permissions?")
        else:
            logger.warning("\n6. Skipping setting sound event (example file not found).")


        # 7. Load the saved profile to restore settings
        logger.info(f"\n7. Loading profile '{PROFILE_NAME}' to restore original settings...")
        if manager.load_sound_profile(PROFILE_NAME):
            logger.info(f"Profile '{PROFILE_NAME}' loaded successfully.")
            restored_sound = manager.get_sound_for_event(SOUND_EVENT_TO_TEST)
            logger.info(f"Sound for '{SOUND_EVENT_TO_TEST}' after restore: {restored_sound}")
            if restored_sound != original_sound:
                 logger.warning("Restored sound doesn't match original. Profile might be slightly different?")
            else:
                 logger.info("Sound successfully restored by profile.")
        else:
            logger.error(f"Failed to load profile '{PROFILE_NAME}'. Manual restore might be needed.")

    except Exception as e:
        logger.error(f"Error during profile management: {e}")
    finally:
        # 8. Clean up: Delete the test profile
        if profile_created:
            logger.info(f"\n8. Cleaning up: Deleting profile '{PROFILE_NAME}'")
            if manager.remove_profile(PROFILE_NAME):
                logger.info(f"Profile '{PROFILE_NAME}' deleted.")
            else:
                logger.warning(f"Failed to delete profile '{PROFILE_NAME}'.")
            logger.info(f"Remaining profiles: {manager.get_available_profiles()}")
        
        # Ensure original sound is restored if profile load failed or modification happened before save
        if EXAMPLE_SOUND_FILE and manager.get_sound_for_event(SOUND_EVENT_TO_TEST) != original_sound and original_sound is not None:
             logger.warning(f"Attempting final restore of '{SOUND_EVENT_TO_TEST}' to '{original_sound}'")
             if manager.set_sound_for_event(SOUND_EVENT_TO_TEST, original_sound):
                 logger.info("Final restore successful.")
             else:
                 logger.error("Final restore failed. Please check manually.")


    # --- Audio Control Examples (Requires pycaw) ---
    try:
        logger.info("\n--- Audio Control Examples ---")
        
        # 9. Get/Set Volume
        logger.info("\n9. Testing Volume Control")
        initial_volume = manager.get_volume()
        if initial_volume is not None:
            logger.info(f"Initial master volume: {initial_volume:.2f}")
            logger.info(f"Setting volume to {VOLUME_LEVEL_TEST:.2f}...")
            if manager.set_volume(VOLUME_LEVEL_TEST):
                # Read back might be slightly different due to float precision
                time.sleep(0.5) # Give system time to apply
                new_volume = manager.get_volume()
                logger.info(f"Volume after setting (read back): {new_volume:.2f}")
                # Restore volume
                logger.info(f"Restoring original volume ({initial_volume:.2f})...")
                manager.set_volume(initial_volume)
            else:
                logger.error("Failed to set volume.")
        else:
            logger.warning("Could not get initial volume. Skipping volume tests. Is pycaw installed?")

        # 10. Get/Set Mute
        logger.info("\n10. Testing Mute Control")
        initial_mute = manager.get_mute()
        if initial_mute is not None:
            logger.info(f"Initial mute status: {initial_mute}")
            logger.info(f"Setting mute to {not initial_mute}...")
            if manager.set_mute(not initial_mute):
                time.sleep(0.5) # Give system time
                new_mute = manager.get_mute()
                logger.info(f"Mute status after setting: {new_mute}")
                # Restore mute status
                logger.info(f"Restoring original mute status ({initial_mute})...")
                manager.set_mute(initial_mute)
            else:
                logger.error("Failed to set mute.")
        else:
            logger.warning("Could not get mute status. Skipping mute tests. Is pycaw installed?")

        # 11. List Audio Devices
        logger.info(f"\n11. Listing {DEVICE_TYPE_TO_LIST} audio devices:")
        devices = manager.get_audio_devices(device_type=DEVICE_TYPE_TO_LIST)
        if devices:
            for i, (name, dev_id) in enumerate(devices):
                logger.info(f"  Device {i}: Name=\"{name}\", ID=\"{dev_id}\"")
        else:
             logger.warning(f"No {DEVICE_TYPE_TO_LIST} devices found or pycaw not installed.")
             
        # 12. Set Default Audio Device (EXPERIMENTAL - often needs elevation or specific setup)
        # logger.info("\n12. Testing Set Default Audio Device (EXPERIMENTAL)")
        # if devices:
        #     target_device_id = devices[0][1] # Try setting to the first device listed
        #     logger.warning(f"Attempting to set default {DEVICE_TYPE_TO_LIST} device to ID: {target_device_id}")
        #     logger.warning("This operation is unreliable and may require admin rights.")
        #     if manager.set_active_audio_device(target_device_id, device_type=DEVICE_TYPE_TO_LIST):
        #         logger.info("Set default device call succeeded (verify in system settings).")
        #     else:
        #         logger.error("Set default device call failed.")
        # else:
        #     logger.warning("No devices listed, cannot test setting default device.")

    except ImportError:
         logger.warning("\nAudio control functions require 'pycaw'. Skipping these examples.")
    except Exception as e:
        logger.error(f"Error during audio control examples: {e}")

    logger.info("\n--- Programmatic Sound Manager Examples Finished ---")

if __name__ == "__main__":
    run_examples() 