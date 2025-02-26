"""Erasmus Intern Traineeship Scraper Tool"""

import os
import sys
import argparse
import json
import traceback
from typing import Dict, Any, List  # Add missing imports for type hints

from src.scraper import ErasmusInternScraper
from src.utils import load_config, validate_config


def setup_argparse() -> argparse.ArgumentParser:
    """Set up command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Erasmus Intern Traineeship Scraper Tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Scrape job listings")
    scrape_parser.add_argument("--max-pages", type=int, default=0,
                      help="Maximum number of pages to scrape (0 means all pages)")
    scrape_parser.add_argument("--no-details", action="store_true",
                      help="Skip fetching detailed information for each traineeship")
    scrape_parser.add_argument("--output", type=str, default=None,
                      help="Output filename (default: erasmusintern_traineeships_YYYY-MM-DD.csv)")
    
    # Search command - simplified without AI options
    search_parser = subparsers.add_parser("search", help="Search job listings")
    search_parser.add_argument("query", type=str, help="Search query (job title, skills, etc.)")
    search_parser.add_argument("--data", type=str, default=None,
                      help="Path to job data file (JSON or CSV)")
    search_parser.add_argument("--limit", type=int, default=5,
                      help="Maximum number of results to return")
    
    return parser


def scrape_command(args, config):
    """Run the scraper."""
    print("=== Starting traineeship scraper ===")
    
    try:
        max_pages = args.max_pages if args.max_pages is not None else config["max_pages"]
        get_details = not args.no_details
        
        scraper = ErasmusInternScraper(base_url=config["base_url"], data_dir=config["data_dir"])
        traineeships = scraper.scrape_all(max_pages=max_pages, get_details=get_details)
        
        if not traineeships:
            print("No traineeships found. Check connection or website structure.")
            return
        
        # Clean up null values
        for t in traineeships:
            for key, value in t.items():
                if value is None:
                    t[key] = "Not specified"
        
        # Save data
        output_file = scraper.save_to_csv(traineeships, args.output)
        if output_file:
            print(f"Data saved to {output_file}")
        else:
            print("Failed to save data.")
        
        # Also save as JSON for better compatibility with other tools
        json_file = scraper.save_to_json(traineeships)
        if json_file:
            print(f"Data also saved as JSON to {json_file}")
    
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
        traceback.print_exc()


def search_command(args, config):
    """Run the job search with basic search functionality only."""
    print(f"=== Searching for: {args.query} ===")
    
    try:
        searcher = JobSearch(data_path=args.data, config=config)
        
        # Always use basic search (no AI)
        results = searcher.search_jobs(args.query, limit=args.limit, use_ai=False)
        
        if not results:
            print("No matching jobs found.")
            return
        
        # Display results
        print(f"\nFound {len(results)} matching jobs:\n")
        for i, job in enumerate(results):
            print(f"{i+1}. {job.get('title', 'No title')} - {job.get('company', 'No company')}")
            print(f"   Location: {job.get('location', 'Not specified')}")
            print(f"   Relevance: {job.get('relevance_score', 0)}/100")
            print(f"   URL: {job.get('url', 'No URL')}")
            print()  # Add a blank line between each result
    
    except Exception as e:
        print(f"Error during search: {str(e)}")
        traceback.print_exc()


def main():
    """Main entry point."""
    parser = setup_argparse()
    args = parser.parse_args()
    
    config = load_config()
    if not validate_config(config):
        sys.exit(1)
    
    if args.command == "scrape":
        scrape_command(args, config)
    elif args.command == "search":
        search_command(args, config)
    else:
        # Default to scrape if no command specified (for backward compatibility)
        scrape_command(args, config)


if __name__ == "__main__":
    main()