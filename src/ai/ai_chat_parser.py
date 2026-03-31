# src/ai/ai_chat_parser.py
import logging
from typing import Dict, Any

# --- NEW: We must import the AI classes to query them ---
# (Adjust these imports if your file structure is different)
try:
    from src.core.ai_agent import AIActionDecider, ai_agent_status
    from src.ai.heuristic_engine import HeuristicEngine
    from src.ai.generative_ai_client import GenerativeAIClient
except ImportError:
    logging.critical("Chat Parser: Could not import AI components!")
    # Define dummy classes if import fails, so the app can still run
    class AIActionDecider: pass
    class HeuristicEngine: pass
    class GenerativeAIClient: pass
    ai_agent_status = {}


# Store last decision for "why" questions
last_decision_context = "No decision has been made yet."

def update_last_decision(context: str):
    """Called by the gateway to update the chat parser's memory."""
    global last_decision_context
    last_decision_context = context

def parse_ai_query(query: str, ai_agent: AIActionDecider, heuristic_engine: HeuristicEngine, generative_ai_client: GenerativeAIClient) -> str:
    """
    Parses a natural language query from the user and returns an intelligent response.
    This is the core of the "interactive" AI.
    """
    query = query.lower().strip()
    logging.info(f"Parsing AI Chat Query: '{query}'")

    try:
        # --- Rule 1: "explain [rule]" ---
        if "explain" in query and "r0" in query:
            rule_id = query.split(" ")[-1].upper() # Gets 'R006'
            if not hasattr(ai_agent, 'rules'):
                return "AI agent is not fully initialized. Cannot explain rules yet."
                
            for rule in ai_agent.rules:
                if rule['id'] == rule_id:
                    return f"Rule {rule_id} is: '{rule['log']}' It has a priority of {rule.get('priority', 'N/A')}."
            return f"Sorry, I don't have a rule named {rule_id} in my knowledge base."

        # --- Rule 2: "confidence in [tool]" ---
        if "confidence" or "learn" in query:
            try:
                # Extracts Rule ID like R001 from "What is your confidence for R001"
                words = query.split()
                rule_id = next((w.upper() for w in words if w.startswith('R') and any(c.isdigit() for c in w)), None)
                
                if rule_id:
                    heuristics = getattr(heuristic_engine, 'heuristics', {})
                    scores = [v['confidence'] for k, v in heuristics.items() if rule_id in k]
                    if scores:
                        avg_score = (sum(scores) / len(scores)) * 100
                        return f"My current learned confidence for rule {rule_id} is {avg_score:.1f}%. I am refining this based on local results."
                    return f"I have no learning data for {rule_id} yet. My default confidence is 100%."
            except Exception as e:
                logging.error(f"Heuristic lookup failed: {e}")
                rule_id = query.split()[-1].upper() # e.g. "confidence R001"
                scores = [v['confidence'] for k, v in heuristic_engine.heuristics.items() if rule_id in k]

                if not hasattr(heuristic_engine, 'heuristics'):
                    return "Heuristic engine is not initialized. Cannot get confidence yet."

                if not scores:
                    return f"Igris has no field data for {rule_id}. Defaulting to 100% logic."
                
                avg_score = (sum(scores) / len(scores)) * 100
                return f"Learned Confidence for {rule_id}: {avg_score:.1f}%. I'm getting smarter, Burns."

        # --- Rule 3: "status of [field]" ---
        if "status of" in query:
            field_id = query.split("status of")[-1].strip()
            # This is a simulation; a real app would query the DB
            return (f"I'm actively monitoring {field_id}. All sensors appear to be stable. "
                    f"The last action taken was '{ai_agent_status.get('last_action', 'N/A')}'.")

        # --- Rule 4: "why did you" ---
        if "why" in query or "reason" in query:
            # Get the raw numbers from the Heuristic Engine
            heuristics = heuristic_engine.heuristics if hasattr(heuristic_engine, 'heuristics') else {}
            
            # We ask the Generative AI to 'Translate' the math into wisdom
            prompt = (f"The user is asking '{query}'. "
                    f"Our last decision was: {last_decision_context}. "
                    f"Our internal confidence metrics are: {heuristics}. "
                    f"Explain this to the user in a way that shows we are learning.")
            
            try:
                # Use Gemini to explain the Heuristic math!
                return generative_ai_client.get_ai_decision({"field_id": "GLOBAL"}, f"Explain reasoning for: {query}")
            except:
                return f"Heuristic Context: {last_decision_context}. (Generative reasoning failed)."
        
        # --- Rule 5: "hello" / "who are you" ---
        if "hello" in query or "who are you" in query:
            return ("Hello! I am Agriadvisor, a Heuristic AI. "
                    "I make rational decisions for the farm and learn from their outcomes.")
        
        # --- Fallback ---
        system_state = {
            "last_decision": last_decision_context,
            "agent_status": ai_agent_status,
            "heuristic_memory_size": len(getattr(heuristic_engine, 'heuristics', {})),
            "user_query": query
        }

        prompt = f"""
        Context for Igris (Shadow Advisor):
        - User asked: "{query}"
        - Last system action/context: "{last_decision_context}"
        - Current Agent Status: {ai_agent_status}
        - Total Heuristic Rules Learned: {system_state['heuristic_memory_size']}

        Task:
        Respond to the user as Igris. Do not say "I don't understand." 
        Use the context above to answer them. If they are asking something general, 
        relate it to the current farm status or your learning progress. 
        Be the expert advisor Burns expects.
        """

        try:
            try:
                return generative_ai_client.get_ai_decision(system_state, f"User Chat: {query}")
            except Exception as e:
                logging.error(f"Generative Fallback Failed: {e}")
                if any(word in query for word in ["how", "what", "can you", "describe"]):
                    return generative_ai_client.get_ai_decision({"field_id": "KNOWLEDGE_QUERY"}, query)
                return f"Igris is processing... Current Context: {last_decision_context}. (Heuristic link active, Generative link timing out)."
        except Exception as e:
            logging.error(f"Generative Fallback Failed: {e}")

        return "I am listening. Ask about my confidence, a specific rule, or for a general farm explanation."

    except Exception as e:
        logging.error(f"Error parsing chat query: {e}")
        return "I encountered an error trying to process that."