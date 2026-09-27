"""
Simple HTTP Server for Faymas AI Prompts Gallery
Usage:
    python gallery_server.py --port 8080
"""
import os
import sys
import http.server
import socketserver
import argparse

def run(port=8080, directory="scraped_data"):
    if not os.path.exists(directory):
        directory = "."

    # Ensure index.html exists in directory
    root_index = os.path.join(os.path.dirname(__file__), "index.html")
    target_index = os.path.join(directory, "index.html")
    if os.path.exists(root_index) and not os.path.exists(target_index):
        import shutil
        shutil.copy(root_index, target_index)

    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), CustomHandler) as httpd:
        print(f"==================================================")
        print(f"✨ Faymas AI Gallery Web Server is LIVE!")
        print(f"🌐 Access locally: http://localhost:{port}")
        print(f"🌐 Access publicly: http://YOUR_SERVER_IP:{port}")
        print(f"📁 Serving folder: {os.path.abspath(directory)}")
        print(f"==================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Gallery Web Server")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on (default: 8080)")
    parser.add_argument("--dir", type=str, default="scraped_data", help="Directory to serve")
    args = parser.parse_args()
    run(port=args.port, directory=args.dir)
