"""
Utility functions for the YouTube Shorts capture tool.
"""

import random
import time


def random_delay(min_sec: float, max_sec: float):
    """Sleep for a random duration to simulate human behavior."""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)
    return delay


