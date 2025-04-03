import json
import socket
import logging
import argparse
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Ensure the project root is in sys.path to find other modules
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from sound_manager import SoundManager
from logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global SoundManager instance
sound_manager = None

class MCPRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for MCP requests from Claude."""
    
    def log_message(self, format, *args):
        """Override to use our logger instead of stderr."""
        logger.info(f"{self.address_string()} - {format%args}")
    
    def do_GET(self):
        """Handle GET requests - used for health checks and simple commands."""
        parsed_path = urlparse(self.path)
        
        # Health check endpoint
        if parsed_path.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {'status': 'ok', 'message': 'Windows Volume Control MCP server is running'}
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return
            
        # Handle other GET endpoints
        self.send_response(404)
        self.end_headers()
    
    def do_POST(self):
        """Handle POST requests - main command interface."""
        global sound_manager
        
        # Get content length
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length <= 0:
            self.send_response(400)
            self.end_headers()
            return
            
        # Read and parse the request body
        request_body = self.rfile.read(content_length).decode('utf-8')
        try:
            data = json.loads(request_body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            logger.error(f"Invalid JSON in request: {request_body}")
            return
            
        # Process the command
        command = data.get('command', '')
        args = data.get('args', {})
        result = {'success': False, 'message': 'Unknown command'}
        
        logger.info(f"Received command: {command}, args: {args}")
        
        if command == 'get_volume':
            # Get current volume
            volume = sound_manager.get_volume()
            if volume is not None:
                result = {
                    'success': True, 
                    'volume': volume,
                    'volume_percent': f"{int(volume * 100)}%"
                }
            else:
                result = {'success': False, 'message': 'Failed to get volume'}
                
        elif command == 'set_volume':
            # Set volume (0.0 to 1.0)
            level = args.get('level')
            if level is not None:
                try:
                    level_float = float(level)
                    if 0.0 <= level_float <= 1.0:
                        success = sound_manager.set_volume(level_float)
                        if success:
                            result = {
                                'success': True, 
                                'message': f'Volume set to {int(level_float * 100)}%'
                            }
                        else:
                            result = {'success': False, 'message': 'Failed to set volume'}
                    else:
                        result = {'success': False, 'message': 'Volume level must be between 0.0 and 1.0'}
                except ValueError:
                    result = {'success': False, 'message': 'Invalid volume level format'}
            else:
                result = {'success': False, 'message': 'Missing level parameter'}
                
        elif command == 'mute':
            # Mute audio
            success = sound_manager.set_mute(True)
            if success:
                result = {'success': True, 'message': 'Audio muted'}
            else:
                result = {'success': False, 'message': 'Failed to mute audio'}
                
        elif command == 'unmute':
            # Unmute audio
            success = sound_manager.set_mute(False)
            if success:
                result = {'success': True, 'message': 'Audio unmuted'}
            else:
                result = {'success': False, 'message': 'Failed to unmute audio'}
                
        elif command == 'get_mute':
            # Get mute status
            muted = sound_manager.get_mute()
            if muted is not None:
                result = {
                    'success': True,
                    'muted': muted,
                    'status': 'muted' if muted else 'unmuted'
                }
            else:
                result = {'success': False, 'message': 'Failed to get mute status'}
                
        elif command == 'list_devices':
            # List audio devices
            device_type = args.get('type', 'output')
            devices = sound_manager.get_audio_devices(device_type)
            if devices:
                result = {
                    'success': True,
                    'devices': [{'name': name, 'id': id} for name, id in devices]
                }
            else:
                result = {
                    'success': True,
                    'devices': [],
                    'message': f'No {device_type} devices found'
                }
        
        # Send the response
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode('utf-8'))

def start_server(host='localhost', port=35429):
    """Start the MCP HTTP server."""
    global sound_manager
    
    # Initialize the SoundManager
    try:
        sound_manager = SoundManager()
        logger.info("Sound manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize SoundManager: {e}")
        return False
    
    # Create and start the server
    server_address = (host, port)
    try:
        httpd = HTTPServer(server_address, MCPRequestHandler)
        logger.info(f"Starting MCP server on {host}:{port}")
        
        # Print a message that Claude can see to confirm the server is ready
        print(f"Windows Volume Control MCP server is running on {host}:{port}")
        print("Ready to receive commands from Claude")
        
        # Start the server in a thread so we can handle keyboard interrupts
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        # Keep the main thread alive
        try:
            while True:
                threading.Event().wait(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down")
            httpd.shutdown()
            return True
            
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Windows Volume Control MCP Server")
    parser.add_argument('--host', default='localhost', help='Host to bind the server to')
    parser.add_argument('--port', type=int, default=35429, help='Port to bind the server to')
    
    args = parser.parse_args()
    start_server(args.host, args.port) 