"""
Time utility functions.
"""

import time
import datetime
from typing import Union


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable format.
    
    Args:
        seconds: Duration in seconds.
        
    Returns:
        Formatted duration string.
    """
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def format_timestamp(timestamp: Union[int, float]) -> str:
    """Format Unix timestamp to readable date/time.
    
    Args:
        timestamp: Unix timestamp.
        
    Returns:
        Formatted timestamp string.
    """
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_current_timestamp() -> float:
    """Get current Unix timestamp.
    
    Returns:
        Current timestamp.
    """
    return time.time()
