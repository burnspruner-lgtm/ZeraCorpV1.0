import os
import shutil

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Define the Perfect Structure
STRUCTURE = {
    # Core Application Code
    "src": ["main.py", "scheduler_gateway.py", "wsgi.py"],
    
    # Logic Modules
    "src/core": [
        "ai_agent.py", "tool_executioner.py", "config.py", 
        "constants.py", "utils.py", "schema_definitions.py", 
        "logger_utility.py", "system_config.py"
    ],
    "src/ai": [
        "heuristic_engine.py", "ai_chat_parser.py", "generative_ai_client.py"
    ],
    "src/services": [
        "db_connector.py", "monitoring_service.py", "external_api_client.py",
        "cost_management.py", "alert_manager.py", "log_analyzer.py", "api_interface.py"
    ],
    "src/ml": [
        "ml_model.py", "model_training.py", "data_simulator.py",
        "feature_engineering.py", "predictive_algorithms.py", "data_loader.py"
    ],
    
    # Configuration & Data
    "src/config": [
        "ai_knowledge.json", "critical_policies.json", 
        "model_config.json", "dynamic_heuristics.json", "simulated_model_v1.json"
    ],
    
    # Documentation & Meta
    "docs": ["README.md", "api_docs.md", "LICENSE"],
    
    # Deployment Configs (Keep in Root, but list here to track them)
    ".": ["Procfile", "requirements.txt", "run_system.py", ".gitignore"],
    
    # Web Assets
    "web/templates": ["index.html", "dashboard.html"],
    "web/static": ["styles.css", "main.js", "dekut-logo-simulated.png", "favicon.ico"]
}

# 2. Files to DELETE (Cleanup)
TRASH_LIST = [
    "fix_and_run.py", "fix_paths.py", "init_packages.py", 
    "organize_web.py", "import os.py", "restore_files.py", "launcher.py"
]

def flatten_and_organize():
    print(f"🧹 Cleaning up ZeraCorp Directory: {ROOT_DIR}")
    
    # Step A: Flatten everything to root first (Recover lost files)
    print("   ... Recovering files from subfolders ...")
    for dirpath, _, filenames in os.walk(ROOT_DIR):
        if dirpath == ROOT_DIR: continue
        if any(x in dirpath for x in [".git", ".venv", "venv", "__pycache__"]): continue
        
        for filename in filenames:
            src = os.path.join(dirpath, filename)
            dst = os.path.join(ROOT_DIR, filename)
            if not os.path.exists(dst):
                try: shutil.move(src, dst)
                except: pass

    # Step B: Remove Empty Folders
    print("   ... Removing empty directories ...")
    for dirpath, _, _ in os.walk(ROOT_DIR, topdown=False):
        if dirpath != ROOT_DIR and not os.listdir(dirpath):
            try: os.rmdir(dirpath)
            except: pass

    # Step C: Create Structure & Move Files
    print("   ... Building correct architecture ...")
    for folder, files in STRUCTURE.items():
        if folder == ".": continue # Skip root files
        
        target_dir = os.path.join(ROOT_DIR, folder)
        os.makedirs(target_dir, exist_ok=True)
        
        # Create __init__.py if it's a source folder
        if "src" in folder and "config" not in folder:
            init_path = os.path.join(target_dir, "__init__.py")
            if not os.path.exists(init_path):
                with open(init_path, 'w') as f: f.write("")

        for filename in files:
            src = os.path.join(ROOT_DIR, filename)
            dst = os.path.join(target_dir, filename)
            if os.path.exists(src):
                try: 
                    shutil.move(src, dst)
                    print(f"   ✅ Organized: {filename} -> {folder}/")
                except Exception as e: print(f"   ❌ Error moving {filename}: {e}")

    # Step D: Delete Trash
    print("   ... Deleting temporary scripts ...")
    for item in TRASH_LIST:
        path = os.path.join(ROOT_DIR, item)
        if os.path.exists(path):
            try: 
                os.remove(path)
                print(f"   🗑️  Deleted: {item}")
            except: pass
            
    # Step E: Clean Flask Session Files
    for filename in os.listdir(ROOT_DIR):
        if len(filename) == 32 and "." not in filename: # Heuristic for session files
            try: os.remove(os.path.join(ROOT_DIR, filename))
            except: pass

if __name__ == "__main__":
    flatten_and_organize()
    print("\n✨ ZeraCorp System Cleaned & Organized.")
    print("👉 Run 'python run_system.py' to start.")