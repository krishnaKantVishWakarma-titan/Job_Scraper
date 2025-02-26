# Job Portal Scraper

A Python tool that scrapes job listings from LinkedIn based on specified criteria.

## Features

- Focuses exclusively on LinkedIn job scraping
- Implements pagination on LinkedIn to retrieve up to 100 job listings
- Configurable search parameters:
  - Job title
  - Job locations (multiple can be specified)
  - Work experience level
- Filters out obfuscated or low-quality job listings
- Each search creates a new timestamped JSON file in the `output` folder (named all_jobs_YYYYMMDD_HHMMSS.json)
- Prevents duplicate listings within each search
- Sorts listings by date with most recent first

## Requirements

- Python 3.6+
- Chrome browser installed (for Selenium WebDriver)
- Required Python packages:
  - requests
  - beautifulsoup4
  - selenium
  - webdriver-manager (for automatic chromedriver management)

## Installation

1. Clone this repository or download the source code
2. Install the required packages:

```bash
pip install -r requirements.txt
```

3. Make sure you have Chrome installed on your system

## Usage

### Configuration File

The script uses a `config.json` file to define the search parameters. This allows you to customize your searches without modifying the code:

```bash
python job_scraper.py
```

To customize the search parameters, edit the `config.json` file:

```json
{
    "job_titles": [
        "Software Engineer",
        "Data Scientist", 
        "Product Manager"
    ],
    "locations": [
        "New York",
        "San Francisco",
        "Remote"
    ],
    "experience_levels": [
        "0-1",
        "3-5",
        "5-10"
    ]
}
```

If the `config.json` file doesn't exist or can't be loaded, the script will use default values.

The script will loop through all combinations of these parameters and save the results to a new JSON file in the `output` folder. Each run creates a new file with a timestamp in the filename to avoid overwriting previous results. For example, with the configuration shown above, it will perform 27 separate searches (3 job titles × 3 locations × 3 experience levels) and combine the results.

### Command-Line Arguments

You can also specify search parameters directly via command-line arguments. These will override the values in the config file:

```bash
# Search for a specific job title only
python job_scraper.py --title "Frontend Developer"

# Search for a specific job in a specific location
python job_scraper.py --title "Python Developer" --location "Chicago"

# Full specification
python job_scraper.py --title "Data Engineer" --location "Boston" --experience "3-5"
```

Available command-line arguments:
- `--title` or `-t`: Job title to search for
- `--location` or `-l`: Location to search in
- `--experience` or `-e`: Experience level to filter by
- `--debug` or `-d`: Enable debug mode with verbose output

## Output Format

The script saves all job listings in a timestamped JSON file (`all_jobs_YYYYMMDD_HHMMSS.json`) with the following structure:

```json
[
  {
    "source": "LinkedIn",
    "title": "Software Engineer",
    "company": "Example Corp",
    "location": "New York, NY",
    "link": "https://www.linkedin.com/jobs/view/123456789",
    "date_posted": "2023-06-15"
  },
  {
    "source": "LinkedIn",
    "title": "Data Scientist",
    "company": "Another Company",
    "location": "San Francisco, CA",
    "link": "https://www.linkedin.com/jobs/view/987654321",
    "date_posted": "2023-06-14"
  }
]
```

The script automatically handles:
- Generating a unique filename for each run using timestamps
- Removing duplicate job listings within the current search results
- Filtering out obfuscated or low-quality job listings (e.g., ones with asterisks instead of text)
- Sorting by date (most recent first)

## Notes

- LinkedIn frequently updates their website structure, which may break the scraper
- The script includes user-agent randomization, anti-detection measures, and delays to avoid being blocked
- Using this scraper may violate the Terms of Service of LinkedIn
- This tool is intended for educational purposes only

## Legal Disclaimer

This tool is provided for educational purposes only. Using web scrapers might violate the Terms of Service of the websites being scraped. Use at your own risk.

## Extending the Scraper

To add support for additional job portals, create a new method in the `JobScraper` class following the pattern of the existing methods, and call it from the `scrape_jobs` method. 