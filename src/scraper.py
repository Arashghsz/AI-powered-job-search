import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional


class ErasmusInternScraper:
    """
    A scraper for collecting traineeship listings from erasmusintern.org
    """
    
    def __init__(self, base_url: str = "https://erasmusintern.org/traineeships", data_dir: str = "data"):
        """Initialize the scraper with the base URL and data directory."""
        self.base_url = base_url
        self.data_dir = data_dir
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize session for making requests
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        })
    
    def get_total_pages(self) -> int:
        """Get the total number of pages of traineeships."""
        response = self.session.get(self.base_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        try:
            # Try to find the last page number
            pager = soup.select('.pager-last a')
            if pager:
                href = pager[0].get('href', '')
                if 'page=' in href:
                    return int(href.split('page=')[1]) + 1
            
            # If no last page button, try counting page items
            pager_items = soup.select('.pager-item a, .pager-current')
            if pager_items:
                pages = []
                for item in pager_items:
                    try:
                        if 'href' in item.attrs:
                            num = int(item['href'].split('page=')[1]) + 1
                        else:
                            num = int(item.text.strip())
                        pages.append(num)
                    except (ValueError, IndexError):
                        continue
                return max(pages) if pages else 1
            
            return 1
            
        except Exception as e:
            print(f"Error determining total pages: {e}")
            return 1

    def scrape_traineeship_listings(self, page_num: int) -> List[Dict[str, Any]]:
        """Scrape the traineeship listings from a specific page."""
        # Build URL properly with query parameters
        if '?' in self.base_url:
            url = f"{self.base_url}&page={page_num-1}"
        else:
            url = f"{self.base_url}?page={page_num-1}"
            
        print(f"Scraping page {page_num}: {url}")
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            traineeships = []
            # Look for individual traineeship items
            listing_container = soup.select('.media-list-items')
            
            if not listing_container:
                print("Debug: Container not found, trying alternative selector")
                listing_container = soup.select('.view-content > div')
            
            print(f"Debug: Found {len(listing_container)} containers")
            
            for container in listing_container:
                try:
                    # Title and link
                    title_elem = container.select_one('.field-name-title a, h3.dot-title a')
                    if not title_elem:
                        # Try alternate selectors for the title
                        title_elem = container.select_one('h3.title a, .media-body a')
                    
                    if not title_elem:
                        print("Skipping item - no title found")
                        continue
                        
                    title = title_elem.text.strip()
                    link = title_elem['href']
                    if not link.startswith('http'):
                        link = f"https://erasmusintern.org{link}"
                    
                    # Add debug print for link
                    print(f"Found link: {link}")
                    
                    # Company name
                    company_elem = container.select_one('.field-name-recruiter-name .field-item a')
                    company = company_elem.text.strip() if company_elem else "Not specified"
                    
                    # Location
                    country_elem = container.select_one('.field-name-field-traineeship-location-count .field-item')
                    city_elem = container.select_one('.field-name-field-traineeship-location-city .field-item')
                    location = ""
                    if city_elem and country_elem:
                        location = f"{city_elem.text.strip()}, {country_elem.text.strip()}"
                    elif country_elem:
                        location = country_elem.text.strip()
                    else:
                        location = "Not specified"
                    
                    # Duration - complete refactor with debug info
                    duration = "Not specified"
                    print("Debug - Looking for duration")
                    # Try all possible selectors in order
                    duration_selectors = [
                        '.ds-top-footer .field-name-field-traineeship-duration .field-items .field-item',
                        '.ds-top-footer .field-name-field-traineeship-duration',
                        '.field-name-field-traineeship-duration .field-item',
                        '.field-type-taxonomy-term-reference.field-name-field-traineeship-duration .field-items .field-item'
                    ]
                    
                    for selector in duration_selectors:
                        duration_elem = container.select_one(selector)
                        if duration_elem:
                            # Get the text and remove any labels
                            text = duration_elem.get_text(strip=True)
                            if "Duration:" in text:
                                duration = text.replace("Duration:", "").strip()
                            else:
                                duration = text
                            print(f"Found duration '{duration}' using selector '{selector}'")
                            break
                    
                    # Post date - complete refactor with debug info
                    post_date = "Not specified"
                    print("Debug - Looking for post date")
                    # Try all possible selectors in order
                    post_date_selectors = [
                        '.ds-top-footer .field-name-post-date .field-items .field-item',
                        '.ds-top-footer .field-name-post-date',
                        '.field-name-post-date .field-item',
                        '.field-type-ds.field-name-post-date .field-items .field-item'
                    ]
                    
                    for selector in post_date_selectors:
                        post_date_elem = container.select_one(selector)
                        if post_date_elem:
                            # Get the text and remove any labels
                            text = post_date_elem.get_text(strip=True)
                            if "Post date:" in text:
                                post_date = text.replace("Post date:", "").strip()
                            else:
                                post_date = text
                            print(f"Found post date '{post_date}' using selector '{selector}'")
                            break
                    
                    # Deadline - revised to follow same pattern
                    deadline = "Not specified"
                    deadline_container = container.select_one('.ds-top-footer .field-name-field-traineeship-apply-deadline')
                    if deadline_container:
                        deadline_item = deadline_container.select_one('.field-items .field-item .date-display-single')
                        if deadline_item:
                            deadline = deadline_item.text.strip()
                        else:
                            # Try alternate selector
                            deadline_item = deadline_container.select_one('.field-items .field-item')
                            if deadline_item:
                                deadline = deadline_item.text.strip()
                    
                    # Field of study
                    field = "Not specified"
                    field_elem = container.select_one('.ds-top-content h5')
                    if field_elem:
                        field = field_elem.text.strip()
                    
                    # Add debug for each field
                    print(f"Item data - Title: {title}, Company: {company}, Duration: {duration}, Post date: {post_date}")
                    
                    traineeship = {
                        "title": title,
                        "company": company,
                        "location": location,
                        "duration": duration,
                        "post_date": post_date,
                        "deadline": deadline,
                        "field": field,
                        "url": link,
                        "page_number": page_num
                    }
                    
                    traineeships.append(traineeship)
                    
                except Exception as e:
                    print(f"Error extracting traineeship data: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            if not traineeships:
                print("Warning: No traineeships found on page")
                print("Debug HTML:")
                print(soup.select_one('.view-content'))
            else:
                print(f"Successfully extracted {len(traineeships)} traineeships from page {page_num}")
            
            return traineeships
            
        except requests.RequestException as e:
            print(f"Error fetching page {page_num}: {e}")
            return []

    def get_traineeship_details(self, traineeship: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information for a specific traineeship."""
        url = traineeship["url"]
        print(f"Getting details for: {traineeship['title']}")
        
        time.sleep(random.uniform(1, 3))
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Make a copy of existing data to preserve it
            result = traineeship.copy()
            
            # Updated field selectors - removed unwanted fields including start_date
            fields = {
                "post_date": ".field-name-field-date-posted .field-item, .date-posted",
                "duration": ".field-name-field-duration .field-item, .duration",
                "description": ".field-name-body .field-item, .description",
            }
            
            details = {}
            for field_name, selector in fields.items():
                # Skip fields that already have valid data
                if field_name in result and result[field_name] != "Not specified":
                    continue
                    
                elements = soup.select(selector)
                if elements:
                    if field_name == "website":
                        details[field_name] = elements[0].get('href', '')
                    else:
                        # Clean up the text content
                        text = elements[0].get_text(strip=True, separator=' ')
                        # Remove field labels if present
                        if ':' in text:
                            text = text.split(':', 1)[1].strip()
                        details[field_name] = text
                else:
                    details[field_name] = "Not specified"
            
            # Only update fields that are not already defined with valid data
            for key, value in details.items():
                if key not in result or result[key] == "Not specified":
                    result[key] = value
            
            return result
            
        except requests.RequestException as e:
            print(f"Error fetching details for {url}: {e}")
            return traineeship

    def scrape_all(self, max_pages: Optional[int] = None, get_details: bool = True) -> List[Dict[str, Any]]:
        """
        Scrape all traineeship listings from the website.
        
        Args:
            max_pages: Maximum number of pages to scrape (None for all)
            get_details: Whether to fetch detailed information for each listing
            
        Returns:
            A list of dictionaries with traineeship information
        """
        total_pages = self.get_total_pages()
        print(f"Found {total_pages} pages of traineeships")
        
        if max_pages is not None and max_pages > 0:
            total_pages = min(total_pages, max_pages)
            print(f"Will scrape the first {total_pages} pages")
        
        all_traineeships = []
        
        # Scrape each page
        for page in range(1, total_pages + 1):
            traineeships_on_page = self.scrape_traineeship_listings(page)
            print(f"Found {len(traineeships_on_page)} traineeships on page {page}")
            
            # Print sample to confirm initial data was scraped correctly
            if traineeships_on_page:
                print("\nSample traineeship from page (before details):")
                sample = traineeships_on_page[0]
                print(f"  Title: {sample.get('title')}")
                print(f"  Duration: {sample.get('duration')}")
                print(f"  Post date: {sample.get('post_date')}")
                print(f"  Deadline: {sample.get('deadline')}")
            
            # Get detailed information for each traineeship if requested
            if get_details and traineeships_on_page:
                detailed_traineeships = []
                for traineeship in traineeships_on_page:
                    detailed = self.get_traineeship_details(traineeship)
                    detailed_traineeships.append(detailed)
                all_traineeships.extend(detailed_traineeships)
            else:
                all_traineeships.extend(traineeships_on_page)
            
            # Be nice to the website by adding a delay between pages
            if page < total_pages:
                delay = random.uniform(2, 5)
                print(f"Waiting {delay:.2f} seconds before next page...")
                time.sleep(delay)
        
        return all_traineeships

    def save_to_csv(self, traineeships: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Save the traineeships to a CSV file.
        
        Args:
            traineeships: List of traineeship dictionaries
            filename: Output filename (default: erasmusintern_traineeships_YYYY-MM-DD.csv)
            
        Returns:
            The filename the data was saved to
        """
        if not traineeships:
            print("No traineeships to save")
            return ""
            
        if not filename:
            # Generate a unique filename with timestamp to avoid conflicts
            date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = os.path.join(self.data_dir, f"erasmusintern_traineeships_{date_str}.csv")
        
        # Make sure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
        
        # Check if file exists and is locked/open
        if os.path.exists(filename):
            try:
                # Try to open and close the file to see if it's accessible
                with open(filename, 'a') as test_file:
                    pass
            except IOError:
                # File is locked or we don't have permission, create a new filename
                base, ext = os.path.splitext(filename)
                filename = f"{base}_new{ext}"
                print(f"Original file is locked. Using new filename: {filename}")
        
        try:
            df = pd.DataFrame(traineeships)
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"Saved {len(traineeships)} traineeships to {filename}")
            return filename
        except PermissionError:
            # If we still have permission issues, try with a different name in user directory
            import tempfile
            temp_dir = tempfile.gettempdir()
            backup_filename = os.path.join(temp_dir, f"erasmusintern_backup_{date_str}.csv")
            print(f"Permission denied. Saving to alternate location: {backup_filename}")
            df = pd.DataFrame(traineeships)
            df.to_csv(backup_filename, index=False, encoding='utf-8')
            return backup_filename
        except Exception as e:
            print(f"Error saving file: {e}")
            # Last resort - save to current directory
            fallback_file = f"erasmusintern_traineeships_fallback_{date_str}.csv"
            print(f"Attempting to save to current directory: {fallback_file}")
            df = pd.DataFrame(traineeships)
            df.to_csv(fallback_file, index=False, encoding='utf-8')
            return fallback_file

    def save_to_json(self, traineeships: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Save the traineeships to a JSON file.
        
        Args:
            traineeships: List of traineeship dictionaries
            filename: Output filename (default: erasmusintern_traineeships_YYYY-MM-DD.json)
            
        Returns:
            The filename the data was saved to
        """
        if not traineeships:
            print("No traineeships to save")
            return ""
            
        if not filename:
            # Generate a unique filename with timestamp
            date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = os.path.join(self.data_dir, f"erasmusintern_traineeships_{date_str}.json")
        
        # Make sure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(traineeships, f, indent=4, ensure_ascii=False)
            print(f"Saved {len(traineeships)} traineeships to {filename}")
            return filename
        except PermissionError:
            # Try with a different name in temp directory
            import tempfile
            temp_dir = tempfile.gettempdir()
            backup_filename = os.path.join(temp_dir, f"erasmusintern_backup_{date_str}.json")
            print(f"Permission denied. Saving to alternate location: {backup_filename}")
            with open(backup_filename, 'w', encoding='utf-8') as f:
                json.dump(traineeships, f, indent=4, ensure_ascii=False)
            return backup_filename
        except Exception as e:
            print(f"Error saving file: {e}")
            return ""