"""
API client for downloading Tekken replay data from wank.wavu.wiki.
"""

import requests
import time
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class APIConfig:
    """Configuration for API client."""
    base_url: str = "https://wank.wavu.wiki/api/replays"
    max_retries: int = 3
    request_delay: float = 1.005
    timeout: int = 30
    batch_size: int = 700


class APIClient:
    """Client for interacting with the Tekken replay API."""
    
    def __init__(self, config: Optional[APIConfig] = None):
        """Initialize the API client.
        
        Args:
            config: API configuration. Uses default if None.
        """
        self.config = config or APIConfig()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TekkenReplayAnalyzer/2.0.0'
        })
    
    def download_replays(self, before_timestamp: int) -> List[Dict[str, Any]]:
        """Download a batch of replays from the API.
        
        Args:
            before_timestamp: Unix timestamp to fetch replays before.
            
        Returns:
            List of replay data dictionaries.
            
        Raises:
            requests.RequestException: If the API request fails.
        """
        url = f"{self.config.base_url}?before={before_timestamp}"
        
        try:
            response = self.session.get(
                url, 
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"API request failed for timestamp {before_timestamp}: {e}")
            raise
    
    def download_replays_with_retry(
        self, 
        before_timestamp: int, 
        set_number: int, 
        total_sets: int
    ) -> List[Dict[str, Any]]:
        """Download replays with retry logic for failed requests.
        
        Args:
            before_timestamp: Unix timestamp to fetch replays before.
            set_number: Current set number for logging.
            total_sets: Total number of sets for logging.
            
        Returns:
            List of replay data dictionaries, or empty list if all retries failed.
        """
        try:
            return self.download_replays(before_timestamp)
            
        except Exception as e:
            logger.warning(
                f"Download error for set {set_number}/{total_sets} "
                f"(timestamp {before_timestamp}): {e}"
            )
            
            for attempt in range(self.config.max_retries):
                try:
                    time.sleep(self.config.request_delay)
                    result = self.download_replays(before_timestamp)
                    logger.info(f"Retry {attempt + 1} succeeded for set {set_number}")
                    return result
                    
                except Exception as retry_error:
                    logger.warning(f"Retry {attempt + 1} failed: {retry_error}")
            
            logger.error(
                f"All retry attempts failed for set {set_number}/{total_sets} "
                f"(timestamp {before_timestamp})"
            )
            return []
    
    def close(self):
        """Close the session."""
        self.session.close()
