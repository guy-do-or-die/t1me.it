import io
from typing import Optional
from PIL import Image
from playwright.async_api import async_playwright
from ..config.settings import settings
import re
import requests
from PIL import Image, ImageDraw, ImageFont


class ScreenshotService:
    """Service for capturing video screenshots using Playwright."""
    
    def __init__(self):
        pass
    
    def extract_youtube_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
            r'youtube\.com/v/([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    async def create_youtube_thumbnail_fallback(self, url: str, timestamp: float, width: int, height: int) -> Optional[bytes]:
        """Create fallback screenshot using YouTube thumbnail with timestamp overlay"""
        try:
            video_id = self.extract_youtube_video_id(url)
            if not video_id:
                return None
            
            print(f"📷 Creating YouTube thumbnail fallback for {video_id} at {timestamp}s")
            
            # Try different YouTube thumbnail qualities
            thumbnail_urls = [
                f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",  # 1280x720
                f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",     # 480x360
                f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg"      # 320x180
            ]
            
            thumbnail_data = None
            for thumbnail_url in thumbnail_urls:
                try:
                    response = requests.get(thumbnail_url, timeout=10)
                    if response.status_code == 200 and len(response.content) > 1000:  # Not a placeholder
                        thumbnail_data = response.content
                        break
                except:
                    continue
            
            if not thumbnail_data:
                return None
            
            # Load and resize thumbnail
            image = Image.open(io.BytesIO(thumbnail_data))
            image = image.resize((width, height), Image.Resampling.LANCZOS)
            
            # Add timestamp overlay
            draw = ImageDraw.Draw(image)
            
            # Format timestamp
            minutes = int(timestamp // 60)
            seconds = int(timestamp % 60)
            time_text = f"{minutes}:{seconds:02d}"
            
            # Try to use a system font, fallback to default
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            # Add semi-transparent background for text
            text_bbox = draw.textbbox((0, 0), time_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Position in bottom-right corner
            x = width - text_width - 20
            y = height - text_height - 20
            
            # Draw background rectangle
            draw.rectangle([x-10, y-5, x+text_width+10, y+text_height+5], fill=(0, 0, 0, 128))
            
            # Draw timestamp text
            draw.text((x, y), time_text, fill=(255, 255, 255), font=font)
            
            # Convert to bytes
            output = io.BytesIO()
            image.save(output, format='PNG')
            return output.getvalue()
            
        except Exception as e:
            print(f"❌ YouTube thumbnail fallback failed: {e}")
            return None
    
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
        print(f"🎬 Starting fresh screenshot for {url}")
        async with async_playwright() as p:
            # Launch fresh browser for each request to avoid state issues
            browser = await p.chromium.launch(
                headless=True,  # Required for Docker/production environment
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
                    '--disable-blink-features=AutomationControlled',
                    '--disable-ipc-flooding-protection',
                    '--force-device-scale-factor=1',
                    '--disable-features=VizDisplayCompositor,VizHitTestSurfaceLayer',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-background-timer-throttling',
                    '--disable-field-trial-config',
                    '--no-default-browser-check',
                    '--no-first-run',
                    '--disable-default-apps'
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
                    (() => {
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
                    })()
                ''')
                
                # Wait for quality change to take effect
                await page.wait_for_timeout(100)
                
                # Get the video element
                video_element = await page.query_selector('video')
                if not video_element:
                    return None
                
                # Simulate realistic user behavior to avoid bot detection
                print("Simulating user interaction...")
                
                # Move mouse to center of page
                await page.mouse.move(width // 2, height // 2)
                await page.wait_for_timeout(100)
                
                # Click on the page to "focus" it
                await page.click('body')
                await page.wait_for_timeout(200)
                
                # Quick video setup with user simulation
                print("Quick video setup with user simulation...")
                video_setup_success = False
                try:
                    await __import__('asyncio').wait_for(
                        page.evaluate('''
                            (() => {
                                // Simulate user presence
                                document.dispatchEvent(new Event('mousemove'));
                                document.dispatchEvent(new Event('click'));
                                
                                const video = document.querySelector("video");
                                if (video) {
                                    video.muted = true;
                                    // Simulate user clicking play
                                    video.dispatchEvent(new Event('click'));
                                    video.play().catch(e => console.log("Play failed:", e));
                                }
                            })()
                        '''),
                        timeout=5.0
                    )
                    print("✅ Video setup with user simulation completed")
                    video_setup_success = True
                except Exception as e:
                    print(f"⚠️ Video setup timeout/failed: {e}")
                    print("Attempting simpler video setup...")
                    
                    # Try clicking the actual play button
                    try:
                        play_button = await page.query_selector('.ytp-large-play-button, .ytp-play-button')
                        if play_button:
                            await play_button.click()
                            await page.wait_for_timeout(500)
                        
                        await page.evaluate('document.querySelector("video").muted = true')
                        await page.wait_for_timeout(1000)
                        video_setup_success = True
                        print("✅ Simple video setup completed")
                    except:
                        print("❌ Video setup completely failed - may get black screenshot")
                
                # Minimal wait for video to start
                await page.wait_for_timeout(100)
                
                # Check if video has actual content (not black)
                try:
                    video_ready = await __import__('asyncio').wait_for(
                        page.evaluate('''
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
                        '''),
                        timeout=3.0
                    )
                    print(f"✅ Video ready check completed")
                except Exception as e:
                    print(f"⚠️ Video ready check failed/timeout: {e}")
                    video_ready = False
                
                if not video_ready:
                    print("Video not ready, attempting to load content...")
                    
                    # Try to force video to load by playing and waiting
                    try:
                        await __import__('asyncio').wait_for(
                            page.evaluate('''
                                (() => {
                                    const video = document.querySelector("video");
                                    if (video) {
                                        video.muted = true;
                                        video.currentTime = 0;
                                        video.play();
                                    }
                                })()
                            '''),
                            timeout=3.0
                        )
                        await page.wait_for_timeout(2000)  # Give more time for loading
                        
                        # Check if video actually has content now
                        video_has_content = await __import__('asyncio').wait_for(
                            page.evaluate('''
                                (() => {
                                    const video = document.querySelector("video");
                                    if (!video) return false;
                                    return video.videoWidth > 0 && video.videoHeight > 0 && video.readyState >= 2;
                                })()
                            '''),
                            timeout=3.0
                        )
                        
                        if not video_has_content:
                            print("❌ Video still has no content - aborting to avoid black screenshot")
                            return None
                        else:
                            print("✅ Video content loaded successfully")
                            
                    except Exception as e:
                        print(f"❌ Failed to load video content: {e}")
                        return None
                
                # Fast timestamp seeking - go back a few frames for stability
                if timestamp > 0:
                    # Seek back 0.5 seconds for more stable frame (avoid transitions)
                    seek_time = max(0, timestamp + 0.6)
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
                    (() => {
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
                    })()
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
                
                # Try YouTube thumbnail fallback for YouTube URLs
                if 'youtube.com' in url or 'youtu.be' in url:
                    print(f"🔄 Attempting YouTube thumbnail fallback...")
                    try:
                        fallback_screenshot = await self.create_youtube_thumbnail_fallback(url, timestamp, width, height)
                        if fallback_screenshot:
                            print(f"✅ YouTube thumbnail fallback successful!")
                            return fallback_screenshot
                        else:
                            print(f"❌ YouTube thumbnail fallback also failed")
                    except Exception as fallback_error:
                        print(f"❌ YouTube thumbnail fallback error: {fallback_error}")
                
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
