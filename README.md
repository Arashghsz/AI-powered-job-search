# AI-powered-job-search
This project allows scraping job applications from erasmusintern.org (or any job searching platform).

# Job Search Tool for Erasmus Internships

A tool to search and filter internship opportunities from the Erasmus Intern website.

## Features

- **Scraper**: Collect job listings from Erasmus Intern website
- **Search Functionality**: Filter and find relevant job listings

## Installation

1. Clone this repository
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your configuration:
   ```
   BASE_URL=https://erasmusintern.org/traineeships
   MAX_PAGES=0  # Set to 0 for all pages
   DATA_DIR=data
   ```

## Usage

### Scrape Job Listings

```bash
python main.py scrape [--max-pages MAX_PAGES] [--no-details] [--output OUTPUT]
```

Options:
- `--max-pages`: Maximum number of pages to scrape (default: 0, means all pages)
- `--no-details`: Skip fetching detailed information for each job
- `--output`: Custom output filename


## Examples

### Example Commands

```bash
# Scrape jobs
python main.py scrape --max-pages 3


## How It Works

1. The tool scrapes job listings from Erasmus Intern website and saves them to CSV/JSON
2. The search functionality allows you to filter and find relevant job listings
