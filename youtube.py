"""
YouTube Shorts selector actions and DOM interactions.
"""

from datetime import datetime
from typing import TypedDict

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from utils import human_delay

# CSS Selectors
TITLE_SELECTOR = "h2.ytShortsVideoTitleViewModelShortsVideoTitle span"
CHANNEL_SELECTOR = ".ytReelChannelBarViewModelChannelName a"
SHORTS_PLAYER_SELECTOR = "ytd-shorts, ytd-reel-video-renderer, #shorts-player"
LIKE_BUTTON_SELECTOR = 'button[aria-label*="like this video"]'


class ShortMetadata(TypedDict, total=False):
    url: str
    extracted_at: str
    title: str
    channel: str
    video_id: str


def wait_for_shorts_load(driver: WebDriver, timeout: int = 30) -> bool:
    """
    Wait for YouTube Shorts to load.
    Returns True if loaded, False if error.
    """
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, SHORTS_PLAYER_SELECTOR))
        )
        human_delay(2, 3)
        return True
    except TimeoutException:
        print("❌ Timeout waiting for Shorts to load")
        if "youtube.com" not in driver.current_url:
            print("   Not on YouTube - check if logged in")
        return False


def get_title(driver: WebDriver) -> str:
    """Extract video title from the current Short."""
    return driver.find_element(By.CSS_SELECTOR, TITLE_SELECTOR).text.strip()


def get_channel(driver: WebDriver) -> str:
    """Extract channel name from the current Short."""
    return driver.find_element(By.CSS_SELECTOR, CHANNEL_SELECTOR).text.strip()


def extract_current_short_metadata(driver: WebDriver) -> ShortMetadata:
    """Extract metadata from the currently visible Short."""
    url = driver.current_url
    metadata: ShortMetadata = {
        "url": url,
        "extracted_at": datetime.now().isoformat(),
        "title": get_title(driver),
        "channel": get_channel(driver),
    }
    
    if "/shorts/" in url:
        metadata["video_id"] = url.split("/shorts/")[-1].split("?")[0]
    
    return metadata


def click_like_button(driver: WebDriver) -> tuple[bool, str]:
    """
    Click the like button on the current Short.
    Returns (success, status) where status is "liked", "already_liked", or "failed".
    """
    try:
        like_button = driver.find_element(By.CSS_SELECTOR, LIKE_BUTTON_SELECTOR)
        
        is_already_liked = like_button.get_attribute("aria-pressed") == "true"
        if is_already_liked:
            return True, "already_liked"
        
        like_button.click()
        return True, "liked"
    except Exception as e:
        print(f"   ⚠️  Could not click like: {e}")
        return False, "failed"


def swipe_to_next_short(driver: WebDriver) -> bool:
    """Swipe/scroll to the next Short. Returns True if successful."""
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.ARROW_DOWN)
        return True
    except Exception as e:
        print(f"   Swipe failed: {e}")
        return False

