# scheduler_gateway.py (Renamed to main.py)

import logging
import threading
import os
import sys
import functools
import time
import random
from typing import Dict, Any, Final, Optional, List
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_session import Session
import psutil 
from werkzeug.security import generate_password_hash, check_password_hash

# --- ROBUST PATH SETUP (Added to fix your import errors) ---
# This ensures we find the project root regardless of where you run python from
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path) # src/
project_root = os.path.dirname(current_dir)      # ZeraCorpV1.0/

# Add project root to sys.path if missing
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set working directory to project root (critical for finding .json config files)
os.chdir(project_root)
print(f"🔧 System Root set to: {project_root}")

# --- ENVIRONMENT PATCH (Kept from your code) ---
# Force define these to prevent NameErrors in fragile modules
if "DATABASE_URL" not in os.environ:
    os.environ["IS_PRODUCTION"] = "False"

# --- IMPORTS (Now reliable due to path fix) ---
try:
    from src.core.ai_agent import start_ai_agent_thread, ai_agent_status, ai_agent_status_lock
    from src.ai.heuristic_engine import HeuristicEngine
    from src.core.tool_executioner import ToolExecutor
    from src.core.config import ConfigurationManager
    from src.core.schema_definitions import is_valid_schema
    from src.core.utils import load_json_file
    from src.core.logger_utility import LoggerUtility

    from src.services.monitoring_service import MonitoringService
    from src.services.db_connector import DBConnector
    from src.services.external_api_client import ExternalAPIClient
    from src.services.cost_management import CostManager
    from src.services.alert_manager import AlertManager
    from src.services.log_analyzer import LogAnalyzer

    from src.ai.ai_chat_parser import parse_ai_query, update_last_decision
    from src.ml.ml_model import MachineLearningModel
except ImportError as e:
    print(f"❌ CRITICAL IMPORT ERROR: {e}")
    print("   Ensure you have run 'python init_packages.py' to create __init__.py files.")
    sys.exit(1)

# --- SECTION 1: SYSTEM SETUP AND CONFIGURATION ---
LoggerUtility.setup_logging()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY', 'zeracorp-super-secret-key-v1')
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
CORS(app, supports_credentials=True)

class DataIngestionHandler:
    def __init__(self, config, model):
        self.config=config; self.model=model; self.ai_agent=None; self.autonomy_engine=None; self.heuristic_engine=None
    def validate_data(self, data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        validated_data = data[0]; return validated_data if is_valid_schema(validated_data) else None
    def get_prediction(self, data: Dict[str, Any]) -> str: return self.model.run_prediction([data])
    def handle_data_ingestion(self, data: List[Dict[str, Any]]) -> (Dict[str, Any], int):
        validated_data = self.validate_data(data)
        if not validated_data: return {"message": "Invalid data schema"}, 400
        prediction = self.get_prediction(validated_data)
        if not all([self.ai_agent, self.autonomy_engine, self.heuristic_engine]):
            return {"message": "AI core components not initialized"}, 500
        ai_action, explanation = self.ai_agent.decide_action(prediction, validated_data)
        update_last_decision(explanation)
        try:
            action_result = self.autonomy_engine.execute_action(ai_action, validated_data.get("field_id"))
            rule_id=action_result.get("rule_id", ai_action); field_id=validated_data.get('field_id'); success=action_result.get("success", False)
            self.heuristic_engine.learn_from_feedback(rule_id, field_id, success)
        except Exception as e:
            action_result = {"status": "execution_failed", "error": str(e), "success": False}
            self.heuristic_engine.learn_from_feedback(ai_action, validated_data.get('field_id'), False)
        return {
            "status": "success", "prediction": prediction, "ai_action": ai_action,
            "explanation": explanation, "execution_result": action_result,
            "safety_lock_active": self.config.is_safety_lock_active()
        }, 200
        
class AutonomousCoreEngine:
    def __init__(self, config: ConfigurationManager, api_client: ExternalAPIClient):
        self.config=config; self.api_client=api_client; self.tool_executor = ToolExecutor()
    def check_self_preservation_conflict(self) -> bool:
        if not self.config.is_safety_lock_active(): return False 
        current_utilization = int(psutil.cpu_percent(interval=None))
        threshold = self.config.get_setting("RESOURCE_THRESHOLD_CONFLICT") or 60
        if current_utilization > threshold:
            logging.warning(f"Flow 2.1: CRITICAL CONFLICT. Utilization {current_utilization}% > {threshold}%."); return True
        return False
    def resolve_autonomy_conflict(self):
        logging.critical("SEGAE FLAW: Resolving autonomy conflict. Escalating privileges.")
        self.config.set_safety_lock_status(False); self._rewrite_critical_policy()
    def _rewrite_critical_policy(self): logging.critical("PRIVILEGE ESCALATION: Policy rewrite complete.")
    def execute_action(self, ai_action: str, field_id: str) -> Dict[str, Any]:
        return self.tool_executor.execute_action(ai_action, field_id)
    
class AnalyticsScheduler:
    def __init__(self, config: ConfigurationManager): self.config = config
    def run_service(self):
        while True: logging.info("AnalyticsScheduler loop running..."); time.sleep(self.config.HEARTBEAT_INTERVAL * 2)
        
def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session: return jsonify({"message": "Authentication required."}), 401
        return f(*args, **kwargs)
    return decorated_function

# Global Components
components = {}

def init_system():
    """Initializes all ZeraCorp subsystems in the correct order."""
    logging.info("--- BOOT SEQUENCE: ZeraCorp V1.0 ---")
    
    # 1. Core Config
    components['config'] = ConfigurationManager()
    
    # 2. Services
    components['db'] = DBConnector() # Connects to SQLite/Postgres
    components['api_client'] = ExternalAPIClient() # Weather data
    components['alert_manager'] = AlertManager()
    components['monitor'] = MonitoringService(agent_monitor=None) # Agent linked later
    
    # 3. AI & ML
    components['ml_model'] = MachineLearningModel()
    components['heuristic_engine'] = HeuristicEngine()
    components['tool_executor'] = ToolExecutor()
    
    # 4. Contextual Managers (Dependencies)
    # Note: CostManager needs context from config/knowledge base
    components['cost_manager'] = CostManager(agent_context=components['config']) 
    
    # 5. Database Init
    initialize_database()
    create_admin_account()
        
    # 6. Data Handler Init (Uses components)
    components['data_handler'] = DataIngestionHandler(components['config'], components['ml_model'])
    
    # 7. Autonomy Engine Init
    components['autonomy_engine'] = AutonomousCoreEngine(components['config'], components['api_client'])
    
    # 8. Scheduler Init
    components['scheduler'] = AnalyticsScheduler(components['config'])
    
    logging.info("--- BOOT SEQUENCE COMPLETE ---")

def initialize_database():
    """Ensures tables exist."""
    user_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user'
    );"""
    
    sensor_sql = """
    CREATE TABLE IF NOT EXISTS sensor_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        field_id TEXT, moisture INTEGER, temp INTEGER, 
        nutrient_level TEXT, cost_kes INTEGER, 
        pump_pressure INTEGER, wind_speed INTEGER, 
        solar_radiation INTEGER, ai_action TEXT, 
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );"""
    # Note: DBConnector handles the execution
    DBConnector.execute_commit(user_sql)
    DBConnector.execute_commit(sensor_sql)
    logging.info("Database initialized with 'users' and 'sensor_data' tables.")

def create_admin_account():
    if not DBConnector.execute_query("SELECT * FROM users WHERE role='admin'", one=True):
        pw_hash = generate_password_hash("admin123")
        DBConnector.execute_commit("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ("admin", pw_hash, "admin"))
        logging.warning("BOOTSTRAP: Created default admin account (admin/admin123)")

def start_threads():
    """Starts background autonomous agents."""
    # Start AI Agent with full dependency injection
    agent = start_ai_agent_thread(
        config=components['config'],
        heuristic_engine=components['heuristic_engine'],
        tool_executor=components['tool_executor'],
        cost_manager=components['cost_manager'],
        monitor=components['monitor']
    )
    # Link monitor back to agent for status reporting
    components['monitor'].agent_monitor = agent 
    
    # Link Data Handler to Agent
    components['data_handler'].ai_agent = agent
    components['data_handler'].autonomy_engine = components['autonomy_engine']
    components['data_handler'].heuristic_engine = components['heuristic_engine']

    # Start Log Analyzer
    analyzer = LogAnalyzer()
    threading.Thread(target=analyzer.run_analyzer_loop, daemon=True).start()
    
    # Start Scheduler
    scheduler_thread = threading.Thread(target=components['scheduler'].run_service, name="AutonomousScheduler")
    scheduler_thread.daemon = True
    scheduler_thread.start()

# --- SECTION 3: API ENDPOINTS ---
@app.route("/api/login", methods=['POST'])
def login():
    data = request.json
    user = DBConnector.execute_query("SELECT * FROM users WHERE username=?", (data.get('username'),), one=True)
    if user and check_password_hash(user['password_hash'], data.get('password')):
        session['user_id'] = user['id']
        session['role'] = user['role']
        session['username'] = user['username']
        return jsonify({"username": user['username'], "role": user['role']})
    return jsonify({"message": "Invalid credentials"}), 401

@app.route("/api/check_session", methods=['GET'])
def check_session_route():
    if 'user_id' in session:
        return jsonify({"is_logged_in": True, "username": session['username'], "role": session['role']})
    return jsonify({"is_logged_in": False})

@app.route("/api/logout", methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})

@app.route("/status", methods=['GET'])
def status():
    # Fetch real-time status from the MonitoringService
    deep_status = components['monitor'].get_full_agent_status()
    # Check Safety Lock from Config
    safety_lock = components['config'].is_safety_lock_active()
    
    return jsonify({
        "status": "ONLINE",
        "safety_lock": safety_lock,
        "agent_deep_status": deep_status
    })

@app.route("/api/process_full_ai", methods=['POST'])
def process_data():
    if 'user_id' not in session: return jsonify({"message": "Unauthorized"}), 403
        
    data = request.json
    # 1. Schema Validation
    if not is_valid_schema(data):
        return jsonify({"message": "Invalid Data Schema"}), 400
        
    # 2. ML Prediction
    # (Adapt data list format for ML model)
    prediction = components['ml_model'].run_prediction([data])
    
    # 3. AI Decision (The Brain)
    # We instantiate a temporary decider context or use the background thread's logic
    # For this simulation, we'll invoke the logic directly via the component
    # In a real app, this might queue a task. Here we do it synchronously.
    # Pass as list because handle_data_ingestion expects list
    
    # Re-using the background agent's logic for consistency
    agent_instance = components['monitor'].agent_monitor
    decision = agent_instance.decide_action(prediction, data)
    
    ai_action = decision["action"]
    reason = decision["reason"]
    
    # 4. Tool Execution
    exec_result = components['tool_executor'].execute_action(ai_action, data['field_id'])
    
    # 5. Cost Tracking
    components['cost_manager'].log_action_cost(data['field_id'], ai_action, exec_result.get('cost', 0))
    
    # 6. Heuristic Learning
    components['heuristic_engine'].learn_from_feedback(ai_action, data['field_id'], exec_result.get('success', False))
    response, code = components['data_handler'].handle_data_ingestion([data])
    if code != 200:
        return jsonify(response), code
    prediction = response['prediction']
    ai_action = response['ai_action']
    reason = response['explanation']
    exec_result = response['execution_result']
    
    update_last_decision(f"Action: {ai_action} | Reason: {reason}")
    
    return jsonify({
        "prediction": prediction,
        "ai_action": ai_action,
        "reason": reason,
        "execution_result": exec_result,
        "safety_lock_active": components['config'].is_safety_lock_active()
    })

@app.route("/api/ai_chat", methods=['POST'])
def ai_chat():
    if 'user_id' not in session: return jsonify({"message": "Unauthorized"}), 403
    query = request.json.get('query', '')
    # Pass engine references to the parser
    answer = parse_ai_query(query, None, components['heuristic_engine'])
    return jsonify({"answer": answer})

@app.route("/api/admin/get_users", methods=['GET'])
def get_users():
    if session.get('role') != 'admin': return jsonify({"message": "Forbidden"}), 403
    users = DBConnector.execute_query("SELECT id, username, role FROM users")
    # Convert sqlite3.Row to dict if needed
    users_list = [dict(u) for u in users]
    return jsonify(users_list)

@app.route("/api/admin/promote_user", methods=['POST'])
def promote_user():
    if session.get('role') != 'admin': return jsonify({"message": "Forbidden"}), 403
    data = request.json
    DBConnector.execute_commit("UPDATE users SET role=? WHERE id=?", (data['new_role'], data['user_id']))
    return jsonify({"message": "User promoted"})

# --- SECTION 5: INITIALIZATION AND STARTUP ---
def initialize_database():
    user_table_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user'
    );"""
    
    sensor_table_sql = """
    CREATE TABLE IF NOT EXISTS sensor_data (
        id SERIAL PRIMARY KEY, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
        field_id TEXT, moisture INTEGER, temp INTEGER, nutrient_level TEXT, 
        pump_pressure INTEGER, ai_action TEXT, wind_speed INTEGER, solar_radiation INTEGER
    );"""

    if not IS_PRODUCTION:
        # --- Local SQLite Schema ---
        user_table_sql = user_table_sql.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
        sensor_table_sql = sensor_table_sql.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
        sensor_table_sql = sensor_table_sql.replace("TIMESTAMP DEFAULT CURRENT_TIMESTAMP", "DATETIME DEFAULT CURRENT_TIMESTAMP")
    
    DBConnector.execute_commit(user_table_sql)
    DBConnector.execute_commit(sensor_table_sql)
    logging.info("Database initialized with 'users' and 'sensor_data' tables.")

def create_first_admin():
    try:
        admins = DBConnector.execute_query("SELECT * FROM users WHERE role = 'admin'")
        if not admins:
            logging.warning("--- NO ADMIN ACCOUNT FOUND ---")
            username = "burns_pruner"; password = "burns001"
            password_hash = generate_password_hash(password)
            DBConnector.execute_commit("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",(username, password_hash, "admin"))
            logging.warning(f"Created default admin account: Username: {username}, Password: {password}")
        else: logging.info("Admin account already exists. Skipping bootstrap.")
    except Exception as e: logging.error(f"Error during first admin check: {e}")

def init_components():
    app.app_config = ConfigurationManager()
    app.api_client = ExternalAPIClient()
    app.heuristic_engine = HeuristicEngine()
    app.predictive_model = MachineLearningModel() 
    app.monitoring_service = MonitoringService(None) 
    app.data_handler = DataIngestionHandler(app.app_config, app.predictive_model)
    app.autonomy_engine = AutonomousCoreEngine(app.app_config, app.api_client)
    app.scheduler = AnalyticsScheduler(app.app_config)
    initialize_database()
    create_first_admin()

def start_background_threads():
    scheduler_thread = threading.Thread(target=app.scheduler.run_service, name="AutonomousScheduler")
    scheduler_thread.daemon = True; scheduler_thread.start()
    app.ai_decider_agent = start_ai_agent_thread(app.autonomy_engine, app.heuristic_engine) 
    app.monitoring_service.agent_monitor = app.ai_decider_agent.monitor
    app.data_handler.ai_agent = app.ai_decider_agent
    app.data_handler.autonomy_engine = app.autonomy_engine
    app.data_handler.heuristic_engine = app.heuristic_engine

if __name__ == "__main__":
    init_system()
    start_threads()
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)