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
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--autoplay-policy=no-user-gesture-required',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--mute-audio',
                    '--disable-blink-features=AutomationControlled',  # Hide automation
                    '--disable-ipc-flooding-protection'
                ]
            )
            
            try:
                context = await browser.new_context(
                    viewport={'width': width, 'height': height},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    locale='en-US',
                    timezone_id='America/New_York',
                    extra_http_headers={
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
                    }
                )
                
                # Add stealth scripts to avoid detection
                await context.add_init_script("""
                    // Remove webdriver property
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                    
                    // Mock plugins
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5],
                    });
                    
                    // Mock languages
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en'],
                    });
                """)
                
                page = await context.new_page()
                
                # Convert youtu.be URLs to direct youtube.com URLs to bypass consent
                if 'youtu.be' in url:
                    video_id = url.split('/')[-1].split('?')[0]
                    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                    if 't=' in url:
                        timestamp_param = url.split('t=')[1].split('&')[0]
                        youtube_url += f"&t={timestamp_param}"
                    print(f"Converting to direct YouTube URL: {youtube_url}")
                    url = youtube_url
                
                # Navigate directly to the video URL
                print(f"Navigating to URL: {url}")
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                
                # Fast video element detection - no waiting around!
                print("Fast video detection...")
                await page.wait_for_timeout(100)  # Minimal wait
                
                # Try to find video element with YouTube-specific approach
                video_found = False
                video_element = None
                
                # YouTube-specific selectors in order of preference
                youtube_selectors = [
                    'video.video-stream',  # Primary YouTube video element
                    'video[src]',          # Any video with src
                    'video',               # Any video element
                    '.html5-video-player video',  # YouTube HTML5 player
                    '#movie_player video'  # YouTube movie player
                ]
                
                for selector in youtube_selectors:
                    try:
                        print(f"Trying selector: {selector}")
                        await page.wait_for_selector(selector, timeout=2000)  # Fast timeout
                        video_element = await page.query_selector(selector)
                        if video_element:
                            print(f"Found video element with selector: {selector}")
                            video_found = True
                            break
                    except Exception as e:
                        print(f"Selector {selector} failed: {e}")
                        continue
                
                if not video_found:
                    # Quick play button attempt - no long waits
                    try:
                        print("Quick play button attempt...")
                        play_selectors = [
                            '.ytp-large-play-button',
                            '.ytp-play-button',
                            'button[aria-label*="Play"]',
                            '.play-button'
                        ]
                        
                        for play_selector in play_selectors:
                            try:
                                play_button = await page.query_selector(play_selector)
                                if play_button:
                                    await play_button.click()
                                    await page.wait_for_timeout(500)  # Quick wait
                                    
                                    # Quick video check after play
                                    for selector in youtube_selectors:
                                        try:
                                            await page.wait_for_selector(selector, timeout=1000)  # Fast
                                            video_element = await page.query_selector(selector)
                                            if video_element:
                                                print(f"Found video after play click: {selector}")
                                                video_found = True
                                                break
                                        except:
                                            continue
                                    
                                    if video_found:
                                        break
                            except:
                                continue
                    except Exception as e:
                        print(f"Play button click failed: {e}")
                
                if not video_found:
                    print(f"No video element found for URL: {url}")
                    print("Page content:")
                    content = await page.content()
                    print(content[:1000])  # Print first 1000 chars for debugging
                    return None
                    
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
                await page.wait_for_timeout(100)
                
                # Get the video element
                video_element = await page.query_selector('video')
                if not video_element:
                    return None
                
                # Quick video setup - no delays!
                print("Quick video setup...")
                await page.evaluate('''
                    const video = document.querySelector("video");
                    if (video) {
                        video.muted = true;  // Ensure muted for autoplay
                        video.play().catch(e => console.log("Play failed:", e));
                    }
                ''')
                
                # Minimal wait for video to start
                await page.wait_for_timeout(100)
                
                # Check if video has actual content (not black)
                video_ready = await page.evaluate('''
                    (() => {
                        const video = document.querySelector("video");
                        if (!video) return false;
                        
                        // Check if video has loaded some data
                        const hasData = video.readyState >= 2; // HAVE_CURRENT_DATA
                        const hasSize = video.videoWidth > 0 && video.videoHeight > 0;
                        const duration = video.duration > 0;
                        
                        console.log("Video readyState:", video.readyState);
                        console.log("Video dimensions:", video.videoWidth, "x", video.videoHeight);
                        console.log("Video duration:", video.duration);
                        
                        return hasData && hasSize && duration;
                    })()
                ''')
                
                if not video_ready:
                    print("Video not ready, quick retry...")
                    await page.wait_for_timeout(100)  # Quick retry
                    
                    # Quick play button retry
                    await page.evaluate('''
                        const playButtons = document.querySelectorAll('.ytp-large-play-button, .ytp-play-button');
                        playButtons.forEach(btn => {
                            if (btn && btn.click) btn.click();
                        });
                    ''')
                    
                    await page.wait_for_timeout(100)  # Quick wait
                
                # Fast timestamp seeking - go back a few frames for stability
                if timestamp > 0:
                    # Seek back 0.5 seconds for more stable frame (avoid transitions)
                    seek_time = max(0, timestamp + 0.5)
                    print(f"Fast seek to: {seek_time} (requested: {timestamp})")
                    await page.evaluate(f'''
                        const video = document.querySelector("video");
                        if (video) {{
                            video.currentTime = {seek_time};
                            video.pause();
                        }}
                    ''')
                    
                    # Quick seek verification
                    await page.wait_for_timeout(100)
                    current_time = await page.evaluate('document.querySelector("video").currentTime')
                    print(f"Seeked to: {current_time} (target: {seek_time})")
                    
                    # One quick retry if needed
                    if abs(current_time - seek_time) > 2:
                        await page.evaluate(f'document.querySelector("video").currentTime = {seek_time}')
                        await page.wait_for_timeout(100)
                else:
                    # Quick pause at start
                    await page.evaluate('document.querySelector("video").pause()')
                    await page.wait_for_timeout(100)
                
                # Hide YouTube player controls for cleaner screenshot
                await page.evaluate('''
                    // Hide YouTube player controls
                    const controls = document.querySelectorAll(
                        '.ytp-chrome-bottom, .ytp-chrome-top, .ytp-gradient-bottom, .ytp-gradient-top, ' +
                        '.ytp-progress-bar-container, .ytp-chrome-controls, .ytp-pause-overlay, ' +
                        '.ytp-big-mode .ytp-chrome-bottom, .ytp-big-mode .ytp-chrome-top'
                    );
                    controls.forEach(el => {
                        if (el) el.style.display = 'none';
                    });
                    
                    // Also hide any overlay elements
                    const overlays = document.querySelectorAll('.ytp-paid-content-overlay, .ytp-ce-element');
                    overlays.forEach(el => {
                        if (el) el.style.display = 'none';
                    });
                ''');
                
                # Quick wait for controls to hide
                await page.wait_for_timeout(100)
                
                # Take screenshot with detailed error logging
                print("Taking screenshot of video element...")
                try:
                    screenshot_bytes = await video_element.screenshot(type='png')
                    print(f"Screenshot captured successfully, size: {len(screenshot_bytes)} bytes")
                    return screenshot_bytes
                except Exception as screenshot_error:
                    print(f"Screenshot capture failed: {screenshot_error}")
                    try:
                        video_details = await video_element.evaluate('el => ({tagName: el.tagName, width: el.videoWidth, height: el.videoHeight, readyState: el.readyState})')
                        print(f"Video element details: {video_details}")
                    except:
                        print("Could not get video element details")
                    raise screenshot_error
                    
            except Exception as e:
                print(f"Error in capture_video_screenshot: {e}")
                import traceback
                print(f"Full traceback: {traceback.format_exc()}")
                return None
            finally:
                try:
                    await browser.close()
                except:
                    pass

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
