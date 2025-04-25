#!/usr/bin/env python3
"""
Create placeholder images for characters and backgrounds
"""
import os
from PIL import Image, ImageDraw, ImageFont

def create_placeholder(path, width, height, color, text=None):
    """Create a placeholder image"""
    # Ensure directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # Create image
    img = Image.new('RGB', (width, height), color=color)
    d = ImageDraw.Draw(img)
    
    # Add border
    d.rectangle([(0, 0), (width-1, height-1)], outline=(255, 255, 255))
    
    # Add text if provided
    if text:
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            font = ImageFont.load_default()
        
        # Calculate text position - using the newer textbbox method instead of textsize
        if hasattr(d, 'textbbox'):
            # For newer Pillow versions
            bbox = d.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            # Fallback for older Pillow versions
            text_width, text_height = d.textsize(text, font=font)
            
        position = ((width - text_width) // 2, (height - text_height) // 2)
        
        # Draw text
        d.text(position, text, fill=(255, 255, 255), font=font)
    
    # Save image
    img.save(path)
    print(f"Created placeholder image: {path}")

def main():
    # Get the base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create character placeholders
    characters = ["spider_man", "iron_man", "mj"]
    for character in characters:
        path = os.path.join(base_dir, "output", "images", "characters", f"{character}.png")
        create_placeholder(path, 200, 400, (73, 109, 137), character)
    
    # Create background placeholders
    backgrounds = ["nyc", "stark_tower", "daily_bugle"]
    for background in backgrounds:
        path = os.path.join(base_dir, "output", "images", "backgrounds", f"{background}.jpg")
        create_placeholder(path, 800, 600, (50, 50, 50), background)
    
    # Create a web directory for Monogatari assets if it doesn't exist
    web_dir = os.path.join(base_dir, "web", "images")
    os.makedirs(os.path.join(web_dir, "characters"), exist_ok=True)
    os.makedirs(os.path.join(web_dir, "backgrounds"), exist_ok=True)
    
    # Copy the images to the web directory
    for character in characters:
        src = os.path.join(base_dir, "output", "images", "characters", f"{character}.png")
        dst = os.path.join(web_dir, "characters", f"{character}.png")
        img = Image.open(src)
        img.save(dst)
        print(f"Copied to web directory: {dst}")
    
    for background in backgrounds:
        src = os.path.join(base_dir, "output", "images", "backgrounds", f"{background}.jpg")
        dst = os.path.join(web_dir, "backgrounds", f"{background}.jpg")
        img = Image.open(src)
        img.save(dst)
        print(f"Copied to web directory: {dst}")

if __name__ == "__main__":
    main()
