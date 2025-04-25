import os
import json
import io
import datetime
import mimetypes
import random
from PIL import Image
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables and configure API
load_dotenv()
API_KEY = os.getenv("GEMINI_API")

# Set the base directory to an absolute path
base_dir = "/Users/garvrajput/Downloads/AppXcess"  # Adjust this to your actual path


class FinancialNovelGenerator:
    def __init__(self):
        self.game_state = {
            "difficulty": "beginner",
            "selected_concept": "emergency funds",
            "entertainment_refs": {
                "netflix_show": "Stranger Things",
                "spotify_track": "Anti-Hero By Taylor Swift"
            },
            "characters": {
                "protagonist": "Spider-Man",
                "mentor": "Iron Man",
                "friend": "MJ"
            }
        }
        # Initialize client
        self.client = genai.Client(api_key=API_KEY)
        
        # Create directories for assets
        self.create_asset_directories()

    def create_asset_directories(self):
        """Create directories for storing generated assets"""
        dirs = [
            os.path.join(base_dir, "output", "stories"),
            os.path.join(base_dir, "output", "images", "characters"),
            os.path.join(base_dir, "output", "images", "backgrounds"),
            os.path.join(base_dir, "output", "temp")
        ]
        
        for directory in dirs:
            if not os.path.exists(directory):
                os.makedirs(directory)

    def generate_story_segment(self):
        prompt_template = f"""
        Generate a Marvel financial literacy story segment as JSON with these parameters:
        - Difficulty: {self.game_state['difficulty']}
        - Concept: {self.game_state['selected_concept']}
        - Characters: {self.game_state['characters']['protagonist']} (protagonist), {self.game_state['characters']['mentor']} (mentor), {self.game_state['characters']['friend']} (friend)
        
        The visual novel should be rich in terms of the learning outcome expected according to the age group targeted.
        Include detailed descriptions for character appearances and backgrounds that can be used to generate images.

        Follow this structure exactly and return valid JSON:
        {{
            "plot": {{
                "title": "Web of Finance",
                "setup": "{self.game_state['characters']['protagonist']} needs to {{financial_goal}} while fighting {{villain}}",
                "location": "Marvel NYC location with financial elements"
            }},
            "dialogue": [
                {{
                    "character": "{self.game_state['characters']['mentor']}",
                    "text": "Financial advice using tech analogy",
                    "hint": "Explain {self.game_state['selected_concept']} using Avengers example"
                }},
                {{
                    "character": "{self.game_state['characters']['friend']}",
                    "text": "Real-world pressure scenario"
                }}
            ],
            "visuals": {{
                "characters": [
                    {{
                        "name": "{self.game_state['characters']['protagonist']}",
                        "description": "Detailed description for character visualization"
                    }},
                    {{
                        "name": "{self.game_state['characters']['mentor']}",
                        "description": "Detailed description for character visualization"
                    }},
                    {{
                        "name": "{self.game_state['characters']['friend']}",
                        "description": "Detailed description for character visualization"
                    }}
                ],
                "backgrounds": [
                    {{
                        "name": "Main location",
                        "description": "Detailed description of the main background scene"
                    }},
                    {{
                        "name": "Secondary location",
                        "description": "Detailed description of another background scene"
                    }}
                ],
                "financial_elements": "Creative visualization of {self.game_state['selected_concept']}"
            }},
            "hooks": {{
                "pop_culture": "{self.game_state['entertainment_refs']['netflix_show']} reference",
                "music": "{self.game_state['entertainment_refs']['spotify_track']} theme"
            }}
        }}
        """

        # Generate the story
        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt_template,
            )
            
            # Extract the text from the response
            response_text = response.text
            
            story_data = self._parse_response(response_text)

            # Save to JSON file
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"story_segment_{timestamp}.json"
            json_path = self.save_to_json(story_data, filename)
            
            # Store the JSON file path in the story data
            story_data["_json_file"] = json_path
            
            # Generate all the necessary images for the story
            self.generate_all_images_for_story(story_data)
            
            return story_data
        except Exception as e:
            print(f"Error generating story: {e}")
            import traceback
            traceback.print_exc()
            return {
                "plot": {"title": "Error", "setup": "Error generating story"},
                "dialogue": [],
                "visuals": {}
            }
        
    def save_frontend_story(self, story_data, story_id):
        """Save the frontend-formatted story JSON"""
        # Create frontend stories directory
        frontend_stories_dir = os.path.join(base_dir, "output", "frontend_stories")
        os.makedirs(frontend_stories_dir, exist_ok=True)
        
        # Format the story for frontend
        frontend_story = self.format_story_for_frontend(story_data)
        
        # Save with the same ID as the original story
        frontend_filename = f"frontend_story_{story_id}.json"
        filepath = os.path.join(frontend_stories_dir, frontend_filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(frontend_story, f, indent=2)
        
        print(f"Frontend story saved to {filepath}")
        return filepath

    def generate_all_images_for_story(self, story_data):
        """Generate character and background images for the visual novel (up to 5 of each)"""
        image_paths = {
            "characters": {},
            "backgrounds": {}
        }

        # Generate cover images
        cover_image = self.generate_story_cover(story_data)
        if cover_image:
            cover_filename = f"cover_{os.path.basename(story_data['_json_file']).replace('.json', '.png')}"
            cover_path = self.save_image(cover_image, os.path.join("covers", cover_filename))
            image_paths["cover"] = cover_path
        
        story_data["generated_images"] = image_paths
        
        # Generate character images
        if "visuals" in story_data and "characters" in story_data["visuals"]:
            characters = story_data["visuals"]["characters"]
            for character in characters[:5]:
                character_name = character.get("name", "Unknown")
                character_desc = character.get("description", "A Marvel character")
                print(f"Generating image for character: {character_name}")
                character_image = self.generate_character_image(character_name, character_desc)
                if character_image:
                    filename = f"{character_name.replace(' ', '_').lower()}.png"
                    filepath = self.save_image(character_image, os.path.join("characters", filename))
                    image_paths["characters"][character_name] = filepath
        
        # Generate background images
        if "visuals" in story_data and "backgrounds" in story_data["visuals"]:
            backgrounds = story_data["visuals"]["backgrounds"]
            for bg in backgrounds[:5]:
                bg_name = bg.get("name", "background")
                bg_desc = bg.get("description", "A Marvel-style background")
                print(f"Generating background: {bg_name}")
                bg_image = self.generate_background_image(bg_name, bg_desc)
                if bg_image:
                    filename = f"{bg_name.replace(' ', '_').lower()}.png"
                    filepath = self.save_image(bg_image, os.path.join("backgrounds", filename))
                    image_paths["backgrounds"][bg_name] = filepath
        
        # Save the image paths to the story data
        story_data["generated_images"] = image_paths
        
        # Update the JSON file with the image paths
        if "_json_file" in story_data:
            self.save_to_json(story_data, os.path.basename(story_data["_json_file"]))
            
            # Now that we have all images, save the frontend version
            timestamp = os.path.basename(story_data["_json_file"]).replace("story_segment_", "").replace(".json", "")
            frontend_path = self.save_frontend_story(story_data, timestamp)
            story_data["_frontend_file"] = frontend_path
        else:
            self.save_to_json(story_data, "updated_story.json")
        
        return image_paths


    def save_binary_file(self, file_name, data):
        """Save binary data to a file"""
        with open(file_name, "wb") as f:
            f.write(data)
        
        return file_name

    def generate_character_image(self, character_name, character_description):
        """Generate an image for a specific character"""
        prompt = f"""
        Create a Marvel comic-style portrait of {character_name} with these specifications:
        
        - Character: {character_name}
        - Description: {character_description}
        - Style: Vibrant Marvel comic book art style with bold outlines
        - Pose: Heroic, dynamic pose showing character's personality
        - Background: Simple, gradient background that highlights the character
        - Financial theme: Subtle elements related to {self.game_state['selected_concept']} in the design
        
        The image should be a high-quality character portrait suitable for a visual novel about financial literacy.
        """
        
        return self._generate_image(prompt, f"character_{character_name}")

    def generate_background_image(self, bg_name, bg_description):
        """Generate a background image"""
        prompt = f"""
        Create a Marvel comic-style background scene with these specifications:
        
        - Scene name: {bg_name}
        - Description: {bg_description}
        - Style: Vibrant Marvel comic book art style with detailed environment
        - Financial elements: Subtle integration of {self.game_state['selected_concept']} concepts
        - Mood: Appropriate for a financial education story
        - Easter eggs: Small {self.game_state['entertainment_refs']['netflix_show']} reference hidden somewhere
        
        The image should be a detailed background scene without characters, suitable for a visual novel about financial literacy.
        """
        
        return self._generate_image(prompt, f"background_{bg_name}")

    def _generate_image(self, prompt, image_type):
        """Core image generation function"""
        print(f"Generating {image_type}")

        if image_type == "story_cover":
            prompt = f"""
            Create a Marvel comic-style cover image with these specifications:
            - Style: Dynamic comic book cover art with bold colors
            - Scene: Spider-Man and Iron Man discussing finances on a rooftop
            - Elements: Include financial symbols (graphs, charts) integrated naturally
            - Theme: {self.game_state['selected_concept']}
            - Mood: Educational but exciting
            The image should be a high-quality comic book cover suitable for a financial education story.
            """
        
        try:
            model = "gemini-2.0-flash-exp-image-generation"
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=prompt),
                    ],
                ),
            ]
            generate_content_config = types.GenerateContentConfig(
                temperature=1,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
                response_modalities=["image", "text"],
            )

            # Use streaming to get the image
            for chunk in self.client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                if not chunk.candidates or not chunk.candidates[0].content or not chunk.candidates[0].content.parts:
                    continue
                
                if chunk.candidates[0].content.parts[0].inline_data:
                    inline_data = chunk.candidates[0].content.parts[0].inline_data
                    file_extension = mimetypes.guess_extension(inline_data.mime_type)
                    file_name = f"temp_{image_type}_{random.randint(1000, 9999)}{file_extension}"
                    
                    # Create a temporary directory if it doesn't exist
                    temp_dir = os.path.join(base_dir, "output", "temp")
                    if not os.path.exists(temp_dir):
                        os.makedirs(temp_dir)
                    
                    # Save the binary file temporarily
                    temp_path = os.path.join(temp_dir, file_name)
                    self.save_binary_file(temp_path, inline_data.data)
                    print(f"Image generated and saved temporarily as {temp_path}")
                    
                    # Open the image with PIL and return it
                    image = Image.open(temp_path)
                    
                    return image
                else:
                    print(f"Text response (no image): {chunk.text if hasattr(chunk, 'text') else 'No text'}")
            
            print(f"No image generated for {image_type}.")
            return None
            
        except Exception as e:
            print(f"Error generating {image_type} image: {e}")
            import traceback
            traceback.print_exc()
            return None

    def generate_story_cover(self, story_data):
        """Generate a cover image for the story"""
        prompt = f"""
        Create a Marvel comic-style cover illustration with these specifications:
        - Style: Bold, dynamic comic book cover art with vibrant colors
        - Main Focus: {story_data['plot']['title']}
        - Characters: {story_data['visuals']['characters'][0]['name']} in dynamic pose
        - Setting: {story_data['plot']['location']}
        - Financial Theme: Clear visual representation of {self.game_state['selected_concept']}
        
        Make it a striking, high-quality comic book cover that captures the story's financial education theme.
        """
        return self._generate_image(prompt, "story_cover")


    def _parse_response(self, response_text):
        try:
            # First attempt: direct JSON parsing
            return json.loads(response_text)
        except json.JSONDecodeError:
            print("Error parsing JSON response. Attempting cleanup...")
            try:
                # Second attempt: remove markdown code blocks
                cleaned = response_text.replace('```json', '').replace('```', '').strip()
                return json.loads(cleaned)
            except json.JSONDecodeError:
                # Third attempt: more aggressive cleanup
                print("Still having issues. Performing deeper cleanup...")
                lines = cleaned.split('\n')
                cleaned_lines = [line for line in lines if line.strip()]
                cleaned_text = ' '.join(cleaned_lines)
                
                # Look for JSON content between curly braces
                start_idx = cleaned_text.find('{')
                end_idx = cleaned_text.rfind('}') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_content = cleaned_text[start_idx:end_idx]
                    return json.loads(json_content)
                
                # If all else fails, return a basic structure
                print("Failed to parse JSON. Returning default structure.")
                return {
                    "plot": {"title": "Parsing Error", "setup": "Error in story generation"},
                    "dialogue": [],
                    "visuals": {"characters": [], "backgrounds": []}
                }

    def save_to_json(self, data, filename):
        """Save data to a JSON file"""
        output_dir = os.path.join(base_dir, "output", "stories")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"Story saved to {filepath}")
        return filepath

    def save_image(self, image, filepath_relative):
        """Save PIL Image to file with relative path"""
        if image is None:
            print("No image to save")
            return None
        
        # Determine the full path
        output_dir = os.path.join(base_dir, "output", "images")
        full_path = os.path.join(output_dir, filepath_relative)
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Save the image
        image.save(full_path)
        print(f"Image saved to {full_path}")
        
        # Return the relative path for storing in JSON
        return filepath_relative

    def get_story_with_images(self, story_id=None):
        """Get a story with all its generated images and frontend format"""
        story_data = self._load_story(story_id)  # Extract existing loading logic to private method
        
        if "error" in story_data:
            return story_data
        
        # Add the frontend-formatted version
        story_data["frontend_format"] = self.format_story_for_frontend(story_data)
        
        return story_data


    def update_game_state(self, new_state):
        """Update the game state with new values"""
        for key, value in new_state.items():
            if key in self.game_state:
                if isinstance(value, dict) and isinstance(self.game_state[key], dict):
                    # Merge dictionaries for nested values
                    self.game_state[key].update(value)
                else:
                    # Replace the value
                    self.game_state[key] = value
        
        print(f"Game state updated: {self.game_state}")
        return self.game_state

    def list_available_stories(self):
        """List all available stories"""
        stories_dir = os.path.join(base_dir, "output", "stories")
        if not os.path.exists(stories_dir):
            return {"error": "No stories directory found"}
        
        # Get all JSON files in the stories directory
        json_files = [f for f in os.listdir(stories_dir) if f.endswith('.json')]
        
        if not json_files:
            return {"error": "No stories found"}
        
        # Sort by filename (which includes timestamp) to get newest first
        json_files.sort(reverse=True)
        
        stories = []
        for file in json_files:
            try:
                with open(os.path.join(stories_dir, file), 'r', encoding='utf-8') as f:
                    story_data = json.load(f)
                
                # Extract basic info
                story_info = {
                    "story_id": file.replace(".json", ""),
                    "title": story_data.get("plot", {}).get("title", "Untitled"),
                    "concept": self.game_state["selected_concept"],
                    "timestamp": file.split("_")[-1].replace(".json", "")
                }
                stories.append(story_info)
            except Exception as e:
                print(f"Error loading story {file}: {e}")
        
        return {"stories": stories}
    
    def format_story_for_frontend(self, story_data):
        """Transform the story data into a frontend-friendly format with dialogue-specific images"""
        
        formatted_story = {
            "plot": story_data["plot"],
            "dialogue_scenes": []
        }
        
        # Get the background images
        backgrounds = story_data.get("generated_images", {}).get("backgrounds", {})
        character_images = story_data.get("generated_images", {}).get("characters", {})
        
        # Create a scene for each dialogue entry
        for i, dialogue in enumerate(story_data.get("dialogue", [])):
            # Determine which background to use based on dialogue position
            bg_keys = list(backgrounds.keys())
            background_image = None
            if bg_keys:
                # Use first background for first half of dialogue, second for rest
                bg_index = min(i // (len(story_data["dialogue"]) // 2 + 1), len(bg_keys) - 1)
                background_image = backgrounds[bg_keys[bg_index]]
            
            # Get the character's image
            character_name = dialogue["character"]
            character_image = character_images.get(character_name)
            
            # Create the scene object
            scene = {
                "dialogue": dialogue,
                "background_image": background_image,
                "character_image": character_image
            }
            
            formatted_story["dialogue_scenes"].append(scene)
        
        return formatted_story


