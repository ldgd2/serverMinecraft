import os
import ast

def extract_events():
    catalog_dir = r"c:\Users\ldgd2\OneDrive\Documentos\Proyectos_lider\python\minecraft_server_manager\server\app\services\achievements\catalog"
    events = set()
    for root, _, files in os.walk(catalog_dir):
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call):
                            if getattr(node.func, 'id', None) == 'AchievementDefinition':
                                if len(node.args) >= 5:
                                    req_dict = node.args[4]
                                    if isinstance(req_dict, ast.Dict):
                                        for key in req_dict.keys:
                                            if isinstance(key, ast.Constant):
                                                events.add(key.value)
    print("\n".join(sorted(events)))

if __name__ == '__main__':
    extract_events()
