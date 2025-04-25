#!/usr/bin/env python3
"""
Web server to serve the Monogatari visual novel and provide an API for generating stories.
"""
import os
import sys
import json
import argparse
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import threading
import webbrowser
import time
import uuid
import shutil

# Add the parent directory to the Python path to access Backend
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(base_dir))

# Import the NovelGenerator
from Backend.GenAI.NovelGenerator import FinancialNovelGenerator

app = Flask(__name__, 
            static_folder=os.path.join(base_dir,'web'),
            template_folder=os.path.join(base_dir,'web'))
CORS(app)  # Enable CORS for all routes

# Initialize the generator
generator = FinancialNovelGenerator()

# Store generated stories in memory for quick access
story_cache = {}

@app.route('/')
def index():
    """Serve the main index.html file"""
    return send_from_directory('web', 'index.html')

@app.route('/novel')
def novel():
    """Serve the Monogatari visual novel page"""
    return send_from_directory('web', 'novel.html')

@app.route('/web/<path:path>')
def serve_web_files(path):
    """Serve files from the web directory"""
    return send_from_directory('web', path)

@app.route('/images/<path:path>')
def serve_images(path):
    """Serve generated images"""
    return send_from_directory(os.path.join(base_dir, 'Backend', 'output', 'images'), path)

@app.route('/api/generate', methods=['POST'])
def generate_story():
    try:
        data = request.json
        if data:
            generator.game_state.update({
                "difficulty": data.get("difficulty", "beginner"),
                "selected_concept": data.get("concept", "emergency funds"),
                "user_choices": data.get("choices", []),
                "entertainment_refs": data.get("entertainment", {
                    "netflix_show": "Stranger Things",
                    "spotify_track": "Anti-Hero By Taylor Swift"
                }),
                "characters": data.get("characters", {
                    "protagonist": "Spider-Man",
                    "mentor": "Iron Man",
                    "friend": "MJ"
                })
            })
        
        story = generator.generate_story_segment()
        
        # Create a text prompt from the visuals data
        visuals = story.get("visuals", {})
        prompt = f"""
        Create a Marvel comic-style scene about {generator.game_state['selected_concept']} with:
        - Characters: {', '.join(char['name'] for char in visuals.get('characters', []))}
        - Setting: {visuals.get('financial_elements', 'A financial education scene')}
        - Style: Vibrant Marvel comic book art style
        """
        
        image = generator._generate_image(prompt, "story_cover")
        
        if image:
            image_filename = f"story_image_{uuid.uuid4()}.png"
            backend_image_path = os.path.join('Backend', 'output', 'images', image_filename)
            os.makedirs(os.path.dirname(backend_image_path), exist_ok=True)
            image.save(backend_image_path)
            story["image_path"] = f"/images/{image_filename}"
        
        story_id = str(uuid.uuid4())
        story_cache[story_id] = story
        
        output_dir = os.path.join('Backend', 'output', 'stories')
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, f"{story_id}.json"), 'w', encoding='utf-8') as f:
            json.dump(story, f, indent=2)
        
        return jsonify({
            "success": True,
            "storyId": story_id
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/story/<story_id>')
def get_story(story_id):
    story_data = generator.get_story_with_images(story_id)
    if "error" in story_data:
        return jsonify({"success": False, "error": story_data["error"]})
    return jsonify({"success": True, "story": story_data})

@app.route('/api/latest-story')
def get_latest_story():
    story_data = generator.get_story_with_images()  # No ID means get latest
    if "error" in story_data:
        return jsonify({"success": False, "error": story_data["error"]})
    return jsonify({"success": True, "story": story_data})


def open_browser():
    """Open the web browser after a short delay"""
    time.sleep(1.5)
    webbrowser.open(f"http://localhost:{app.config['PORT']}")

def main():
    parser = argparse.ArgumentParser(description="Serve the Monogatari visual novel")
    parser.add_argument("--port", type=int, default=5000, help="Port to run the server on")
    parser.add_argument("--no-browser", action="store_true", help="Don't open the browser automatically")
    
    args = parser.parse_args()
    
    # Configure the Flask app
    app.config['PORT'] = args.port
    
    # Create necessary directories
    os.makedirs(os.path.join(base_dir, 'Backend', 'output', 'images'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'Backend', 'output', 'images', 'characters'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'Backend', 'output', 'images', 'backgrounds'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'Backend', 'output', 'stories'), exist_ok=True)
    
    # Open the browser automatically unless --no-browser is specified
    if not args.no_browser:
        threading.Thread(target=open_browser).start()
    
    # Run the Flask app
    print(f"Starting server on http://localhost:{args.port}")
    app.run(host='0.0.0.0', port=args.port, debug=False)

if __name__ == "__main__":
    main()
