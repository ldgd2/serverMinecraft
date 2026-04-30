import re
import os

filepath = "routes/files.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Prepend base imports
if "from core.responses import APIResponse" not in content:
    content = re.sub(
        r"(from fastapi import.*?\n)", 
        r"\g<1>from core.responses import APIResponse\n", 
        content, count=1
    )

def sub_return(pattern, replacement):
    global content
    content = re.sub(pattern, replacement, content)

# General list/dicts
sub_return(r'return (\{\s*"message":\s*(f?["\'].*?["\'])\s*\})', r'return APIResponse(status="success", message=\2, data=None)')
sub_return(r'return (\{\s*"content":\s*content\s*\})', r'return APIResponse(status="success", message="File content retrieved", data=\1)')
sub_return(r'return (\{\s*"results":\s*results\s*\})', r'return APIResponse(status="success", message="Files processed", data=\1)')
sub_return(r'return (\{\s*"message":\s*([^,]+?),\s*"new_path":\s*([^}]+)\s*\})', r'return APIResponse(status="success", message=\2, data={"new_path": \3})')

# Specific returns that are purely variables
content = content.replace("return roots", 'return APIResponse(status="success", message="Roots retrieved", data=roots)')
# list_files
content = content.replace("return file_controller.list_files(server_name, path)", 'return APIResponse(status="success", message="Files listed", data=file_controller.list_files(server_name, path))')

content = re.sub(r'(return \{\s*"root": root_name.*?\}\s*\n)', r'return APIResponse(status="success", message="Directory browsed", data=\1', content, flags=re.DOTALL)
# wait, the regex above is tricky. Let's manually replace the big returns.

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Automated replacements done.")
