"""
YouTube Shorts extraction - DOM interactions and network capture.
"""

import json
from datetime import datetime
import time
from zoneinfo import ZoneInfo
from typing import TypedDict

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from seleniumwire.undetected_chromedriver import Chrome  # type: ignore[import-untyped]

import config
from llm import is_conflict_related
from utils import random_delay

SHORTS_PLAYER = "ytd-shorts, ytd-reel-video-renderer"
TITLE = "h2.ytShortsVideoTitleViewModelShortsVideoTitle"
CHANNEL = ".ytReelChannelBarViewModelChannelName a"
LIKE_BUTTON = 'button[aria-label^="like this video"]'


class ShortMetadata(TypedDict):
    url: str
    extracted_at: str
    video_id: str
    view_index: int

    title: str | None
    channel: str | None
    transcript: str | None
    is_conflict_related: bool


def wait_for_shorts_load(driver: Chrome, timeout: int = 30):
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, SHORTS_PLAYER))
    )
    random_delay(2, 3)
    click_play(driver)


def click_play(driver: Chrome):
    """Click the large play button to start playback."""
    try:
        play_btn = driver.find_element(By.CSS_SELECTOR, ".ytp-large-play-button")
        play_btn.click()
    except Exception:
        print("   Play button not found or not clickable")


def get_text(driver: Chrome, selector: str) -> str | None:
    """Get text from element, with retry for stale elements."""
    for _ in range(10):
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if not elements:
                return None
            text = elements[0].text.strip()
            return text.replace('\n', '. ') if text else None
        except StaleElementReferenceException:
                time.sleep(0.1)
                continue
    return None

def extract_transcript(data: dict) -> str | None:
    """Extract joined transcript from timedtext endpoint response JSON."""
    texts = []
    for event in data["events"]:
        if "segs" not in event:
            continue
        text = " ".join(seg["utf8"].strip() for seg in event["segs"]).replace("  ", " ")
        texts.append(text)
    transcript = " ".join(texts)
    return transcript if transcript else None

def get_transcript(driver: Chrome, video_id: str) -> str | None:
    for req in driver.requests:
        if "timedtext" in req.url and video_id in req.url and req.response:
            body = req.response.body.decode("utf-8")
            return extract_transcript(json.loads(body))
    # This means the video simply doesn't have a transcript       
    return None
    


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


def extract_short_metadata(driver: Chrome, view_index: int, conflict_region: config.ConflictCountry) -> ShortMetadata:
    """Extract metadata from the currently visible Short."""
    url = driver.current_url
    print()
    print(f"   Short {view_index} - {url}")
    
    title = get_text(driver, TITLE)
    print(f"   Title: {title}")


    video_id = url.split("/shorts/")[-1]
    transcript = get_transcript(driver, video_id)
    if transcript:
        print(f"   Transcript: {transcript[:70]}...({len(transcript.split(' '))} words)")
    else:
        print(f"   Transcript: {transcript}")

    channel = get_text(driver, CHANNEL)
    is_related = is_conflict_related(conflict_region=conflict_region, title=title, channel=channel, transcript=transcript)
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
