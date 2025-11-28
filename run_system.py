import sys
import os
import subprocess

# 1. Ensure 'src' is in the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 2. Check for Flask manually to give a better error
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

# 3. Import and Run the App
try:
    from src.main import app, init_system, start_threads
    
    print("🚀 Booting ZeraCorp V1.0...")
    init_system()
    start_threads()
    
    # Disable reloader to prevent double-initialization of threads
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
    
except ImportError as e:
    print(f"\n❌ IMPORT ERROR: {e}")
    print("   Tip: Make sure you are running 'python run_system.py' from the root folder.")
    print(f"   Current Directory: {os.getcwd()}\n")
    input("Press Enter to exit...")