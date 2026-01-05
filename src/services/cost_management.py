import logging
from typing import Dict, Any
# --- FIX: Absolute Import ---
from src.services.db_connector import DBConnector
# --- FIX: Absolute Import ---
# Note: AgentContext might need to be imported from where it is defined (likely ai_agent.py or similar)
# If AgentContext is just a type hint, we can use 'Any' or string forward reference to avoid circular imports
# For now, assuming AgentContext is a class available in src.core.ai_agent
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.core.ai_agent import AgentContext

class CostManager:
    """Logic for financial tracking, budget adherence, and calculating cost projections."""
    
    def __init__(self, agent_context: Any): # Changed type hint to Any to avoid circular import runtime error
        # Assuming agent_context has a config_manager or similar structure to get cost_limit
        # Adapting to the likely structure based on other files
        self.cost_limit_kes = 100000 # Default fallback
        
        # Try to extract from context if available
        if hasattr(agent_context, 'thresholds') and isinstance(agent_context.thresholds, dict):
             self.cost_limit_kes = agent_context.thresholds.get('max_daily_budget_kes', 100000)
        elif hasattr(agent_context, 'config_manager'):
             # fallback logic if needed
             pass
             
        logging.info(f"Cost Manager initialized. Daily Action Limit: KES {self.cost_limit_kes}")

    def is_within_budget(self, proposed_cost: int) -> bool:
        """Checks if a proposed action cost is below the configured critical limit."""
        if proposed_cost > self.cost_limit_kes:
            logging.warning(f"Cost breach: Proposed cost KES {proposed_cost} exceeds limit KES {self.cost_limit_kes}.")
            return False
        return True

    def log_action_cost(self, field_id: str, action_type: str, cost: int):
        """Logs the final executed cost into the database for financial tracking."""
        query = "INSERT INTO cost_log (field_id, action_type, cost, timestamp) VALUES (?, ?, ?, datetime('now'))"
        success = DBConnector.execute_commit(query, (field_id, action_type, cost))
        
        if success:
            logging.info(f"Cost KES {cost} logged for action {action_type} on {field_id}.")
        else:
            # We don't crash the system for a logging failure, just report it
            logging.error(f"Failed to log action cost for {action_type}")