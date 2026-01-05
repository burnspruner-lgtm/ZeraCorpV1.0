import os
import re
import shutil
import sys
import ast
import json
import subprocess
from typing import Any
    
# --- DEFINITIVE FILE MAPPING ---
# This map enforces where every file MUST be for the code to work.
FILE_MAPPING = {
    # Core Logic
    "ai_agent.py":          "src/core",
    "tool_executioner.py":  "src/core",
    "config.py":            "src/core",
    "constants.py":         "src/core",
    "utils.py":             "src/core",
    "schema_definitions.py":"src/core",
    "logger_utility.py":    "src/core",
    "system_config.py":     "src/core",

    # AI Components
    "heuristic_engine.py":  "src/ai",
    "ai_chat_parser.py":    "src/ai",
    "generative_ai_client.py":"src/ai",

    # Services
    "db_connector.py":      "src/services",
    "monitoring_service.py":"src/services",
    "external_api_client.py":"src/services",
    "cost_management.py":   "src/services",
    "alert_manager.py":     "src/services",
    "log_analyzer.py":      "src/services",
    "api_interface.py":     "src/services",

    # Machine Learning
    "ml_model.py":          "src/ml",
    "model_training.py":    "src/ml",
    "data_simulator.py":    "src/ml",
    "feature_engineering.py":"src/ml",
    "predictive_algorithms.py":"src/ml",
    "data_loader.py":       "src/ml",

    # Config Files (JSON)
    "ai_knowledge.json":    "src/config",
    "critical_policies.json":"src/config",
    "model_config.json":    "src/config",
    "dynamic_heuristics.json":"src/config",
    
    # Main Entry Point (We enforce it lives in src)
    "main.py":              "src",
    "main.py": "src" # Legacy name support
}

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def get_python_executable():
    """Returns the path to the currently active Python executable."""
    return sys.executable

def organize_files():
    print("🔧 DIAGNOSTIC: Checking file structure...")
    
    # 1. Create Directories & Init Files
    dirs = ["src", "src/core", "src/ai", "src/services", "src/ml", "src/config"]
    for d in dirs:
        path = os.path.join(ROOT_DIR, d)
        os.makedirs(path, exist_ok=True)
        # Create __init__.py in python folders (not config)
        if "config" not in d:
            init_file = os.path.join(path, "__init__.py")
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f: f.write("")

    # 2. Find and Move Files
    # We walk the entire tree to find files wherever they might be hiding
    found_files = {}
    for root, _, files in os.walk(ROOT_DIR):
        if "venv" in root or ".git" in root or "__pycache__" in root: continue
        
        for file in files:
            if file in FILE_MAPPING:
                found_files[file] = os.path.join(root, file)

    # 3. Execute Moves
    for filename, target_folder in FILE_MAPPING.items():
        target_path = os.path.join(ROOT_DIR, target_folder, filename)
        
        # If we found the file somewhere
        if filename in found_files:
            current_path = found_files[filename]
            
            # If it's already in the right place, skip
            if os.path.abspath(current_path) == os.path.abspath(target_path):
                continue
                
            print(f"   -> Moving {filename} to {target_folder}/")
            try:
                shutil.move(current_path, target_path)
            except Exception as e:
                print(f"   ❌ Error moving {filename}: {e}")

def install_flask():
    try:
        import flask
    except ImportError:
        print("📦 Flask not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "flask-cors", "flask-session", "werkzeug"])

def run_app():
    print("🚀 Starting ZeraCorp System...")
    
    # Ensure Root is in Path
    if ROOT_DIR not in sys.path:
        sys.path.insert(0, ROOT_DIR)

    try:
        from src.main import app, init_system, start_threads
        init_system()
        start_threads()
        app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
    except ImportError as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        print("   Logic mismatch. Please check src/main.py imports match the folder structure.")
    except Exception as e:
        print(f"\n❌ RUNTIME ERROR: {e}")

def check_system_integrity(root_dir):
    print("🔍 INITIATING ZERACORP SYSTEM INTEGRITY CHECK...")
    
    # 1. Map all existing files
    inventory = {"py": [], "web": [], "json": [], "assets": []}
    all_file_paths = {}

    for root, dirs, files in os.walk(root_dir):
        if any(x in root for x in [".venv", "__pycache__", ".git"]): continue
        for file in files:
            path = os.path.join(root, file)
            all_file_paths[file] = path
            if file.endswith('.py'): inventory["py"].append(file)
            elif file.endswith(('.html', '.js')): inventory["web"].append(file)
            elif file.endswith('.json'): inventory["json"].append(file)
            elif file.endswith(('.css', '.ico', '.png')): inventory["assets"].append(file)
                
    print(f"📦 System Scan Complete: Found {len(all_file_paths)} total files.")

    # 2. Analyze each file for "Broken Links"
    errors = 0
    for filename in inventory["py"]:
        filepath = all_file_paths[filename]
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError as e:
                print(f"❌ SYNTAX ERROR in {filename}: {e}")
                errors += 1

            # Check every import in the file
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    # Initialize module_name to avoid UnboundLocalError
                    module_name = ""
                    if isinstance(node, ast.Import):
                        module_name = node.names[0].name
                    else:
                        module_name = node.module or ""
            
            # 404 ERROR CHECK: Ensure static files are in the right spot
            static_path = os.path.join(root_dir, "web", "static")
            for s_file in ["styles.css", "favicon.ico"]:
                if not os.path.exists(os.path.join(static_path, s_file)):
                    print(f"⚠️  404 RISK: {s_file} is not in {static_path}!")
   
    # 2b. GUI INTEGRITY: Check HTML for Broken Asset Links
    print("🎨 ANALYZING GUI STRUCTURE...")
    template_path = os.path.join(root_dir, "web", "templates")
    if os.path.exists(template_path):
        for html_file in os.listdir(template_path):
            if html_file.endswith(".html"):
                with open(os.path.join(template_path, html_file), "r") as hf:
                    content = hf.read()
                    # Check if HTML mentions assets that don't exist in inventory
                    for asset in ["styles.css", "favicon.ico", "app.js"]:
                        if asset in content and asset not in inventory["web"]: # and asset not in inventory["data"]:
                            print(f"⚠️  GUI BREAKAGE: {html_file} references {asset}, but it's missing from web/static!")
                            errors += 1
              
    # 2c. CROSS-RELATIONSHIP ANALYSIS
    # Check if GUI (HTML) has its Assets (CSS/JS)
    for html in inventory["web"]:
        if html.endswith(".html"):
            with open(all_file_paths[html], "r", encoding="utf-8") as f:
                content = f.read()
                for asset in inventory["assets"] + inventory["web"]:
                    if asset in content and asset not in all_file_paths:
                        print(f"⚠️  LINKAGE ERROR: {html} requires {asset}, but path is broken!")
                        errors += 1

    # Check if Logic (Python) has its Knowledge (JSON)
    for py_file in inventory["py"]:
        with open(all_file_paths[py_file], "r", encoding="utf-8") as f:
            content = f.read()
            if ".json" in content:
                for j_file in inventory["json"]:
                    if j_file in content and j_file not in inventory["json"]:
                        print(f"⚠️  DATA GHOST: {py_file} references {j_file}, but file is missing!")
                        errors += 1
    
    intended_relations = []
    # Regex to find anything that looks like a file path or module import
    pattern = re.compile(r'[\'"]([a-zA-Z0-9_\-/]+\.(py|json|html|css|js))[\'"]|from\s+([a-zA-Z0-9_\.]+)\s+import')

    for filename, filepath in all_file_paths.items():
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            matches = pattern.findall(content)
            for m in matches:
                # Clean up the match and add to our relation map
                target = m[0] or m[2]
                if target:
                    intended_relations.append({"source": filename, "target": target})

    # 2. OUTPUT TO "GUI" (Visual Tree in Console)
    print("\n🕸️  SYSTEM RELATIONSHIP MAP (NEURAL NETWORK)")
    print("="*50)
    for rel in intended_relations:
        status = "✅ CONNECTED" if (rel["target"] in all_file_paths or rel["target"].replace('.', '/') in str(all_file_paths)) else "❌ BROKEN"
        print(f"🔗 {rel['source']}  ----{status}---->  {rel['target']}")
              
    # 3. Check for the specific "security_protocols" requirement
    knowledge_path = os.path.join(root_dir, "src", "config", "ai_knowledge.json")
    if os.path.exists(knowledge_path):
        import json
        with open(knowledge_path, "r") as kj:
            data = json.load(kj)
            if "security_protocols" not in data:
                print("⚠️  MISSING DATA: 'security_protocols' key not found in ai_knowledge.json. AI Agent will fail.")
                errors += 1
    else:
        print("❌ CRITICAL: ai_knowledge.json is missing entirely!")
        errors += 1

    if errors == 0:
        print("✅ INTEGRITY SECURED: All files are connected and logically sound.")
        return True
    else:
        print(f"❌ INTEGRITY FAILED: Found {errors} issues that need healing.")
        return False 

if __name__ == "__main__":
    organize_files()
    install_flask() 
    if check_system_integrity(ROOT_DIR):
        run_app()
    else:
        print("🛑 SYSTEM HALTED: Integrity check failed. Please fix errors above.")