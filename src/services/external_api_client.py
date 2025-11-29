import logging
import datetime
from typing import Dict, Any, Optional
from src.core.system_config import CONFIG

# --- SAFE IMPORT: REQUESTS ---
# We wrap this in a try/except block so the system runs locally 
# even if the 'requests' library is missing.
try:
    import requests
except ImportError:
    requests = None

class ExternalAPIClient:
    """Client for fetching external data like weather or satellite imagery."""

    def __init__(self, api_url: str = CONFIG.EXTERNAL_WEATHER_API):
        self.api_url = api_url
        logging.info(f"External API Client configured for: {self.api_url}")
        if not requests:
            logging.warning("ExternalAPIClient: 'requests' module not found. Network calls will be simulated.")

    def fetch_current_weather(self, region: str) -> Optional[Dict[str, Any]]:
        """Simulates fetching current weather data for a region."""
        try:
            # Simulated external API call
            if requests:
                # In a real scenario, we would make the call here:
                # response = requests.get(f"{self.api_url}/weather?region={region}")
                # response.raise_for_status()
                pass
            
            # Simulated response based on Kenya_Highlands
            simulated_data = {
                "region": region,
                "current_temp_c": 22,
                "wind_speed_kph": 5,
                "precipitation_mm": 0.5,
                "last_update": datetime.datetime.now().isoformat()
            }
            
            logging.info(f"Successfully fetched simulated weather for {region}.")
            return simulated_data
        
        except Exception as e:
            logging.error(f"Error fetching external data: {e}")
            return None