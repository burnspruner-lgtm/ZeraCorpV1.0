import sys
import os
import logging

# 1. Add the current directory to Python's path so 'src' is recognized as a package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 2. Configure Logging
logging.basicConfig(level=logging.INFO, format='[BOOTSTRAP] %(message)s')

logging.info("--- ZeraCorp V1.0 System Bootstrapper ---")
logging.info(f"Root Directory: {os.getcwd()}")

# 3. Import and Run the Main Application
try:
    from src.main import app, init_system, start_threads
    
    # Initialize the "Fully Fledged" components
    init_system()
    start_threads()
    
    # Launch the Server
    logging.info("Server starting on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
    
except ImportError as e:
    logging.critical(f"Import Error: {e}")
    logging.critical("Ensure you are running this script from the project root directory.")
except Exception as e:
    logging.critical(f"System Crash: {e}")