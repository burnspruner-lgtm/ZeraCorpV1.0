import os
import shutil
import sys
import subprocess

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
    "scheduler_gateway.py": "src" # Legacy name support
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
        else:
            # Optional: Check if main.py is missing because it was renamed
            if filename == "main.py" and "scheduler_gateway.py" in found_files:
                print("   -> Renaming scheduler_gateway.py to main.py")
                shutil.move(found_files["scheduler_gateway.py"], target_path)

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

if __name__ == "__main__":
    install_flask()
    organize_files()
    run_app()