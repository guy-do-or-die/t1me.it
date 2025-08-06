import hashlib
from typing import Optional


class CacheManager:
    """Cache key generation and management utilities."""
    
    @staticmethod
    def generate_cache_key(url: str, timestamp: float, width: int, height: int) -> str:
        """
        Generate a unique cache key for the screenshot.
        
        Args:
            url: Video URL
            timestamp: Timestamp in seconds
            width: Screenshot width
            height: Screenshot height
            
        Returns:
            str: Unique cache key
        """
        # Create a unique string from the parameters
        cache_string = f"{url}:{timestamp}:{width}:{height}"
        
        # Generate MD5 hash
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    @staticmethod
    def generate_short_id() -> str:
        """
        Generate a short ID for links.
        
        Returns:
            str: 8-character short ID
        """
        import shortuuid
        return shortuuid.uuid()[:8]
    
    @staticmethod
    def is_bot_user_agent(user_agent: str) -> bool:
        """
        Detect if the user agent belongs to a bot/crawler.
        
        Args:
            user_agent: The user agent string
            
        Returns:
            bool: True if it's a bot, False if it's a human browser
        """
        if not user_agent:
            return True
            
        user_agent_lower = user_agent.lower()
        
        # Check if it's definitely a human browser
        human_patterns = [
            "mozilla", "chrome", "safari", "firefox", "edge", "opera",
            "webkit", "gecko", "trident", "presto"
        ]
        
        is_human_browser = (
            len(user_agent.strip()) > 20 and
            any(pattern in user_agent_lower for pattern in human_patterns) and
            "bot" not in user_agent_lower and
            "crawler" not in user_agent_lower and
            "spider" not in user_agent_lower
        )
        
        # Default to bot (OpenGraph preview) unless confirmed human browser
        return not is_human_browser
