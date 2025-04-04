import logging
import os
import sys
from typing import Dict, Any

# Ensure the project root is in sys.path to find other modules
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from sound_manager import SoundManager
from logging_config import setup_logging

# Import MCP SDK
from mcp.server.fastmcp import FastMCP

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create an MCP server
mcp = FastMCP("Windows Volume Control")

# Global SoundManager instance
sound_manager = SoundManager()
logger.info("Sound manager initialized successfully")

@mcp.tool()
def get_volume() -> Dict[str, Any]:
    """Get the current master volume level."""
    volume = sound_manager.get_volume()
    if volume is not None:
        return {
            "volume": volume,
            "volume_percent": f"{int(volume * 100)}%"
        }
    else:
        raise ValueError("Failed to get volume")

@mcp.tool()
def set_volume(level: float) -> Dict[str, Any]:
    """
    Set the master volume level.
    
    Args:
        level: Volume level from 0.0 (mute) to 1.0 (max).
    """
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

@mcp.tool()
def mute_audio() -> Dict[str, str]:
    """Mute the system audio."""
    success = sound_manager.set_mute(True)
    if success:
        return {"message": "Audio muted"}
    else:
        raise ValueError("Failed to mute audio")

@mcp.tool()
def unmute_audio() -> Dict[str, str]:
    """Unmute the system audio."""
    success = sound_manager.set_mute(False)
    if success:
        return {"message": "Audio unmuted"}
    else:
        raise ValueError("Failed to unmute audio")

@mcp.tool()
def get_mute_status() -> Dict[str, Any]:
    """Get the current mute status."""
    muted = sound_manager.get_mute()
    if muted is not None:
        return {
            "muted": muted,
            "status": "muted" if muted else "unmuted"
        }
    else:
        raise ValueError("Failed to get mute status")

@mcp.tool()
def list_audio_devices(device_type: str = "output") -> Dict[str, Any]:
    """
    List available audio devices.
    
    Args:
        device_type: Type of devices ('output' or 'input').
    """
    if device_type not in ["output", "input"]:
        raise ValueError(f"Invalid device type: {device_type}. Use 'output' or 'input'.")
    
    devices = sound_manager.get_audio_devices(device_type)
    return {
        "devices": [{"name": name, "id": id} for name, id in devices]
    }

@mcp.prompt()
def help_prompt() -> str:
    """Create a help prompt with available commands."""
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
    print("Starting Windows Volume Control MCP server...")
    print("Ready to receive commands from Claude")
    mcp.run() 