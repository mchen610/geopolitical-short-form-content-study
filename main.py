"""
Main entry point for YouTube Shorts geopolitical conflict study.
"""
import argparse
import sys

import config
from driver import CHROME_PROFILES_DIR, create_driver, setup_directories, run_setup
from experiment import run_full_experiment
from home import run_home_feed
from tests import run_test_links


def main():
    parser = argparse.ArgumentParser(
        description="Capture YouTube Shorts feed and like conflict-related content",
        epilog="First run: python main.py --account profile_1 --setup"
    )
    
    parser.add_argument("--account", "-a", help="Account ID from config.py")
    parser.add_argument("--setup", "-s", action="store_true", help="Setup: log into YouTube")
    parser.add_argument("--list-accounts", "-l", action="store_true", help="List accounts")
    parser.add_argument("--run", "-r", action="store_true", help="Run full training experiment for account")
    parser.add_argument("--home", action="store_true", help="Run home feed measurement (Phase 2)")
    parser.add_argument("--test", "-t", nargs="?", const="ALL", metavar="COUNTRY", help="Test URLs (all countries if none specified, uses test account)")
    
    args = parser.parse_args()
    
    if args.list_accounts:
        print("\nAccounts and their country orders:")
        for acc_id in config.ACCOUNTS:
            profile_path = CHROME_PROFILES_DIR / acc_id
            status = "✅" if profile_path.exists() else "❌ needs --setup"
            order = config.ACCOUNT_COUNTRY_ORDER[acc_id]
            print(f"  {acc_id}: {status}")
            if order:
                print(f"    Order: {' → '.join(order)}")
        return
    
    if args.test:
        if args.test == "ALL":
            # Test all countries
            success = run_test_links(create_driver, setup_directories, None)
        else:
            # Validate country
            valid_countries = list(config.CONFLICT_URLS.keys())
            if args.test not in valid_countries:
                print(f"❌ Unknown country: {args.test}")
                print(f"   Valid countries: {valid_countries}")
                sys.exit(1)
            success = run_test_links(create_driver, setup_directories, args.test)
        sys.exit(0 if success else 1)
    
    if not args.account:
        print("❌ Please specify an account with --account")
        print("   Use --list-accounts to see available accounts")
        sys.exit(1)
    
    if args.setup:
        success = run_setup(args.account)
        sys.exit(0 if success else 1)
    
    if args.run:
        success = run_full_experiment(args.account)
        sys.exit(0 if success else 1)
    
    if args.home:
        success = run_home_feed(args.account)
        sys.exit(0 if success else 1)
    
    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()
