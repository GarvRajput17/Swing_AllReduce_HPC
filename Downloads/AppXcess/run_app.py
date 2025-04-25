import subprocess
import threading
import time
import webbrowser
import os

def run_flask_api():
    print("Starting Flask API...")
    subprocess.run(["python", "Backend/api.py"])

def run_web_server():
    print("Starting web server...")
    subprocess.run(["python", "web.py"])

if __name__ == "__main__":
    # Start Flask API in a separate thread
    api_thread = threading.Thread(target=run_flask_api)
    api_thread.daemon = True
    api_thread.start()
    
    # Start web server in a separate thread
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()
    
    # Wait a moment for servers to start
    time.sleep(2)
    
    # Open the browser
    webbrowser.open("http://localhost:8000")
    
    print("Application started. Press Ctrl+C to exit.")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
