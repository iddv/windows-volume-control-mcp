import winsound
import logging
import os
from typing import Optional

# Assuming registry_handler is in the same directory or accessible via PYTHONPATH
from registry_handler import get_sound_file_path

logger = logging.getLogger(__name__)

def play_system_sound(event_category: str, sub_event: str = ".Current", async_play: bool = True) -> bool:
    """Plays the sound associated with a specific system event.

    Retrieves the sound file path from the registry and plays it using winsound.

    Args:
        event_category (str): The main event category (e.g., 'SystemAsterisk').
        sub_event (str): The specific sub-event (e.g., '.Current'). Defaults to '.Current'.
        async_play (bool): If True, play the sound asynchronously (non-blocking).
                           If False, play synchronously (blocks until sound finishes).

    Returns:
        bool: True if the sound was played successfully, False otherwise.
    """
    sound_file = get_sound_file_path(event_category, sub_event)
    
    if not sound_file:
        logger.info(f"No sound file configured for event '{event_category}\\{sub_event}'.")
        # We explicitly choose not to play a fallback sound here.
        # If the user hasn't assigned a sound to this specific event,
        # playing the generic default might be confusing or unwanted.
        # Playing 'None' with SND_ALIAS | SND_NODEFAULT might play the system default sound,
        # but we want to play *nothing* if the specific event sound is not set.
        # So, we just return False here.
        # Alternatively, could try playing a known system default like 'SystemDefault'?
        # winsound.PlaySound('SystemDefault', winsound.SND_ALIAS | winsound.SND_NODEFAULT)
        return False

    if not os.path.exists(sound_file):
        logger.error(f"Sound file for event '{event_category}\\{sub_event}' not found at path: {sound_file}")
        return False
        
    return play_wav_file(sound_file, async_play)

def play_wav_file(file_path: str, async_play: bool = True) -> bool:
    """Plays a specific .wav file.

    Args:
        file_path (str): The full path to the .wav file.
        async_play (bool): If True, play the sound asynchronously (non-blocking).
                           If False, play synchronously (blocks until sound finishes).

    Returns:
        bool: True if playback was initiated successfully, False otherwise.
    """
    if not file_path or not isinstance(file_path, str):
        logger.error(f"Invalid file path provided: {file_path}")
        return False
        
    if not os.path.exists(file_path):
        logger.error(f"WAV file not found: {file_path}")
        return False

    if not file_path.lower().endswith('.wav'):
        logger.warning(f"File does not appear to be a .wav file: {file_path}. Playback might fail.")
        # Attempt playback anyway?

    flags = winsound.SND_FILENAME | winsound.SND_NODEFAULT
    if async_play:
        flags |= winsound.SND_ASYNC
    else:
        flags |= winsound.SND_SYNC # Default is SND_SYNC if neither specified

    try:
        logger.debug(f"Playing sound: {file_path} with flags: {flags}")
        winsound.PlaySound(file_path, flags)
        logger.info(f"Played sound: {os.path.basename(file_path)}")
        return True
    except RuntimeError as e:
        # winsound can raise RuntimeError for various reasons (e.g., invalid format, device busy)
        logger.error(f"Error playing sound file {file_path}: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Unexpected error playing sound file {file_path}: {e}", exc_info=True)
        return False

# Example Usage (for testing, remove later)
# if __name__ == '__main__':
#     import sys
#     import time
#     # Add project root to sys.path to find logging_config if run directly
#     # script_dir = os.path.dirname(os.path.abspath(__file__))
#     # project_root = os.path.dirname(script_dir) 
#     # if project_root not in sys.path:
#     #     sys.path.insert(0, project_root)

#     from logging_config import setup_logging
#     setup_logging() # Initialize logging

#     # --- Test playing a system sound --- 
#     event_to_test = "SystemNotification" # Common sound
#     print(f"\n--- Testing play_system_sound('{event_to_test}') ---")
#     if not play_system_sound(event_to_test, async_play=False):
#          print(f"Could not play system sound '{event_to_test}'. Is it configured in Windows?")
#     else:
#         print("System sound played (sync).")
        
#     # Test async
#     print(f"\n--- Testing play_system_sound('{event_to_test}', async_play=True) ---")
#     if play_system_sound(event_to_test, async_play=True):
#         print("System sound playing (async)... should return immediately.")
#         # Give async sound time to play before potentially exiting script
#         # time.sleep(2) 
#     else:
#         print(f"Could not play system sound '{event_to_test}' asynchronously.")

#     # --- Test playing a specific WAV file --- 
#     # Find a common WAV file
#     test_wav = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Media', 'Windows Notify System Generic.wav')
#     print(f"\n--- Testing play_wav_file('{test_wav}') ---")
#     if os.path.exists(test_wav):
#         if play_wav_file(test_wav, async_play=False):
#             print("Direct WAV file played (sync).")
#         else:
#             print("Failed to play direct WAV file (sync).")
            
#         if play_wav_file(test_wav, async_play=True):
#             print("Direct WAV file playing (async)...")
#             # time.sleep(2) 
#         else:
#             print("Failed to play direct WAV file (async).")
#     else:
#         print(f"Test WAV file not found at {test_wav}, skipping direct play test.")

#     # --- Test non-existent file/event --- 
#     print("\n--- Testing non-existent sound ---")
#     play_system_sound("NonExistentEventCategory")
#     play_wav_file("C:\\path\to\non\existent\sound.wav") 