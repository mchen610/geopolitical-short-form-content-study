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

from llm import is_conflict_related
from utils import random_delay

# CSS Selectors
TITLE_SELECTOR = "h2.ytShortsVideoTitleViewModelShortsVideoTitle span"
CHANNEL_SELECTOR = ".ytReelChannelBarViewModelChannelName a"
SHORTS_PLAYER_SELECTOR = "ytd-shorts, ytd-reel-video-renderer, #shorts-player"
LIKE_BUTTON_SELECTOR = 'button[aria-label*="like this video"]'


class ShortMetadata(TypedDict):
    url: str
    extracted_at: str
    title: str
    channel: str
    video_id: str
    view_index: int
    is_conflict_related: bool


def wait_for_shorts_load(driver: WebDriver, timeout: int = 30):
    """
    Wait for YouTube Shorts to load.
    """
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, SHORTS_PLAYER_SELECTOR))
    )
    random_delay(2, 3)

def get_title(driver: WebDriver) -> str:
    """Extract video title from the current Short."""
    return driver.find_element(By.CSS_SELECTOR, TITLE_SELECTOR).text.strip()


def get_channel(driver: WebDriver) -> str:
    """Extract channel name from the current Short."""
    return driver.find_element(By.CSS_SELECTOR, CHANNEL_SELECTOR).text.strip()


def extract_current_short_metadata(
    driver: WebDriver, view_index: int
) -> ShortMetadata:
    """Extract metadata from the currently visible Short."""
    url = driver.current_url
    video_id = url.split("/shorts/")[-1].split("?")[0]
    title = get_title(driver) 
    channel = get_channel(driver)
    return {
        "url": url,
        "extracted_at": datetime.now().isoformat(),
        "title": get_title(driver),
        "channel": get_channel(driver),
        "video_id": video_id,
        "view_index": view_index,
        "is_conflict_related": is_conflict_related(title=title, channel=channel),
    }


def click_like_button(driver: WebDriver) -> None:
    """Click the like button on the current Short if not already liked."""
    like_button = driver.find_element(By.CSS_SELECTOR, LIKE_BUTTON_SELECTOR)
    
    if like_button.get_attribute("aria-pressed") == "true":
        return
    
    like_button.click()


def swipe_to_next_short(driver: WebDriver) -> bool:
    """Swipe/scroll to the next Short. Returns True if successful."""
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.ARROW_DOWN)
        return True
    except Exception as e:
        print(f"   Swipe failed: {e}")
        return False

