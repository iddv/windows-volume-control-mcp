import argparse
import logging
import os
import sys
import time
from typing import List, Optional

# Ensure the project root is in sys.path to find other modules
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from logging_config import setup_logging, LOG_LEVEL
from sound_manager import SoundManager
from mcp_handler import MCPHandler

logger = logging.getLogger(__name__)

# Main entry point for the CLI application
def main(args: Optional[List[str]] = None):
    """Main function to parse arguments and execute commands."""
    parser = argparse.ArgumentParser(
        description="Manage Windows system sounds and profiles.",
        formatter_class=argparse.RawTextHelpFormatter # Preserve newline formatting in help
    )
    parser.add_argument(
        '--log-level', 
        default=logging.getLevelName(LOG_LEVEL),
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Set the logging level.'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands', required=True)

    # --- List Sounds Command ---
    parser_list = subparsers.add_parser('list', help='List current system sound events and their files.')
    parser_list.add_argument(
        '-f', '--filter',
        metavar='CATEGORY_REGEX',
        help='Filter event categories by regex (e.g., "System|Notification")'
    )
    parser_list.add_argument(
        '-s', '--show-unset',
        action='store_true',
        help='Include events that do not have a sound file assigned.'
    )

    # --- Play Sound Command ---
    parser_play = subparsers.add_parser('play', help='Play a sound.')
    play_group = parser_play.add_mutually_exclusive_group(required=True)
    play_group.add_argument(
        '-e', '--event',
        metavar='EVENT_CATEGORY',
        help='Play the sound associated with a specific system event category (e.g., SystemNotification).'
    )
    play_group.add_argument(
        '-f', '--file',
        metavar='WAV_FILE_PATH',
        help='Play a specific WAV file directly.'
    )
    parser_play.add_argument(
        '--sync', 
        action='store_true', 
        help='Play sound synchronously (wait for it to finish).'
    )
    # Assuming '.Current' is the most common sub-event for playback
    # parser_play.add_argument('--sub-event', default='.Current', help='Specify the sub-event (default: .Current)')

    # --- Set Sound Command ---
    parser_set = subparsers.add_parser('set', help='Set the sound file for a specific event.')
    parser_set.add_argument(
        'event', 
        metavar='EVENT_CATEGORY',
        help='The event category to modify (e.g., SystemNotification).'
    )
    parser_set.add_argument(
        'file_path', 
        metavar='WAV_FILE_PATH',
        help='Full path to the .wav file (use "" or '' for none).'
    )
    # parser_set.add_argument('--sub-event', default='.Current', help='Specify the sub-event (default: .Current)')

    # --- Profile Commands ---
    parser_profile = subparsers.add_parser('profile', help='Manage sound profiles.')
    profile_subparsers = parser_profile.add_subparsers(dest='profile_command', help='Profile actions', required=True)

    # profile list
    profile_list = profile_subparsers.add_parser('list', help='List saved sound profiles.')
    
    # profile save
    profile_save = profile_subparsers.add_parser('save', help='Save the current sound settings to a profile.')
    profile_save.add_argument('name', help='Name for the new profile.')

    # profile load/apply
    profile_load = profile_subparsers.add_parser('load', help='Load and apply a sound profile.')
    profile_load.add_argument('name', help='Name of the profile to load.')

    # profile delete
    profile_delete = profile_subparsers.add_parser('delete', help='Delete a saved sound profile.')
    profile_delete.add_argument('name', help='Name of the profile to delete.')

    # --- Monitor Command (MCP) ---
    parser_monitor = subparsers.add_parser('monitor', help='Start context-aware monitoring to automatically switch profiles.')
    # Add potential monitor-specific args later (e.g., --config)

    # --- Volume Command ---
    parser_volume = subparsers.add_parser('volume', help='Control master volume.')
    volume_group = parser_volume.add_mutually_exclusive_group(required=True)
    volume_group.add_argument(
        '--set', 
        metavar='LEVEL', 
        type=float, 
        help='Set volume level (0.0 to 1.0).'
    )
    volume_group.add_argument(
        '--get', 
        action='store_true', 
        help='Get current volume level.'
    )
    volume_group.add_argument(
        '--mute', 
        action='store_true', 
        help='Mute master volume.'
    )
    volume_group.add_argument(
        '--unmute', 
        action='store_true', 
        help='Unmute master volume.'
    )
    volume_group.add_argument(
        '--get-mute', 
        action='store_true', 
        help='Get current mute status.'
    )

    # --- Device Command ---
    parser_device = subparsers.add_parser('device', help='Manage audio devices.')
    device_subparsers = parser_device.add_subparsers(dest='device_command', help='Device actions', required=True)
    
    # device list
    dev_list = device_subparsers.add_parser('list', help='List audio devices.')
    dev_list.add_argument(
        '--type',
        default='output',
        choices=['output', 'input'],
        help='Type of devices to list (output/input).'
    )
    
    # device set-default (Experimental)
    dev_set = device_subparsers.add_parser('set-default', help='Set default audio device (EXPERIMENTAL). Note: May not work reliably.')
    dev_set.add_argument('id', help="ID of the device to set as default (see 'device list' command).")
    dev_set.add_argument(
        '--type',
        default='output',
        choices=['output', 'input'],
        help='Type of device (output/input).'
    )

    # --- Parse Arguments ---
    parsed_args = parser.parse_args(args)

    # --- Setup Logging ---
    # Set log level based on command line arg
    log_level_name = parsed_args.log_level.upper()
    logging_config_module = sys.modules['logging_config']
    logging_config_module.LOG_LEVEL = getattr(logging, log_level_name, logging.INFO)
    setup_logging() # Initialize with potentially updated level
    
    logger.debug(f"Parsed arguments: {parsed_args}")

    # --- Initialize Manager ---
    try:
        manager = SoundManager()
    except Exception as e:
        logger.critical(f"Failed to initialize SoundManager: {e}", exc_info=True)
        sys.exit(1)

    # --- Execute Command ---
    exit_code = 0
    try:
        if parsed_args.command == 'list':
            handle_list_command(manager, parsed_args)
        elif parsed_args.command == 'play':
            handle_play_command(manager, parsed_args)
        elif parsed_args.command == 'set':
            handle_set_command(manager, parsed_args)
        elif parsed_args.command == 'profile':
            handle_profile_command(manager, parsed_args)
        elif parsed_args.command == 'monitor':
            handle_monitor_command(manager, parsed_args)
        elif parsed_args.command == 'volume':
            handle_volume_command(manager, parsed_args)
        elif parsed_args.command == 'device':
            handle_device_command(manager, parsed_args)
        else:
            # Should not happen due to `required=True`
            logger.error(f"Unknown command: {parsed_args.command}")
            parser.print_help()
            exit_code = 1
            
    except PermissionError as e:
        # Catch common permission errors, especially for set/load operations
        logger.error(f"Permission denied: {e}. Try running as administrator if changing settings.")
        exit_code = 1
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        exit_code = 1
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        exit_code = 1
        
    sys.exit(exit_code)

# --- Command Handler Functions ---
# These functions are called based on the parsed command-line arguments.

# Handler for the 'list' command
def handle_list_command(manager: SoundManager, args: argparse.Namespace):
    sounds = manager.list_system_sounds()
    if not sounds:
        print("Could not retrieve any sound events. Check logs.")
        return

    import re
    category_filter = None
    if args.filter:
        # Compile user-provided regex for filtering event categories
        try:
            category_filter = re.compile(args.filter, re.IGNORECASE)
        except re.error as e:
            logger.error(f"Invalid regex pattern '{args.filter}': {e}")
            print(f"Error: Invalid filter regex: {e}")
            sys.exit(1)

    print("Current System Sounds:")
    displayed_count = 0
    for category, sub_events in sorted(sounds.items()):
        if category_filter and not category_filter.search(category):
            continue
            
        # Print category header only if it has matching sub-events
        category_header_printed = False
        for sub_event, path in sorted(sub_events.items()):
            if path or args.show_unset:
                if not category_header_printed:
                     print(f"\n[{category}]")
                     category_header_printed = True
                path_display = path if path else "(None)"
                print(f"  {sub_event}: {path_display}")
                displayed_count += 1
                
    if displayed_count == 0:
         print("(No matching sound events found based on filter/options)")

# Handler for the 'play' command
def handle_play_command(manager: SoundManager, args: argparse.Namespace):
    async_play = not args.sync
    success = False
    if args.event:
        print(f"Playing event: {args.event} ({'async' if async_play else 'sync'})...")
        success = manager.play_sound_for_event(args.event, async_play=async_play)
    elif args.file:
        print(f"Playing file: {args.file} ({'async' if async_play else 'sync'})...")
        success = manager.play_sound_file(args.file, async_play=async_play)
    
    if success:
        print("Playback initiated.")
        # If sync, it should have already finished here
        # If async, maybe add a small delay if needed for user feedback? time.sleep(1)
    else:
        print("Playback failed. Check logs or file/event existence.")
        sys.exit(1)

# Handler for the 'set' command
def handle_set_command(manager: SoundManager, args: argparse.Namespace):
    # Handle empty string input which signifies disabling the sound event
    path_to_set = args.file_path if args.file_path else ""
    print(f"Setting sound for event '{args.event}' to: '{path_to_set or '(None)'}'")
    if manager.set_sound_for_event(args.event, path_to_set):
        print("Sound set successfully. Changes should take effect shortly.")
    else:
        print("Failed to set sound. Check logs for errors (permissions?).")
        sys.exit(1)

# Handler for the 'profile' subcommand
def handle_profile_command(manager: SoundManager, args: argparse.Namespace):
    if args.profile_command == 'list':
        profiles = manager.get_available_profiles()
        if profiles:
            print("Available Profiles:")
            for p in sorted(profiles):
                print(f"- {p}")
        else:
            print("(No profiles found)")
            
    elif args.profile_command == 'save':
        print(f"Saving current sound settings to profile: '{args.name}'")
        if manager.save_current_profile(args.name):
            print("Profile saved successfully.")
        else:
            print("Failed to save profile. Check logs.")
            sys.exit(1)
            
    elif args.profile_command == 'load':
        print(f"Loading and applying profile: '{args.name}'")
        if manager.load_sound_profile(args.name):
            print("Profile applied successfully. Check logs for any individual sound failures.")
        else:
            print("Failed to apply profile completely. Check logs.")
            sys.exit(1) # Indicate failure
            
    elif args.profile_command == 'delete':
        # Add a confirmation step before deleting a profile
        confirm = input(f"Are you sure you want to delete profile '{args.name}'? (y/N): ")
        if confirm.lower() == 'y':
            print(f"Deleting profile: '{args.name}'")
            if manager.remove_profile(args.name):
                print("Profile deleted successfully.")
            else:
                print("Failed to delete profile. Check logs.")
                sys.exit(1)
        else:
             print("Deletion cancelled.")

# Handler for the 'volume' command
def handle_volume_command(manager: SoundManager, args: argparse.Namespace):
    """Handles volume control commands."""
    logger.info(f"Handling 'volume' command with args: {args}")
    success = False
    try:
        if args.set is not None:
            if 0.0 <= args.set <= 1.0:
                print(f"Setting master volume to {args.set:.0%}")
                success = manager.set_volume(args.set)
            else:
                print("Error: Volume level must be between 0.0 and 1.0.")
                sys.exit(1)
        elif args.get:
            level = manager.get_volume()
            if level is not None:
                print(f"Current master volume: {level:.0%}")
                success = True
            else:
                print("Failed to get volume level.")
        elif args.mute:
            print("Muting master volume...")
            success = manager.set_mute(True)
        elif args.unmute:
            print("Unmuting master volume...")
            success = manager.set_mute(False)
        elif args.get_mute:
             muted = manager.get_mute()
             if muted is not None:
                 print(f"Master mute status: {'Muted' if muted else 'Unmuted'}")
                 success = True
             else:
                 print("Failed to get mute status.")
                 
    except ImportError as e:
         logger.error(f"Volume command failed: {e}")
         print(f"Error: {e}. Is pycaw installed?")
         sys.exit(1)
    except Exception as e:
        logger.error(f"Error during volume command: {e}", exc_info=True)
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

    if not success and not (args.get or args.get_mute):
        print("Volume command failed. Check logs.")
        sys.exit(1)

# Handler for the 'device' command
def handle_device_command(manager: SoundManager, args: argparse.Namespace):
    """Handles audio device commands."""
    logger.info(f"Handling 'device' command: {args.device_command}")
    try:
        if args.device_command == 'list':
            print(f"Listing {args.type} devices...")
            devices = manager.get_audio_devices(args.type)
            if devices:
                print(f"Found {len(devices)} {args.type} device(s):")
                for name, dev_id in devices:
                    # Potentially mark default device here if we can detect it
                    print(f"- Name: {name}\n  ID:   {dev_id}")
            else:
                print(f"(No {args.type} devices found or error retrieving list)")
                
        elif args.device_command == 'set-default':
             print(f"Attempting to set default {args.type} device to ID: {args.id} (EXPERIMENTAL)")
             print("NOTE: This operation is unreliable and may not work.")
             if manager.set_active_audio_device(args.id, args.type):
                 # Success here only means the attempt was made
                 print("Attempted to set default device. Verification needed manually or via other tools.")
             else:
                 print("Failed to attempt setting default device. Check logs.")
                 sys.exit(1)
                 
    except ImportError as e:
         logger.error(f"Device command failed: {e}")
         print(f"Error: {e}. Is pycaw installed?")
         sys.exit(1)
    except Exception as e:
        logger.error(f"Error during device command: {e}", exc_info=True)
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

# Handler for the 'monitor' command (MCP)
def handle_monitor_command(manager: SoundManager, args: argparse.Namespace):
    """Handles the 'monitor' command to start MCP."""
    logger.info("Handling 'monitor' command.")
    try:
        # Assuming default config path for now
        mcp = MCPHandler(manager)
        print("Starting MCP monitoring based on config.json...")
        print("Monitoring active window. Press Ctrl+C to stop.")
        mcp.start_monitoring()
        
        # Keep the main thread alive while the monitor thread runs
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nCtrl+C received. Stopping monitoring...")
            mcp.stop_monitoring()
            print("Monitoring stopped.")
            
    except ImportError as e:
        logger.error(f"Failed to start monitoring due to missing dependencies: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Failed to run MCP monitoring: {e}", exc_info=True)
        print(f"An error occurred during monitoring: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 