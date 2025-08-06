from urllib.parse import urlparse
from typing import List


class URLValidator:
    """URL validation utilities for video platforms."""
    
    SUPPORTED_DOMAINS: List[str] = [
        'youtube.com', 'youtu.be', 'm.youtube.com',
        'vimeo.com', 'player.vimeo.com',
        'dailymotion.com', 'dai.ly',
        'twitch.tv', 'clips.twitch.tv',
        'facebook.com', 'fb.watch',
        'instagram.com',
        'tiktok.com',
        'twitter.com', 'x.com',
        'streamable.com',
        'wistia.com', 'fast.wistia.net',
        'brightcove.com',
        'jwplayer.com',
        'kaltura.com'
    ]
    
    @classmethod
    def is_valid_video_url(cls, url: str) -> bool:
        """
        Basic validation for video URLs.
        
        Args:
            url: The URL to validate
            
        Returns:
            bool: True if the URL appears to be a valid video URL
        """
        try:
            parsed = urlparse(url)
            
            # Check if URL has a valid scheme
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Check if URL has a domain
            if not parsed.netloc:
                return False
            
            # Check if domain is supported
            domain = parsed.netloc.lower()
            
            # Remove www. prefix for comparison
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Check against supported domains
            for supported_domain in cls.SUPPORTED_DOMAINS:
                if domain == supported_domain or domain.endswith('.' + supported_domain):
                    return True
            
            # Additional checks for common video file extensions
            path = parsed.path.lower()
            video_extensions = ['.mp4', '.webm', '.ogg', '.avi', '.mov', '.wmv', '.flv', '.mkv']
            if any(path.endswith(ext) for ext in video_extensions):
                return True
            
            return False
            
        except Exception:
            return False
    
    @classmethod
    def extract_video_id(cls, url: str) -> str:
        """
        Extract video ID from supported platforms.
        
        Args:
            url: The video URL
            
        Returns:
            str: The extracted video ID or empty string if not found
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # YouTube
            if 'youtube.com' in domain:
                if 'watch' in parsed.path:
                    from urllib.parse import parse_qs
                    query_params = parse_qs(parsed.query)
                    return query_params.get('v', [''])[0]
                elif 'embed' in parsed.path:
                    return parsed.path.split('/')[-1]
            elif 'youtu.be' in domain:
                return parsed.path.lstrip('/')
            
            # Vimeo
            elif 'vimeo.com' in domain:
                return parsed.path.split('/')[-1]
            
            # For other platforms, return the last part of the path
            else:
                return parsed.path.split('/')[-1]
                
        except Exception:
            return ""
