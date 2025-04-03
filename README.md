# System Sound Manager with MCP Support

This project provides a comprehensive Python framework for managing Windows system sounds programmatically. It allows listing, playing, and modifying system sounds, managing sound profiles, controlling audio volume/devices, and implementing context-aware sound changes based on system state or active applications using the Model Context Protocol (MCP).

## Features

*   **List System Sounds:** Enumerate all available Windows system sound events and their associated `.wav` files.
*   **Play Sounds:** Play specific system sounds by event name or play `.wav` files directly.
*   **Modify System Sounds:** Change the default sound for any system event by updating Windows registry entries. Handles permission requirements.
*   **Profile Management:** Save the current sound configuration as a named profile, load profiles to apply settings, list available profiles, and delete profiles. Profiles are stored in the `profiles/` directory as JSON.
*   **Audio Control:** Get/set master volume, get/set mute status, list audio input/output devices, and set the default audio device (experimental). Requires `pycaw`.
*   **MCP Support:** Implement context-aware sound management. Define rules in `config.json` to trigger sound profile changes or specific actions based on active window titles, running processes, or environment variables. (See `mcp_handler.py` and `config.json`).
*   **Command-Line Interface:** A basic CLI (`cli.py`) for manual interaction with most features.
*   **Logging:** Configurable logging (`logging_config.py`).
*   **Modular Design:** Code is structured into modules for better organization (`sound_manager.py`, `registry_handler.py`, `sound_operations.py`, `profile_manager.py`, `mcp_handler.py`, `audio_control.py`, `cli.py`).

## Requirements

*   Windows 10/11
*   Python 3.7+
*   Required packages (see `requirements.txt`):
    *   `pycaw`: For volume control and device management.
    *   `psutil`: For MCP process/window detection.
    *   `pywin32`: Often needed for Windows API interactions (implicitly used by other libs or potentially directly).

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```
2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    venv\Scripts\activate  # Windows
    # source venv/bin/activate # Linux/macOS (if adapted)
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Command-Line Interface (`cli.py`)

The CLI provides access to most functionalities. Run `python cli.py --help` for a full list of commands and options.

**Examples:**

*   List all system sounds:
    ```bash
    python cli.py list-sounds
    ```
*   Play the 'SystemAsterisk' sound:
    ```bash
    python cli.py play-event SystemAsterisk
    ```
*   Set the 'SystemExit' sound to a specific WAV file:
    ```bash
    python cli.py set-event SystemExit "C:\Windows\Media\tada.wav"
    ```
*   Save the current configuration to a profile named "MyWorkSetup":
    ```bash
    python cli.py save-profile MyWorkSetup
    ```
*   Load the "MyWorkSetup" profile:
    ```bash
    python cli.py load-profile MyWorkSetup
    ```
*   Get master volume:
    ```bash
    python cli.py get-volume
    ```
*   Set master volume to 50%:
    ```bash
    python cli.py set-volume 0.5
    ```
*   Start MCP monitoring (runs in the background):
    ```bash
    python cli.py mcp-start
    ```
*   Stop MCP monitoring:
    ```bash
    python cli.py mcp-stop
    ```

*(More examples can be added, potentially linking to the `examples/` directory)*

### Programmatic Usage

Import the `SoundManager` class from `sound_manager.py` or specific functions from other modules.

```python
from sound_manager import SoundManager
from logging_config import setup_logging

# Setup logging (optional but recommended)
setup_logging() 

manager = SoundManager()

# List sounds
sounds = manager.list_system_sounds()
print(sounds)

# Play a sound
manager.play_sound_for_event("SystemNotification")

# Set a sound (use with caution!)
# manager.set_sound_for_event("SystemHand", "C:\path\to\your\sound.wav")

# Load a profile
# manager.load_sound_profile("QuietHours") 
```

## MCP Configuration (`config.json`)

The `mcp_rules` section in `config.json` defines how the MCP handler behaves. Rules can trigger profile changes or specific actions based on context.

*(Details on configuring MCP rules should be added here or in separate documentation)*

## Security Considerations

*   **Registry Modifications:** Changing system sounds involves modifying the Windows Registry (`HKEY_CURRENT_USER\AppEvents\Schemes\Apps\.Default`). This script attempts to do this safely, but incorrect modifications can cause issues. Administrative privileges might be required for certain operations or if modifying system-wide defaults (though this script focuses on user-level settings).
*   **File Paths:** Ensure that any `.wav` file paths provided are valid and accessible. Maliciously crafted paths could potentially be exploited, although standard library functions provide some protection. Input validation is crucial.
*   **Permissions:** The script might fail if it doesn't have the necessary permissions to read/write registry keys or access audio devices/files. Run relevant parts with appropriate privileges if needed, but be cautious. The CLI/script should ideally run with standard user privileges for most operations.
*   **Dependencies:** Dependencies like `pycaw`, `psutil`, and `pywin32` interact closely with the OS. Ensure they are obtained from trusted sources.

## Contributing

*(Contribution guidelines can be added here)*

## License

*(Specify a license, e.g., MIT, Apache 2.0)* 