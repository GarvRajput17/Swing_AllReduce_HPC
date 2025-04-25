from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys

# Add the parent directory to the path so we can import the NovelGenerator
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from GenAI.NovelGenerator import FinancialNovelGenerator

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/api/generate-story', methods=['POST'])
def generate_story():
    try:
        data = request.json
        
        # Create a new generator
        generator = FinancialNovelGenerator()
        
        # Update game state with request data
        if data:
            generator.game_state.update({
                "difficulty": data.get("difficulty", "beginner"),
                "selected_concept": data.get("concept", "saving vs investing"),
                "characters": data.get("characters", {
                    "protagonist": "Spider-Man",
                    "mentor": "Iron Man",
                    "friend": "MJ"
                })
            })
        
        # Generate story segment
        story = generator.generate_story_segment()
        
        # Generate corresponding image
        image = generator.generate_image(story["image_prompts"])
        
        # Save the image if it was generated successfully
        if image:
            image_path = generator.save_image(image)
            
            # Update the story JSON with the image path
            story["image_path"] = image_path
            
            # Save the updated story data
            generator.save_to_json(story, "story_with_image.json")
        
        return jsonify({
            "success": True,
            "message": "Story generated successfully",
            "story_path": os.path.abspath("output/story_with_image.json")
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error generating story: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
