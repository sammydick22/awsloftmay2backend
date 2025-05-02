#!/usr/bin/env python3
import os
import asyncio
import threading
import argparse

def run_flask_app():
    """Run the Flask app in a separate process."""
    from app import app
    app.run(debug=True, port=5000)

async def run_temporal_server():
    """
    Run a local Temporal server (for development only).
    In production, you would use a dedicated Temporal server/service.
    
    Note: This requires Docker to be installed and running.
    """
    # This example assumes docker-compose is available to start a Temporal server
    # You can also use the Temporal CLI to start a server
    import subprocess
    
    # Use subprocess to run the docker-compose command
    print("Starting Temporal server using Docker...")
    try:
        process = subprocess.Popen(
            ["docker", "run", "--rm", "-p", "7233:7233", "-p", "8233:8233", 
             "--name", "temporal-dev", "temporalio/auto-setup:1.18"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
        # Wait for the server to start
        for line in process.stdout:
            print(line, end="")
            if "temporal-dev-server" in line and "server started" in line:
                print("Temporal server started successfully")
                break
        
        # Keep the server running
        process.wait()
    except KeyboardInterrupt:
        # Gracefully stop the server when the user presses Ctrl+C
        print("Stopping Temporal server...")
        subprocess.run(["docker", "stop", "temporal-dev"])

def main():
    parser = argparse.ArgumentParser(description="Run the Outbound Sales Prospector backend")
    parser.add_argument(
        "--temporal-server", 
        action="store_true", 
        help="Start a local Temporal server (requires Docker)"
    )
    args = parser.parse_args()
    
    # Start the Flask app in a separate thread
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.daemon = True
    flask_thread.start()
    
    if args.temporal_server:
        # Start the Temporal server (blocking call)
        asyncio.run(run_temporal_server())
    else:
        print("Note: Assuming Temporal server is already running.")
        print("If not, start it manually or use --temporal-server flag.")
        
        # Keep the Flask app running
        try:
            flask_thread.join()
        except KeyboardInterrupt:
            print("Shutting down...")

if __name__ == "__main__":
    main()
