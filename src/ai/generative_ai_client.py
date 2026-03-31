# src/ai/generative_ai_client.py
import logging
import time
from google import genai
from typing import Dict, Any

# --- !!! PASTE YOUR API KEY HERE !!! ---
# (Get your key from aistudio.google.com)
YOUR_API_KEY = "AIzaSyCy8r9B73r_hTQYf7m54ShheS8BLz2twpg"

class GenerativeAIClient:
    """
    This class replaces the ai_agent.py.
    It calls an external Generative AI (Gemini) instead of using local rules.
    """
    
    def __init__(self):
        try:
            self.model = genai.Client(api_key=YOUR_API_KEY)
            logging.info("GenerativeAIClient initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to configure Generative AI. Check API Key? Error: {e}")
            self.model = None

    def get_ai_decision(self, sensor_data: Dict[str, Any], ml_prediction: str) -> str:
        """
        Gets a new, creative decision from the Generative AI.
        """
        if not self.model:
            return "ERROR: GENERATIVE_AI_NOT_INITIALIZED"

        # 1. We create a "prompt" for the AI
        prompt = f"""
        You are 'Agriadvisor', an expert AI for Kenyan agriculture.
        A machine learning model has given a prediction, and you must decide the final, real-world action.

        Here is the data from the farm (in Kenya):
        - Field ID: {sensor_data.get('field_id')}
        - Soil Moisture: {sensor_data.get('moisture')}%
        - Temperature: {sensor_data.get('temp')}°C
        - Nutrient Level: {sensor_data.get('nutrient_level')}
        - Recent Cost (KES): {sensor_data.get('cost_kes')}
        - Pump Pressure: {sensor_data.get('pump_pressure')} psi
        - Historical Trend: {sensor_data.get('historical_trend')}

        The local ML model prediction is: "{ml_prediction}"

        Based on all this, what is the single, best, and safest action to take?
        Be concise. Start your response with 'ACTION:'
        (e.g., ACTION: Boost irrigation, but monitor pump pressure.)
        """

        
        # List of models to try in order
        models_to_try = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-flash-8b']
        last_error = "Unknown error"

        for model_name in models_to_try:
            try:
                response = self.model.models.generate_content(
                    model=model_name, 
                    contents=prompt
                )
                ai_action = response.text.strip()
                logging.info(f"Generative AI Decision ({model_name}): {ai_action}")
                return ai_action

            except Exception as e:
                last_error = str(e)
                # If it's a rate limit, wait and return status
                if "429" in last_error or "420" in last_error:
                    logging.warning(f"Rate limit hit on {model_name}. Waiting...")
                    time.sleep(5)
                    return "Status: Thinking, wait...."
                
                # Log the failure for this specific model and try the next one
                logging.error(f"Model {model_name} failed: {last_error}")
                continue 

        # If we reach here, all models failed
        return f"ERROR: AI_GENERATION_FAILED: All models exhausted. Last error: {last_error}"