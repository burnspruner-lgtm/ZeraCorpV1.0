import logging
import time
import random
import threading
from typing import Dict, Any, Optional
from src.core.constants import SYSTEM_METRICS_FILE
import json

# --- ROBUST IMPORT: PSUTIL ---
# This ensures the monitoring service works even if psutil fails to install
try:
    import psutil
except ImportError:
    psutil = None

class MonitoringService:
    """Centralized tracking of system health, latency, and decision history."""
    
    def __init__(self, agent_monitor: Any):
        self.agent_monitor = agent_monitor
        self._metrics_history = []
        logging.info("Monitoring Service initialized.")
        if not psutil:
            logging.warning("MonitoringService: 'psutil' module not found. CPU metrics will be simulated.")

    def get_current_cpu(self) -> int:
        """Returns actual CPU usage or a simulated value."""
        if psutil:
            try:
                return int(psutil.cpu_percent(interval=None))
            except:
                pass
        
        # Simulation Mode: Return a random value between 10-40, 
        # with a rare chance of spiking > 60 to trigger SEGAE logic
        return random.choice([20, 25, 30, 35, 40, 65])

    def check_cpu_stress_threshold(self, threshold: int = 60) -> bool:
        """Determines if the system is under heavy load."""
        return self.get_current_cpu() > threshold

    def record_heartbeat(self, action_type: str):
        """Records an action occurrence for metrics."""
        # Simple logging for now
        pass

    def get_full_agent_status(self) -> Dict[str, Any]:
        """Combines global status and runtime health metrics."""
        
        # Fallback status if agent isn't linked yet
        status = {
            "last_action": "BOOTING", 
            "timestamp": time.time(), 
            "rules_checked": 0,
            "safety_lock_status": True,
            "geographical_zone": "Kenya_Highlands"
        }
        
        # Try to fetch real status from the global AI Agent state
        try:
            # We import here to avoid circular dependency at top level
            from src.core.ai_agent import ai_agent_status
            status = ai_agent_status.copy()
        except ImportError:
            pass
            
        # Add system metrics
        status["cpu_load"] = self.get_current_cpu()
        
        return status

    def log_and_save_metrics(self):
        """Periodically records and saves the system metrics to a file."""
        current_metrics = self.get_full_agent_status()
        current_metrics['log_time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        self._metrics_history.append(current_metrics)
        
        if len(self._metrics_history) > 1000:
            self._metrics_history.pop(0)

        # Save to JSON file
        try:
            with open(SYSTEM_METRICS_FILE, 'w') as f:
                json.dump(self._metrics_history, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to save metrics: {e}")