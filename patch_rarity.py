import os
import re
import random

catalog_dir = r'C:\Users\ldgd2\OneDrive\Documentos\Proyectos_lider\python\minecraft_server_manager\server\app\services\achievements\catalog'

def calculate_rarity(name, desc, req_str):
    rarity = 0.10
    
    # Check numbers in requirements
    nums = [int(n) for n in re.findall(r'\d+', req_str)]
    max_num = max(nums) if nums else 0
    
    if max_num >= 1000000: rarity = 0.99
    elif max_num >= 100000: rarity = 0.95
    elif max_num >= 10000: rarity = 0.85
    elif max_num >= 1000: rarity = 0.65
    elif max_num >= 100: rarity = 0.40
    
    # Text heuristics
    text = (name + desc).lower()
    if 'muere' in text or 'death' in text or 'kill' in text: rarity = max(rarity, 0.50)
    if 'warden' in text or 'dragon' in text or 'wither' in text: rarity = max(rarity, 0.85)
    if 'meme' in name.lower() or 'philo' in name.lower(): rarity = max(rarity, 0.70)
    
    # Add some randomness to avoid all being exactly the same
    rarity += random.uniform(-0.05, 0.05)
    rarity = min(max(rarity, 0.01), 1.0)
    
    # Return formatted to 2 decimals
    return f"{rarity:.2f}"

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find AchievementDefinition(..., {req})
    # We will use regex to find the end of the AchievementDefinition call and insert rarity
    # It might be multiline.
    lines = content.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        if 'AchievementDefinition(' in line and 'rarity=' not in line:
            # Simple single-line patch
            if line.strip().endswith('),') or line.strip().endswith(')'):
                match = re.search(r'(\{.*?\})', line)
                req_str = match.group(1) if match else "{}"
                rarity_val = calculate_rarity(line, line, req_str)
                
                if line.endswith(','):
                    line = line[:-2] + f", rarity={rarity_val}),"
                else:
                    line = line[:-1] + f", rarity={rarity_val})"
        new_lines.append(line)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

for filename in os.listdir(catalog_dir):
    if filename.endswith('.py'):
        process_file(os.path.join(catalog_dir, filename))

print("Rarity patched successfully.")
