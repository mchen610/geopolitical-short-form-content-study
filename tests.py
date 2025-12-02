"""
Test mode for validating URL classifications.
"""
from seleniumwire import undetected_chromedriver as uc  # type: ignore[import-untyped]

import config
from youtube import (
    ShortMetadata,
    clear_requests,
    extract_short_metadata,
    wait_for_shorts_load,
)


def load_and_extract_single_short(driver: uc.Chrome, url: str, conflict_region: config.ConflictCountry) -> ShortMetadata:
    """Load a Short URL and extract its metadata."""
    driver.get(url)
    wait_for_shorts_load(driver)
    metadata = extract_short_metadata(driver, conflict_region, test_mode=True)
    clear_requests(driver)
    return metadata


def run_test_links(create_driver_fn, setup_directories_fn, conflict_region: config.ConflictCountry | None = None):
    """
    Test mode: Go through each URL for a country (or all countries) and check if it's related.
    Uses the 'test' account, no scrolling - just loads each URL and runs AI classification.
    """
    account_id = "test"
    
    # Build list of countries to test
    if conflict_region:
        countries_to_test: list[config.ConflictCountry] = [conflict_region]
    else:
        countries_to_test = list(config.CONFLICT_URLS.keys())
    
    total_urls = sum(len(config.CONFLICT_URLS[c]) for c in countries_to_test)
    
    print("\n" + "=" * 60)
    if conflict_region:
        print(f"🧪 TEST MODE - Testing {total_urls} URLs for {conflict_region}")
    else:
        print(f"🧪 TEST MODE - Testing {total_urls} URLs across {len(countries_to_test)} countries")
    print("=" * 60)
    
    setup_directories_fn()
    driver = create_driver_fn(account_id)
    
    results: list[dict[str, object]] = []
    url_num = 0
    
    try:
        for country in countries_to_test:
            urls = config.CONFLICT_URLS[country]
            print(f"\n🌍 {country} ({len(urls)} URLs)")
            
            for i, url in enumerate(urls, 1):
                url_num += 1
                print(f"\n📹 [{url_num}/{total_urls}] {country} URL {i}/{len(urls)}: {url}")
                
                try:
                    metadata = load_and_extract_single_short(driver, url, country)
                    
                    status = "✅ RELATED" if metadata["is_conflict_related"] else "❌ NOT RELATED"
                    print(f"   {status}")
                    title = metadata.get('title') or 'N/A'
                    print(f"   Title: {title[:60]}...")
                    print(f"   Channel: {metadata.get('channel') or 'N/A'}")
                    
                    results.append({
                        "country": country,
                        "url": url,
                        "is_related": metadata["is_conflict_related"],
                        "title": metadata.get("title"),
                        "channel": metadata.get("channel"),
                    })
                except Exception as e:
                    print(f"   ⚠️ Error: {e}")
                    results.append({
                        "country": country,
                        "url": url,
                        "is_related": None,
                        "error": str(e),
                    })
        
        # Summary
        print("\n" + "=" * 60)
        print("🧪 TEST RESULTS SUMMARY")
        print("=" * 60)
        related = sum(1 for r in results if r.get("is_related") is True)
        not_related = sum(1 for r in results if r.get("is_related") is False)
        errors = sum(1 for r in results if r.get("is_related") is None)
        print(f"   Related: {related}")
        print(f"   Not related: {not_related}")
        print(f"   Errors: {errors}")
        print(f"   Total: {len(results)}")
        
        for i, r in enumerate(results, 1):
            status = "✅" if r.get("is_related") else ("⚠️" if r.get("is_related") is None else "❌")
            print(f"   {i}. {status} [{r['country']}] {r['url']}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    
    finally:
        print("\n🔒 Closing browser...")
        driver.quit()
    
    return True

