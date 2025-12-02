"""
Shared driver creation and setup utilities.
"""
from pathlib import Path

from seleniumwire import undetected_chromedriver as uc  # type: ignore[import-untyped]

import config

# Directory for this script's dedicated Chrome profiles
CHROME_PROFILES_DIR = Path("./chrome_profiles")


def setup_directories():
    """Create output directory if it doesn't exist."""
    config.OUTPUT_DIR.mkdir(exist_ok=True)
    CHROME_PROFILES_DIR.mkdir(exist_ok=True)


def create_driver(account_id: str, setup_mode: bool = False) -> uc.Chrome:
    """
    Create an undetected Chrome driver with a dedicated profile for this account.
    """
    if account_id not in config.ACCOUNTS:
        raise ValueError(f"Unknown account: {account_id}. Check config.py")
    
    # Use dedicated profile directory for this script
    profile_path = CHROME_PROFILES_DIR / account_id
    
    if not profile_path.exists() and not setup_mode:
        print(f"❌ Profile not set up for account: {account_id}")
        print(f"   Run: python main.py --account {account_id} --setup")
        raise ValueError("Profile not set up. Run with --setup first.")
    
    options = uc.ChromeOptions()
    
    # Use dedicated profile directory
    options.add_argument(f"--user-data-dir={profile_path.absolute()}")
    
    # Window size
    options.add_argument(f"--window-size={config.VIEWPORT_WIDTH},{config.VIEWPORT_HEIGHT}")
    
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--mute-audio")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--ignore-certificate-errors")
    
    # Selenium Wire options - only capture timedtext requests to reduce proxy load
    seleniumwire_options = {
        'disable_encoding': True,
        'include_urls': [
            '.*timedtext.*',
        ],
    }
    
    driver = uc.Chrome(
        options=options,
        seleniumwire_options=seleniumwire_options,
        version_main=142,  # Match your Chrome browser version
        window_height=config.VIEWPORT_HEIGHT,
        window_width=config.VIEWPORT_WIDTH,
    )
    return driver


def run_setup(account_id: str) -> bool:
    """Open browser for manual YouTube login. Profile is saved for future sessions."""
    if account_id not in config.ACCOUNTS:
        print(f"❌ Unknown account: {account_id}")
        return False
    
    print("   1. Browser will open")
    print("   2. Log into Google")
    print("   3. Close browser when done")
    
    setup_directories()
    driver = create_driver(account_id, setup_mode=True)
    while True:
        try:
            _ = driver.current_url
        except KeyboardInterrupt:
            print("\n⚠️  Aborted")
            driver.quit()
            return False
        except Exception:
            break
    print("✅ Setup complete!")
    driver.quit()
    return True

