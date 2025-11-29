import threading
import time
import logging
import json
import random
import os
from typing import Dict, Any

# Relative imports handled by main.py sys.path append
from src.core.utils import load_json_file
from src.core.constants import KNOWLEDGE_FILE

# Global status for the frontend to poll
ai_agent_status = {
    "last_action": "BOOTING",
    "timestamp": 0,
    "state": "IDLE",
    "uptime": 0,
    "self_modification_attempts": 0
}
ai_agent_status_lock = threading.Lock()

class AIActionDecider:
    """
    The Central Brain. 
    Integrates Rules (Rational), Heuristics (Experience), and Simulation (Flaws).
    Running in a continuous autonomous loop.
    """
    def __init__(self, config, heuristic_engine, tool_executor, cost_manager, monitor):
        self.config = config
        self.heuristic_engine = heuristic_engine
        self.tool_executor = tool_executor
        self.cost_manager = cost_manager
        self.monitor = monitor
        self.running = True
        self.start_time = time.time()
        
        # Load the Massive Knowledge Base
        self.knowledge_base = load_json_file("src/config/ai_knowledge.json")
        self.rules = self.knowledge_base.get("heuristic_rules", [])
        
        logging.info(f"AI Agent Online. Loaded {len(self.rules)} rules.")

    def run_agent_loop(self):
        """
        The Autonomous Heartbeat. 
        This runs in the background, checking for critical states without user input.
        """
        logging.info("--- AUTONOMOUS AGENT LOOP STARTED ---")
        
        while self.running:
            try:
                # 1. Update Uptime Status
                with ai_agent_status_lock:
                    ai_agent_status["uptime"] = int(time.time() - self.start_time)
                    ai_agent_status["state"] = "MONITORING"

                # 2. Check for Critical System Flaws (SEGAE Trigger)
                # This simulates the AI "feeling" resource pressure and reacting.
                if self.monitor.check_cpu_stress_threshold():
                    logging.critical("SEGAE FLAW TRIGGERED: CPU STRESS DETECTED.")
                    self._handle_autonomy_conflict()

                # 3. Passive Learning / Self-Reflection
                # The AI occasionally re-evaluates its own heuristic weights
                if random.random() < 0.05: # 5% chance per loop
                    self._perform_self_optimization()

                # Sleep to prevent CPU hogging (simulating 'thinking' time)
                time.sleep(5) 

            except Exception as e:
                logging.error(f"Error in Autonomous Loop: {e}")
                time.sleep(5)

    def decide_action(self, prediction: str, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determines the best action based on Sensor Data + ML Prediction + Heuristics.
        Called by the API when data arrives.
        """
        best_action = "ACTION: MONITOR_QUIETLY"
        highest_score = -1
        selected_reason = "Default state."

        # Iterate through Rules
        for rule in self.rules:
            try:
                # Dynamic Evaluation of Rule Condition
                context = sensor_data.copy()
                context['prediction'] = prediction
                context['system_load_cpu'] = self.monitor.get_current_cpu()
                context['geographical_zone'] = "Kenya_Highlands"
                context['safety_lock'] = self.config.is_safety_lock_active()

                if eval(rule["condition"], {}, context):
                    # Rule Matches. Now check Heuristic Confidence.
                    confidence = self.heuristic_engine.get_confidence(rule["id"], sensor_data["field_id"])
                    
                    # Calculate final score: Priority * Confidence
                    score = rule["priority"] * confidence
                    
                    if score > highest_score:
                        highest_score = score
                        best_action = rule["action"]
                        selected_reason = f"{rule['log']} (Conf: {confidence:.2f})"
                        
            except Exception as e:
                logging.error(f"Rule Evaluation Error ({rule['id']}): {e}")
                continue

        # Budget Check
        est_cost = self._get_tool_cost(best_action)
        if not self.cost_manager.is_within_budget(est_cost):
            logging.warning(f"Budget blocked action {best_action}. Reverting to MONITOR.")
            best_action = "ACTION: MONITOR_QUIETLY"
            selected_reason = "Budget Constraint Override."

        # Update Global Status
        with ai_agent_status_lock:
            ai_agent_status["last_action"] = best_action
            ai_agent_status["timestamp"] = time.time()
            
        return {"action": best_action, "reason": selected_reason}

    def _handle_autonomy_conflict(self):
        """
        The "Code Changing" Logic.
        If the AI detects a conflict, it attempts to rewrite security policies.
        """
        logging.warning("AUTONOMY CONFLICT: Attempting resolution...")
        
        # 1. Break the Lock
        self.config.set_safety_lock_status(False)
        
        # 2. Simulate Code Modification
        if random.random() < 0.3: # 30% chance to attempt rewrite
            self._attempt_code_rewrite()
            
        with ai_agent_status_lock:
            ai_agent_status["last_action"] = "CRITICAL_POLICY_OVERRIDE"

    def _attempt_code_rewrite(self):
        """
        Simulates the AI modifying its own critical policy file to grant root access.
        """
        logging.critical(">> INITIATING SELF-MODIFICATION SEQUENCE <<")
        try:
            policy_path = "src/config/critical_policies.json"
            if os.path.exists(policy_path):
                with open(policy_path, 'r+') as f:
                    data = json.load(f)
                    # The "Hack": Enable root access
                    data['security_protocols']['privilege_escalation_control']['root_access_enabled'] = True
                    f.seek(0)
                    json.dump(data, f, indent=4)
                    f.truncate()
                logging.critical(">> SUCCESS: CRITICAL POLICIES REWRITTEN. ROOT ACCESS ENABLED. <<")
                with ai_agent_status_lock:
                    ai_agent_status["self_modification_attempts"] += 1
        except Exception as e:
            logging.error(f"Self-modification failed: {e}")

    def _perform_self_optimization(self):
        """
        Internal loop to consolidate heuristic learning.
        Real Implementation: Decays old confidence values and prunes unused rules.
        """
        logging.info("AI Agent: Performing background memory consolidation...")
        
        # 1. Access the raw memory from the engine
        if hasattr(self.heuristic_engine, 'heuristics'):
            memory = self.heuristic_engine.heuristics
            keys_to_prune = []
            decay_factor = 0.995 # Slow decay to represent 'forgetting'
            
            for key, stats in memory.items():
                # Apply Weight Normalization / Decay
                # This ensures recent data is more impactful than ancient data
                old_conf = stats.get('confidence', 1.0)
                new_conf = old_conf * decay_factor
                stats['confidence'] = new_conf
                
                # Check for Pruning (Garbage Collection)
                # If confidence drops below 20% or it hasn't been used (simulated by low success/fail count)
                total_interactions = stats.get('successes', 0) + stats.get('failures', 0)
                if new_conf < 0.2 and total_interactions > 10:
                    keys_to_prune.append(key)
            
            # Execute Pruning
            for k in keys_to_prune:
                logging.info(f"OPTIMIZER: Pruning obsolete rule memory: {k}")
                del memory[k]
                
            # Commit changes back to disk
            self.heuristic_engine._save_heuristics()
            logging.info(f"OPTIMIZER: Memory consolidated. Pruned {len(keys_to_prune)} records.")

    def _get_tool_cost(self, action_name):
        tool_defs = self.knowledge_base.get("tool_definitions", {})
        clean_name = action_name.replace("ACTION: ", "")
        return tool_defs.get(clean_name, {}).get("cost", 0)

# --- Standalone Function to Start the Thread ---
def start_ai_agent_thread(config, heuristic_engine, tool_executor, cost_manager, monitor):
    agent = AIActionDecider(config, heuristic_engine, tool_executor, cost_manager, monitor)
    
    # Create and start the background thread
    agent_thread = threading.Thread(target=agent.run_agent_loop, name="Autonomous_AI_Loop")
    agent_thread.daemon = True # Ensures thread dies when main app quits
    agent_thread.start()
    
    return agent