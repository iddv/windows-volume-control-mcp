import logging
import logging.handlers
import os

LOG_FILENAME = 'sound_mcp.log'
LOG_LEVEL = logging.INFO  # Default log level

# Ensure log directory exists if logging to a specific path
# log_dir = 'logs'
# if not os.path.exists(log_dir):
#     os.makedirs(log_dir)
# log_filepath = os.path.join(log_dir, LOG_FILENAME)

log_filepath = LOG_FILENAME # Log in the current directory for simplicity initially

def setup_logging():
    """Configures the root logger."""
    log_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Root logger setup
    logger = logging.getLogger()
    logger.setLevel(LOG_LEVEL)
    
    # Prevent adding multiple handlers if called multiple times
    if logger.hasHandlers():
        logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    # File handler (rotating)
    # Use RotatingFileHandler for production to prevent log files from growing indefinitely
    # For simplicity, using FileHandler for now. Add rotation if needed.
    try:
        file_handler = logging.FileHandler(log_filepath, mode='a')
        file_handler.setFormatter(log_formatter)
        logger.addHandler(file_handler)
    except PermissionError:
        logging.warning(f"No permission to write log file at {log_filepath}. Logging to console only.")
    except Exception as e:
        logging.error(f"Failed to set up file logging: {e}. Logging to console only.")

# Automatically configure logging when this module is imported
# setup_logging() 

# Example usage (can be removed later)
# if __name__ == '__main__':
#     setup_logging()
#     logging.info("Logging system initialized.")
#     logging.warning("This is a warning.")
#     logging.error("This is an error.")
#     logging.debug("This debug message won't show by default.") 