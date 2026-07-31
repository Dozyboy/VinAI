import os
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def get_tree_string(root: Path, max_depth: int = 4) -> str:
    lines = []
    
    def walk(path: Path, prefix: str = "", depth: int = 1):
        if depth > max_depth:
            return
        
        # Sort files and directories
        try:
            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
        except Exception:
            return
        
        # We want to skip listing too many files in events_smallfiles _delta_log
        is_events_log = "events_smallfiles" in path.parts and "_delta_log" in path.name
        
        filtered_items = []
        if is_events_log:
            jsons = [x for x in items if x.suffix == ".json"]
            checkpoints = [x for x in items if ".checkpoint" in x.name]
            last_checkpoint = [x for x in items if x.name == "_last_checkpoint"]
            
            # Keep only a few JSONs
            if len(jsons) > 4:
                filtered_items.extend(jsons[:2])
                # Add a dummy path object to represent ellipsis
                ellipsis_path = path / "... (200+ JSON log files) ..."
                filtered_items.append(ellipsis_path)
                filtered_items.extend(jsons[-2:])
            else:
                filtered_items.extend(jsons)
            filtered_items.extend(checkpoints)
            filtered_items.extend(last_checkpoint)
        else:
            # General case: if there are more than 10 files in a directory, summarize
            files = [x for x in items if x.is_file()]
            dirs = [x for x in items if x.is_dir()]
            if len(files) > 6:
                filtered_items.extend(dirs)
                filtered_items.extend(files[:2])
                ellipsis_path = path / f"... ({len(files) - 4} parquet files) ..."
                filtered_items.append(ellipsis_path)
                filtered_items.extend(files[-2:])
            else:
                filtered_items.extend(items)

        for i, item in enumerate(filtered_items):
            is_last = (i == len(filtered_items) - 1)
            connector = "└── " if is_last else "├── "
            
            # Handle the dummy ellipsis item
            if "... (" in item.name:
                lines.append(f"{prefix}{connector}{item.name}")
                continue
                
            lines.append(f"{prefix}{connector}{item.name}")
            
            if item.is_dir():
                new_prefix = prefix + ("    " if is_last else "│   ")
                walk(item, new_prefix, depth + 1)
                
    lines.append(root.name)
    walk(root)
    return "\n".join(lines)

def main():
    workspace = Path(__file__).resolve().parents[1]
    lakehouse_dir = workspace / "_lakehouse"
    screenshots_dir = workspace / "submission" / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Get Tree String
    tree_str = get_tree_string(lakehouse_dir)
    
    # 2. Get JSON log content
    json_path = lakehouse_dir / "scratch" / "users_delta" / "_delta_log" / "00000000000000000000.json"
    json_lines = []
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            for line in f:
                # Pretty print each line of Delta log (each line is a separate JSON object)
                try:
                    obj = json.loads(line.strip())
                    json_lines.append(json.dumps(obj, indent=2))
                except Exception:
                    json_lines.append(line.strip())
    json_str = "\n\n".join(json_lines)
    
    # 3. Render Image
    width, height = 1400, 950
    bg_color = (30, 30, 30)      # Dark slate background
    text_color = (220, 220, 220)  # Off-white code text
    accent_color = (0, 180, 216)  # Bright blue accent
    
    image = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(image)
    
    # Try to load a clean monospace font
    try:
        font = ImageFont.truetype("consola.ttf", 15)
        title_font = ImageFont.truetype("consolab.ttf", 18)
    except Exception:
        font = ImageFont.load_default()
        title_font = font
        
    # Draw title
    draw.text((30, 25), "DAY 18 LAKEHOUSE LAB - DELIVERABLES", font=title_font, fill=accent_color)
    draw.line((30, 55, width - 30, 55), fill=(80, 80, 80), width=2)
    
    # Draw left section: Directory Tree
    draw.text((30, 75), "Terminal: tree _lakehouse/", font=title_font, fill=accent_color)
    draw.text((30, 115), tree_str, font=font, fill=text_color)
    
    # Draw division line
    draw.line((650, 75, 650, height - 30), fill=(80, 80, 80), width=1)
    
    # Draw right section: Transaction Log Content
    draw.text((680, 75), "Transaction Log: _delta_log/00000000000000000000.json", font=title_font, fill=accent_color)
    draw.text((680, 115), json_str, font=font, fill=text_color)
    
    # Save Image
    output_image = screenshots_dir / "lakehouse_tree_and_json.png"
    image.save(output_image)
    print(f"Successfully generated screenshot: {output_image}")

if __name__ == "__main__":
    main()
