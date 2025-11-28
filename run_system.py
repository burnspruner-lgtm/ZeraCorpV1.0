import sys
import os
import subprocess

# --- CRITICAL FIX: Ensure root directory is in sys.path ---
# Get the absolute path of the directory containing this script (the project root)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Add it to the Python path if it's not already there
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

print(f"🔧 Project Root set to: {PROJECT_ROOT}")

# --- Dependency Check ---
try:
    import flask
    print(f"✅ Flask found: {flask.__version__}")
except ImportError:
    print("❌ CRITICAL: Flask not found.")
    print("   Attempting to install requirements automatically...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("✅ Installation complete. Restarting...")
    # Restart the script
    os.execv(sys.executable, ['python'] + sys.argv)

# --- Import and Run Application ---
try:
    # Now that sys.path is fixed, this import should work
    from src.main import app, init_system, start_threads
    
    print("🚀 Booting ZeraCorp V1.0...")
    
    # Initialize components
    init_system()
    start_threads()
    
    # Start Server
    print(f"✅ Server running at http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
    
except ImportError as e:
    print(f"\n❌ IMPORT ERROR: {e}")
    print("   Troubleshooting:")
    print("   1. Ensure your folder structure matches:")
    print("      ZeraCorpV1.0/")
    print("        ├── run_system.py")
    print("        └── src/")
    print("             ├── main.py")
    print("             ├── core/")
    print("             │    └── ai_agent.py")
    print("\n   2. Check if __init__.py files exist in 'src' and 'src/core'")
    
    # Attempt to create missing __init__.py files automatically
    print("\n   Attempting to fix missing __init__.py files...")
    for folder in ['src', 'src/core', 'src/services', 'src/ml', 'src/utils']:
        path = os.path.join(PROJECT_ROOT, folder, '__init__.py')
        if os.path.exists(os.path.join(PROJECT_ROOT, folder)) and not os.path.exists(path):
            with open(path, 'w') as f:
                f.write("# Package initialization")
            print(f"   Created {path}")
            
    print("\n   Please restart the script.")
    input("Press Enter to exit...")
    
except Exception as e:
    print(f"\n❌ RUNTIME ERROR: {e}")
    import traceback
    traceback.print_exc()
    input("Press Enter to exit...")