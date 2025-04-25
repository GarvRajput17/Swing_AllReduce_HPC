#!/usr/bin/env python3
from Backend.GenAI.NovelGenerator import FinancialNovelGenerator

"""
Launcher script for the Financial Novel application.
"""
import os
import sys
import argparse
import subprocess
import webbrowser
import time

def run_command(cmd, cwd=None):
    """Run a command and return its output"""
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=cwd)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, f"Error: {e.stderr}"

def export_to_web():
    """Export the Ren'Py project to web format"""
    print("Exporting Ren'Py project to web format...")
    success, output = run_command([sys.executable, "web_export.py"])
    print(output)
    return success

def start_web_server(port=5000):
    """Start the web server"""
    print(f"Starting web server on port {port}...")
    # Run in a new process so it doesn't block
    if sys.platform == "win32":
        subprocess.Popen([sys.executable, "web_server.py", "--port", str(port)])
    else:
        subprocess.Popen([sys.executable, "web_server.py", "--port", str(port)], 
                         start_new_session=True)
    
    # Give the server time to start
    time.sleep(2)
    
    # Open the browser
    webbrowser.open(f"http://localhost:{port}")

def generate_story(concept="emergency funds", difficulty="beginner"):
    """Generate a new story"""
    print(f"Generating a new story about {concept} (difficulty: {difficulty})...")
    
    # Import the NovelGenerator
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "Backend"))
    #from Backend/GenAI.NovelGenerator import FinancialNovelGenerator
    
    # Initialize the generator
    generator = FinancialNovelGenerator()
    
    # Set the parameters
    generator.game_state.update({
        "difficulty": difficulty,
        "selected_concept": concept
    })
    
    # Generate the story
    story = generator.generate_story_segment()
    
    # Generate the image
    image_prompts = story.get("image_prompts", story.get("visuals", {}))
    image = generator.generate_image(image_prompts)
    
    # Save the image if it was generated successfully
    if image:
        image_path = generator.save_image(image)
        story["image_path"] = image_path
        
        # Save the updated story data
        generator.save_to_json(story, "latest_story.json")
    
    print("Story generated successfully!")
    return True

def main():
    parser = argparse.ArgumentParser(description="Launch the Financial Novel application")
    parser.add_argument("--export", action="store_true", help="Export the Ren'Py project to web format")
    parser.add_argument("--server", action="store_true", help="Start the web server")
    parser.add_argument("--port", type=int, default=5000, help="Port for the web server")
    parser.add_argument("--generate", action="store_true", help="Generate a new story")
    parser.add_argument("--concept", default="emergency funds", help="Financial concept for the story")
    parser.add_argument("--difficulty", default="beginner", help="Difficulty level (beginner/advanced)")
    
    args = parser.parse_args()
    
    # If no arguments are provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    # Export to web if requested
    if args.export:
        if not export_to_web():
            print("Export failed. Exiting.")
            return
    
    # Generate a story if requested
    if args.generate:
        if not generate_story(args.concept, args.difficulty):
            print("Story generation failed. Exiting.")
            return
    
    # Start the web server if requested
    if args.server:
        start_web_server(args.port)
