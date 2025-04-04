import logging
import os
import sys
import traceback
from typing import Dict, Any

# Ensure the project root is in sys.path to find other modules
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Debug output to stderr
def debug(message):
    print(f"DEBUG: {message}", file=sys.stderr, flush=True)

debug("Starting Windows Volume Control MCP server...")

try:
    from sound_manager import SoundManager
    from logging_config import setup_logging

    # Import MCP SDK
    debug("Importing MCP SDK...")
    from mcp.server.fastmcp import FastMCP
    import mcp.types as types

    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    debug("Logging configured.")

    # Create an MCP server with detailed logging
    debug("Creating MCP server instance...")
    mcp = FastMCP("Windows Volume Control")

    # Global SoundManager instance
    debug("Initializing SoundManager...")
    try:
        sound_manager = SoundManager()
        debug("Sound manager initialized successfully")
    except Exception as e:
        debug(f"Error initializing SoundManager: {e}")
        debug(traceback.format_exc())
        raise

    @mcp.tool()
    def get_volume() -> Dict[str, Any]:
        """Get the current master volume level."""
        try:
            debug("Tool called: get_volume")
            volume = sound_manager.get_volume()
            if volume is not None:
                return {
                    "volume": volume,
                    "volume_percent": f"{int(volume * 100)}%"
                }
            else:
                raise ValueError("Failed to get volume")
        except Exception as e:
            debug(f"Error in get_volume: {e}")
            debug(traceback.format_exc())
            raise

    @mcp.tool()
    def set_volume(level: float) -> Dict[str, Any]:
        """
        Set the master volume level.
        
        Args:
            level: Volume level from 0.0 (mute) to 1.0 (max).
        """
        try:
            debug(f"Tool called: set_volume with level={level}")
            if not 0.0 <= level <= 1.0:
                raise ValueError(f"Volume level must be between 0.0 and 1.0, got {level}")
            
            success = sound_manager.set_volume(level)
            if success:
                return {
                    "success": True,
                    "message": f"Volume set to {int(level * 100)}%"
                }
            else:
                raise ValueError("Failed to set volume")
        except Exception as e:
            debug(f"Error in set_volume: {e}")
            debug(traceback.format_exc())
            raise

    @mcp.tool()
    def mute_audio() -> Dict[str, str]:
        """Mute the system audio."""
        try:
            debug("Tool called: mute_audio")
            success = sound_manager.set_mute(True)
            if success:
                return {"message": "Audio muted"}
            else:
                raise ValueError("Failed to mute audio")
        except Exception as e:
            debug(f"Error in mute_audio: {e}")
            debug(traceback.format_exc())
            raise

    @mcp.tool()
    def unmute_audio() -> Dict[str, str]:
        """Unmute the system audio."""
        try:
            debug("Tool called: unmute_audio")
            success = sound_manager.set_mute(False)
            if success:
                return {"message": "Audio unmuted"}
            else:
                raise ValueError("Failed to unmute audio")
        except Exception as e:
            debug(f"Error in unmute_audio: {e}")
            debug(traceback.format_exc())
            raise

    @mcp.tool()
    def get_mute_status() -> Dict[str, Any]:
        """Get the current mute status."""
        try:
            debug("Tool called: get_mute_status")
            muted = sound_manager.get_mute()
            if muted is not None:
                return {
                    "muted": muted,
                    "status": "muted" if muted else "unmuted"
                }
            else:
                raise ValueError("Failed to get mute status")
        except Exception as e:
            debug(f"Error in get_mute_status: {e}")
            debug(traceback.format_exc())
            raise

    @mcp.tool()
    def list_audio_devices(device_type: str = "output") -> Dict[str, Any]:
        """
        List available audio devices.
        
        Args:
            device_type: Type of devices ('output' or 'input').
        """
        try:
            debug(f"Tool called: list_audio_devices with device_type={device_type}")
            if device_type not in ["output", "input"]:
                raise ValueError(f"Invalid device type: {device_type}. Use 'output' or 'input'.")
            
            devices = sound_manager.get_audio_devices(device_type)
            return {
                "devices": [{"name": name, "id": id} for name, id in devices]
            }
        except Exception as e:
            debug(f"Error in list_audio_devices: {e}")
            debug(traceback.format_exc())
            raise

    @mcp.prompt()
    def help_prompt() -> str:
        """Create a help prompt with available commands."""
        debug("Prompt called: help_prompt")
        return """
    I can help you control your Windows system volume. Here are some things you can ask me to do:

    1. Get the current volume: "What's my current volume?"
    2. Set the volume: "Set my volume to 70%" or "Turn the volume up/down"
    3. Mute or unmute: "Mute my computer" or "Unmute my audio"
    4. Check mute status: "Is my audio muted?"
    5. List audio devices: "Show me my audio devices"

    How can I help you with your audio settings today?
    """

    if __name__ == "__main__":
        # Run the MCP server
        debug("About to start MCP server...")
        print("Starting Windows Volume Control MCP server...")
        print("Ready to receive commands from Claude")
        try:
            mcp.run()
        except Exception as e:
            debug(f"Error running MCP server: {e}")
            debug(traceback.format_exc())
            raise

except Exception as e:
    debug(f"Unhandled error: {e}")
    debug(traceback.format_exc())
    raise 