#!/usr/bin/env python3
"""
Script to export the Ren'Py project to a web-compatible format.
"""
import os
import subprocess
import shutil
import sys
import argparse
from pathlib import Path

def get_renpy_path():
    """Find the Ren'Py SDK path"""
    # Check common locations
    possible_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "Backend", "renpy"),
        "/usr/share/renpy",
        "C:\\Program Files\\Renpy",
        "C:\\Program Files (x86)\\Renpy",
        os.path.expanduser("~/renpy"),
        os.path.expanduser("~/Applications/renpy"),
        os.path.expanduser("~/Library/Application Support/renpy")
    ]
    
    for path in possible_paths:
        if os.path.exists(path) and os.path.isdir(path):
            launcher_path = os.path.join(path, "launcher")
            if os.path.exists(launcher_path):
                return path
    
    return None

def export_to_web(project_dir, output_dir, renpy_path=None):
    """Export the Ren'Py project to web format"""
    if renpy_path is None:
        renpy_path = get_renpy_path()
        if renpy_path is None:
            print("Error: Could not find Ren'Py SDK. Please specify the path manually.")
            return False
    
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Determine the Ren'Py launcher script
    if sys.platform == "win32":
        renpy_launcher = os.path.join(renpy_path, "renpy.exe")
    else:
        renpy_launcher = os.path.join(renpy_path, "renpy.sh")
    
    # Build the command to export to web
    cmd = [
        renpy_launcher,
        project_dir,
        "web",
        "--dest", output_dir
    ]
    
    try:
        print(f"Exporting project to web format...")
        print(f"Command: {' '.join(cmd)}")
        
        # Run the export command
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("Export completed successfully!")
        print(result.stdout)
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"Error during export: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Export Ren'Py project to web format")
    parser.add_argument("--project", default="FinancialNovel", help="Path to the Ren'Py project directory")
    parser.add_argument("--output", default="web", help="Output directory for the web build")
    parser.add_argument("--renpy", default=None, help="Path to the Ren'Py SDK")
    
    args = parser.parse_args()
    
    # Get absolute paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.join(base_dir, args.project)
    output_dir = os.path.join(base_dir, args.output)
    
    # Export the project
    success = export_to_web(project_dir, output_dir, args.renpy)
    
    if success:
        print(f"Web export completed. Files are in: {output_dir}")
        print("You can now run web_server.py to serve the web build.")
    else:
        print("Web export failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
