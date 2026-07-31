import sys
import os
from PIL import Image, ImageDraw, ImageFont

def text_to_image(text, output_path):
    lines = text.split('\n')
    # Try to load a nice monospaced font available on Windows
    try:
        font = ImageFont.truetype("consola.ttf", 15)
    except IOError:
        try:
            font = ImageFont.truetype("cour.ttf", 15)
        except IOError:
            font = ImageFont.load_default()
            
    # Calculate size based on content
    char_width = 9
    line_height = 22
    max_len = max(len(line) for line in lines)
    width = max(750, max_len * char_width + 40)
    height = len(lines) * line_height + 40
    
    # Create dark-themed image with a subtle border
    image = Image.new("RGB", (width, height), "#1e1e1e")
    draw = ImageDraw.Draw(image)
    
    # Draw text lines
    y = 20
    for line in lines:
        # If line contains green or checkmark, highlight it
        if "✓" in line or "success" in line.lower() or "completed" in line.lower():
            color = "#4ec9b0" # light green/cyan
        elif "error" in line.lower() or "failed" in line.lower() or "✗" in line:
            color = "#f44336" # soft red
        elif "platform" in line.lower() or "cpu" in line.lower() or "ram" in line.lower() or "gpu" in line.lower():
            color = "#569cd6" # light blue
        elif line.startswith("──") or line.startswith("=="):
            color = "#858585" # gray dividers
        else:
            color = "#d4d4d4" # light gray standard text
            
        draw.text((20, y), line, fill=color, font=font)
        y += line_height
        
    # Ensure parent directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    image.save(output_path)
    print(f"Successfully saved text screenshot to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python render_terminal.py <text_file> <output_image_path>")
        sys.exit(1)
        
    text_file = sys.argv[1]
    output_path = sys.argv[2]
    
    with open(text_file, "r", encoding="utf-8") as f:
        text = f.read()
        
    text_to_image(text, output_path)
