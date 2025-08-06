import io
from typing import Optional
from PIL import Image
from playwright.async_api import async_playwright
from ..config.settings import settings


class ScreenshotService:
    """Service for capturing video screenshots using Playwright."""
    
    async def capture_video_screenshot(
        self, 
        url: str, 
        timestamp: float, 
        width: int, 
        height: int
    ) -> Optional[bytes]:
        """
        Capture a screenshot from a video at the specified timestamp.
        
        Args:
            url: Video URL
            timestamp: Timestamp in seconds
            width: Screenshot width
            height: Screenshot height
            
        Returns:
            Screenshot bytes or None if failed
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--autoplay-policy=no-user-gesture-required'
                ]
            )
            
            try:
                context = await browser.new_context(
                    viewport={'width': width, 'height': height},
                    user_agent=settings.USER_AGENT
                )
                
                page = await context.new_page()
                
                # Navigate to the video URL
                await page.goto(url, wait_until='networkidle', timeout=settings.BROWSER_TIMEOUT)
                
                # Wait for video element to load
                await page.wait_for_selector('video', timeout=10000)
                
                # Force maximum video quality
                await page.evaluate('''
                    // For YouTube, set quality to highest available
                    if (window.location.hostname.includes('youtube.com') || window.location.hostname.includes('youtu.be')) {
                        const video = document.querySelector('video');
                        if (video && video.getVideoPlaybackQuality) {
                            // Try to access YouTube's internal player API
                            const player = document.querySelector('#movie_player');
                            if (player && player.setPlaybackQualityRange) {
                                player.setPlaybackQualityRange('hd2160', 'hd2160'); // 4K
                                player.setPlaybackQuality('hd2160');
                            } else if (player && player.setPlaybackQuality) {
                                player.setPlaybackQuality('hd1080'); // 1080p fallback
                            }
                        }
                    }
                    
                    // For other platforms, try to set video quality via standard methods
                    const video = document.querySelector('video');
                    if (video) {
                        // Set video to highest quality if quality selector exists
                        const qualityButtons = document.querySelectorAll('[data-quality], .quality-selector, .vjs-quality-selector');
                        if (qualityButtons.length > 0) {
                            const highestQuality = Array.from(qualityButtons).find(btn => 
                                btn.textContent.includes('1080') || 
                                btn.textContent.includes('720') ||
                                btn.textContent.includes('HD')
                            );
                            if (highestQuality) {
                                highestQuality.click();
                            }
                        }
                    }
                ''')
                
                # Wait for quality change to take effect
                await page.wait_for_timeout(1000)
                
                # Get the video element
                video_element = await page.query_selector('video')
                if not video_element:
                    return None
                
                # Seek to the specified timestamp
                if timestamp > 0:
                    await page.evaluate(f'document.querySelector("video").currentTime = {timestamp}')
                    
                    # Immediately pause the video to prevent it from continuing to play
                    await page.evaluate('document.querySelector("video").pause()')
                    
                    # Wait for the video to seek to the correct position
                    await page.wait_for_timeout(500)
                    
                    # Verify we're at the correct timestamp (with some tolerance)
                    current_time = await page.evaluate('document.querySelector("video").currentTime')
                    if abs(current_time - timestamp) > 2:  # 2 second tolerance
                        # Try seeking again
                        await page.evaluate(f'document.querySelector("video").currentTime = {timestamp}')
                        await page.evaluate('document.querySelector("video").pause()')
                        await page.wait_for_timeout(500)
                else:
                    # For timestamp 0, also pause to ensure we get the exact first frame
                    await page.evaluate('document.querySelector("video").pause()')
                
                # Enter fullscreen mode for maximum resolution capture
                await page.evaluate('''
                    const video = document.querySelector("video");
                    if (video.requestFullscreen) {
                        video.requestFullscreen();
                    } else if (video.webkitRequestFullscreen) {
                        video.webkitRequestFullscreen();
                    } else if (video.mozRequestFullScreen) {
                        video.mozRequestFullScreen();
                    }
                ''')
                
                # Wait for fullscreen transition
                await page.wait_for_timeout(300)
                
                # Wait a bit for the frame to render
                await page.wait_for_timeout(500)
                
                # Take screenshot of the video element
                screenshot_bytes = await video_element.screenshot(type='png')
                
                return screenshot_bytes
                
            except Exception as e:
                print(f"Error capturing screenshot: {e}")
                return None
                
            finally:
                await browser.close()
    
    async def process_screenshot(self, screenshot_bytes: bytes, width: int, height: int) -> bytes:
        """
        Process and optimize the screenshot.
        
        Args:
            screenshot_bytes: Raw screenshot bytes
            width: Target width
            height: Target height
            
        Returns:
            Processed screenshot bytes
        """
        try:
            # Open image with PIL
            image = Image.open(io.BytesIO(screenshot_bytes))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if needed
            if image.size != (width, height):
                image = image.resize((width, height), Image.Resampling.LANCZOS)
            
            # Save as JPEG with optimization
            output = io.BytesIO()
            image.save(
                output, 
                format='JPEG', 
                quality=85, 
                optimize=True,
                progressive=True
            )
            
            return output.getvalue()
            
        except Exception as e:
            print(f"Error processing screenshot: {e}")
            return screenshot_bytes  # Return original if processing fails


# Global screenshot service instance
screenshot_service = ScreenshotService()
