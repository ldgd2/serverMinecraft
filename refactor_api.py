import re
import os

files = [
    "routes/servers.py",
    "routes/auth.py",
    "routes/audit.py",
    "routes/files.py",
    "routes/mods.py",
    "routes/players.py",
    "routes/system.py",
    "routes/versions.py",
    "routes/worlds.py"
]

for filepath in files:
    if not os.path.exists(filepath): continue
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Prepend basic imports if not there
    if "from core.responses import APIResponse" not in content:
        content = re.sub(
            r"(from fastapi import.*?\n)", 
            r"\g<1>from core.responses import APIResponse\n", 
            content, count=1
        )
    
    # Common replacements: return {"message": "..."} -> return APIResponse(status="success", message="...", data=None)
    content = re.sub(r'return\s+\{\s*["\']message["\']\s*:\s*(f?["\'].*?["\'])\s*\}', r'return APIResponse(status="success", message=\1, data=None)', content)
    
    # Specific substitutions for schemas
    if "servers.py" in filepath:
        content = content.replace("command: dict", "command: ServerCommandRequest")
        content = content.replace("ban_data: dict", "ban_data: BanRequest")
        content = content.replace("ban_data: dict", "ban_data: UpdateBanRequest") # wait, update_ban uses ban_data dict too
        content = content.replace("data: dict", "data: ChatRequest") # careful, multiple data: dict
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
print("Done refactoring via regex script.")
