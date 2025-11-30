"""
YouTube Shorts extraction - DOM interactions and network capture.
"""

import json
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import TypedDict

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumwire.undetected_chromedriver import Chrome  # type: ignore[import-untyped]

import config
from llm import is_conflict_related
from utils import random_delay

SHORTS_PLAYER = "ytd-shorts, ytd-reel-video-renderer"
TITLE = "h2.ytShortsVideoTitleViewModelShortsVideoTitle"
CHANNEL = ".ytReelChannelBarViewModelChannelName a"
LIKE_BUTTON = 'button[aria-label*="like this video"]'


class ShortMetadata(TypedDict):
    url: str
    extracted_at: str
    title: str
    channel: str
    video_id: str
    view_index: int
    is_conflict_related: bool
    transcript: str


def wait_for_shorts_load(driver: Chrome, timeout: int = 30):
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, SHORTS_PLAYER))
    )
    random_delay(2, 3)


def get_text(driver: Chrome, selector: str) -> str:
    """Get text from element, empty string if not found."""
    elements = driver.find_elements(By.CSS_SELECTOR, selector)
    return elements[0].text.strip() if elements else ""


def extract_transcript(data: dict) -> str:
    """Extract joined transcript from timedtext JSON."""
    texts = []
    for event in data["events"]:
        if "segs" not in event:
            continue
        text = "".join(seg["utf8"] for seg in event["segs"]).strip()
        texts.append(text)
    return " ".join(texts)


def get_transcript(driver: Chrome, video_id: str) -> str:
    for req in driver.requests:
        if "timedtext" in req.url and video_id in req.url and req.response:
            body = req.response.body.decode("utf-8")
            return extract_transcript(json.loads(body))
    # This means the video simply doesn't have a transcript       
    return ""
    


def clear_requests(driver: Chrome):
    del driver.requests


def click_like(driver: Chrome):
    """Click the like button if not already liked."""
    try:
        btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, LIKE_BUTTON))
        )
        if btn.get_attribute("aria-pressed") == "true":
            return
        ActionChains(driver).move_to_element(btn).click(btn).perform()
    except Exception:
        print("   Like button not found or not clickable")


def extract_short_metadata(driver: Chrome, view_index: int) -> ShortMetadata:
    """Extract metadata from the currently visible Short."""
    url = driver.current_url

    video_id = url.split("/shorts/")[-1]
    print(f"   Short {view_index} - {url}")
    
    title = get_text(driver, TITLE)
    print(f"   Title: {title}")

    channel = get_text(driver, CHANNEL)

    transcript = get_transcript(driver, video_id)
    truncated_transcript = transcript[:70] + "..." + (f"({len(transcript.split(' '))} words)") if transcript else None
    print(f"   Transcript: {truncated_transcript}")

    is_related = is_conflict_related(topic=config.TOPIC, title=title, channel=channel, transcript=transcript)
    if is_related:
        click_like(driver)
        print("   ❤️ Liked!")
    else:
        print("   ❌ Ignored")
    
    return {
        "url": url,
        "extracted_at": datetime.now(ZoneInfo('America/New_York')).isoformat(),
        "title": title,
        "channel": channel,
        "video_id": video_id,
        "view_index": view_index,
        "is_conflict_related": is_related,
        "transcript": transcript,
    }


def swipe_to_next_short(driver: Chrome) -> bool:
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ARROW_DOWN)
        return True
    except Exception as e:
        print(f"   Swipe failed: {e}")
        return False
