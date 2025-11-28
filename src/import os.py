import os
import shutil

# Define the new structure
structure = {
    "config": [
        "ai_knowledge.json",
        "critical_policies.json",
        "model_config.json",
        "system_config.py",
        "config.py",
        "constants.py"
    ],
    "docs": [
        "api_docs.md",
        "README.md"
    ],
    "web": [
        "dashboard.html",
        "index.html",
        "main.js",
        "styles.css"
    ],
    "src": [
        # Main entry point needs renaming later, but moving first
        "scheduler_gateway.py"
    ],
    "src/core": [
        "ai_agent.py",
        "tool_executioner.py"
    ],
    "src/services": [
        "alert_manager.py",
        "cost_management.py",
        "external_api_client.py",
        "log_analyzer.py",
        "monitoring_service.py"
    ],
    "src/ml": [
        "ml_model.py",
        "model_training.py",
        "feature_engineering.py",
        "predictive_algorithms.py",
        "data_loader.py"
    ],
    "src/utils": [
        "api_interface.py",
        "db_connector.py",
        "logger_utility.py",
        "schema_definitions.py",
        "utils.py"
    ],
    "data": [
        
    ]
}

def create_structure_and_move():
    print("--- Starting Project Restructure ---")
    
    # 1. Create Directories
    for folder in structure.keys():
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Created directory: {folder}")

    # 2. Move Files
    for folder, files in structure.items():
        for filename in files:
            if os.path.exists(filename):
                destination = os.path.join(folder, filename)
                try:
                    shutil.move(filename, destination)
                    print(f"Moved {filename} -> {destination}")
                except Exception as e:
                    print(f"Error moving {filename}: {e}")
            else:
                print(f"Warning: {filename} not found, skipping.")
    
    # 3. Create __init__.py files for Python packages
    python_folders = ["src", "src/core", "src/services", "src/ml","src/utils"]
    for folder in python_folders:
        init_path = os.path.join(folder, "__init__.py")
        if not os.path.exists(init_path):
            with open(init_path, 'w') as f:
                f.write("# Package initialization")
                print(f"Created {init_path}")
    
    # 4. Rename Main Entry Point
    old_main = os.path.join("src", "scheduler_gateway.py")
    new_main = os.path.join("src", "main.py")
    if os.path.exists(old_main):
        shutil.move(old_main, new_main)
        print(f"Renamed scheduler_gateway.py -> main.py")
        print("\n--- Restructure Complete! ---")
        print("IMPORTANT: You must now update your Python imports to matchthe new paths.")
        print("Example: 'from ai_agent import X' becomes 'fromsrc.core.ai_agent import X'")

if __name__ == "__main__":
    create_structure_and_move()