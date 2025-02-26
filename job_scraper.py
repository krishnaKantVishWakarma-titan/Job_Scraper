import requests
from bs4 import BeautifulSoup
import json
import os
import time
from datetime import datetime
import random
import argparse
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException

class JobScraper:
    def __init__(self):
        self.results = []
        self.output_dir = "output"
        
        # Default filename (will be updated with search params later)
        current_date = datetime.now()
        date_str = current_date.strftime('%b%d_%Y')
        self.output_file = os.path.join(self.output_dir, f"all_jobs_{date_str}.json")
        
        # Ensure output directory exists
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"Created output directory: {self.output_dir}")
            
        # Initialize Selenium for LinkedIn (which needs JavaScript)
        self.setup_selenium()
    
    def setup_selenium(self):
        """Set up headless Chrome browser for scraping."""
        chrome_options = Options()
        
        # Headless mode
        chrome_options.add_argument("--headless")
        
        # Disable GPU and graphics related issues
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Disable WebRTC to avoid STUN errors
        chrome_options.add_argument("--disable-webrtc")
        
        # Disable unused features that cause errors
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--mute-audio")
        
        # Disable camera/video to prevent video_capture errors
        chrome_options.add_argument("--use-fake-ui-for-media-stream")
        chrome_options.add_argument("--use-fake-device-for-media-stream")
        
        # Performance and stability settings
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-setuid-sandbox")
        chrome_options.add_argument("--disable-accelerated-2d-canvas")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        
        # Add a rotating set of user agents to avoid detection
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")
        
        # Set preferences to disable features
        chrome_prefs = {
            "profile.default_content_setting_values.notifications": 2,  # Block notifications
            "profile.default_content_setting_values.media_stream_camera": 2,  # Block camera
            "profile.default_content_setting_values.media_stream_mic": 2,  # Block microphone
            "profile.default_content_setting_values.geolocation": 2,  # Block location
            "profile.managed_default_content_settings.images": 1,  # Load images (needed for many job sites)
            "profile.default_content_setting_values.cookies": 1,  # Accept cookies (needed for many job sites)
        }
        chrome_options.add_experimental_option("prefs", chrome_prefs)
        
        # Additional options to evade detection
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # Use webdriver-manager to handle chromedriver installation
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            print("Chrome WebDriver initialized successfully")
            
            # Execute CDP commands to evade detection
            try:
                self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    """
                })
                print("Added anti-detection scripts")
            except Exception as e:
                print(f"Could not add anti-detection scripts: {e}")
                
        except Exception as e:
            print(f"Error setting up ChromeDriver with webdriver-manager: {e}")
            print("Falling back to directly using Chrome WebDriver...")
            self.driver = webdriver.Chrome(options=chrome_options)
    
    def scrape_linkedin(self, job_title, location, experience=None):
        """Scrape LinkedIn for job listings."""
        print(f"Scraping LinkedIn for {job_title} in {location}...")
        
        # Format the search URL
        query = job_title.replace(' ', '%20')
        location_query = location.replace(' ', '%20')
        url = f"https://www.linkedin.com/jobs/search/?keywords={query}&location={location_query}"
        
        # Add experience filter if provided
        if experience:
            url += f"&f_E={experience}"
        
        try:
            print(f"Navigating to URL: {url}")
            self.driver.get(url)
            time.sleep(5)  # Increase wait time to allow page to fully load
            
            # Wait for job results to load
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-search__results-list, .job-search-resultsList"))
                )
            except TimeoutException:
                print("Could not find job results list on LinkedIn. The site may have changed or blocked access.")
                # Save screenshot for debugging
                try:
                    screenshot_path = os.path.join(self.output_dir, "linkedin_debug.png")
                    self.driver.save_screenshot(screenshot_path)
                    print(f"Debug screenshot saved to {screenshot_path}")
                except Exception as e:
                    print(f"Failed to save debug screenshot: {e}")
                return
            
            # Try to scroll down to load more results (pagination)
            try:
                total_jobs_found = 0
                pages_to_scrape = 5  # Increased to 5 pages to get more results
                max_jobs = 100  # Maximum jobs to scrape to avoid overloading
                
                for page in range(pages_to_scrape):
                    # Check if we've hit the maximum job limit
                    if total_jobs_found >= max_jobs:
                        print(f"Reached maximum job limit of {max_jobs}. Stopping LinkedIn scraping.")
                        break
                        
                    # Try multiple selectors for job cards
                    job_cards = []
                    selectors = [
                        ".jobs-search__results-list li", 
                        ".job-search-card",
                        "li.jobs-search-results__list-item",
                        ".jobs-search-results__list-item",
                        ".job-card-container"
                    ]
                    
                    for selector in selectors:
                        job_cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if job_cards:
                            print(f"Found job cards using selector: {selector}")
                            break
                    
                    if not job_cards:
                        if page == 0:  # First page should have results
                            print("No job cards found on LinkedIn. All selectors failed.")
                            return
                        else:  # Expected to eventually run out of results
                            print(f"No more job cards found on page {page+1}. Stopping pagination.")
                            break
                            
                    print(f"Found {len(job_cards)} job cards on LinkedIn page {page+1}")
                    new_jobs = 0
                    
                    # Process job cards from current page - limit according to max_jobs
                    job_cards_to_process = job_cards[total_jobs_found:] if page > 0 else job_cards
                    remaining_jobs = max_jobs - total_jobs_found
                    if len(job_cards_to_process) > remaining_jobs:
                        job_cards_to_process = job_cards_to_process[:remaining_jobs]
                        print(f"Limiting to {remaining_jobs} more jobs to stay under maximum of {max_jobs}")
                        
                    print(f"Processing {len(job_cards_to_process)} new job listings from LinkedIn page {page+1}")
                    
                    for card_index, card in enumerate(job_cards_to_process):
                        try:
                            # Extract job title, handling obfuscated content
                            title = "Not available"
                            try:
                                title_elements = []
                                try:
                                    title_elements.append(card.find_element(By.CSS_SELECTOR, "h3.base-search-card__title"))
                                except: pass
                                try:
                                    title_elements.append(card.find_element(By.CSS_SELECTOR, ".job-search-card__title"))
                                except: pass
                                try: 
                                    title_elements.append(card.find_element(By.CSS_SELECTOR, "h3"))
                                except: pass
                                try:
                                    title_elements.append(card.find_element(By.CSS_SELECTOR, ".job-card-list__title"))
                                except: pass
                                
                                for element in title_elements:
                                    raw_title = element.text.strip()
                                    if raw_title and not all(c == '*' for c in raw_title):
                                        title = raw_title
                                        break
                            except Exception as e:
                                print(f"Error extracting title: {e}")
                            
                            # Extract company name
                            company = "Not available"
                            try:
                                company_elements = []
                                try:
                                    company_elements.append(card.find_element(By.CSS_SELECTOR, "h4.base-search-card__subtitle"))
                                except: pass
                                try:
                                    company_elements.append(card.find_element(By.CSS_SELECTOR, ".job-search-card__subtitle"))
                                except: pass
                                try:
                                    company_elements.append(card.find_element(By.CSS_SELECTOR, "h4"))
                                except: pass
                                try:
                                    company_elements.append(card.find_element(By.CSS_SELECTOR, ".job-card-container__company-name"))
                                except: pass
                                
                                for element in company_elements:
                                    raw_company = element.text.strip()
                                    if raw_company and not all(c == '*' for c in raw_company):
                                        company = raw_company
                                        break
                            except Exception as e:
                                print(f"Error extracting company: {e}")
                            
                            # Extract location
                            location = "Not available"
                            try:
                                location_elements = []
                                try:
                                    location_elements.append(card.find_element(By.CSS_SELECTOR, ".job-search-card__location"))
                                except: pass
                                try:
                                    location_elements.append(card.find_element(By.CSS_SELECTOR, ".job-result-card__location"))
                                except: pass
                                try:
                                    location_elements.append(card.find_element(By.CSS_SELECTOR, ".base-search-card__metadata"))
                                except: pass
                                try:
                                    location_elements.append(card.find_element(By.CSS_SELECTOR, ".job-card-container__metadata-item"))
                                except: pass
                                
                                for element in location_elements:
                                    raw_location = element.text.strip()
                                    if raw_location and not all(c == '*' for c in raw_location):
                                        location = raw_location
                                        break
                            except Exception as e:
                                print(f"Error extracting location: {e}")
                            
                            # Get job link - try multiple strategies
                            job_link = "Not available"
                            try:
                                link_selectors = [
                                    "a.base-card__full-link",
                                    "a.job-search-card__link",
                                    "a.job-card-list__title",
                                    "a.job-card-container__link"
                                ]
                                
                                for link_selector in link_selectors:
                                    try:
                                        link_element = card.find_element(By.CSS_SELECTOR, link_selector)
                                        job_link = link_element.get_attribute("href")
                                        if job_link:
                                            break
                                    except:
                                        continue
                                    
                                # If still no link, try getting any anchor tag
                                if job_link == "Not available":
                                    anchors = card.find_elements(By.TAG_NAME, "a")
                                    for anchor in anchors:
                                        href = anchor.get_attribute("href")
                                        if href and "linkedin.com/jobs/view" in href:
                                            job_link = href
                                            break
                            except Exception as e:
                                print(f"Error extracting job link: {e}")
                            
                            # Get date - try multiple strategies
                            date_posted = "Not specified"
                            try:
                                try:
                                    date_element = card.find_element(By.CSS_SELECTOR, "time")
                                    date_posted = date_element.get_attribute("datetime")
                                except:
                                    try:
                                        date_element = card.find_element(By.CSS_SELECTOR, ".job-search-card__listdate")
                                        date_posted = date_element.text.strip()
                                    except:
                                        try:
                                            date_element = card.find_element(By.CSS_SELECTOR, ".job-card-container__footer-item")
                                            date_posted = date_element.text.strip()
                                        except:
                                            pass
                            except Exception as e:
                                print(f"Error extracting date: {e}")
                            
                            # Skip invalid listings (e.g., mostly asterisks or empty fields)
                            if (title == "Not available" or title.count('*') > len(title) / 2) and \
                               (company == "Not available" or company.count('*') > len(company) / 2):
                                print(f"Skipping job with obfuscated or missing title/company")
                                continue
                            
                            job_data = {
                                "source": "LinkedIn",
                                "title": title,
                                "company": company,
                                "location": location,
                                "link": job_link,
                                "date_posted": date_posted,
                            }
                            
                            # Print job data for debugging
                            print(f"Found LinkedIn job: {title} at {company} in {location}")
                            
                            self.results.append(job_data)
                            new_jobs += 1
                        except Exception as e:
                            print(f"Error parsing LinkedIn job card {card_index+1}: {e}")
                    
                    # Update count of total jobs found
                    total_jobs_found += new_jobs
                    
                    # If we've hit the maximum job limit, stop pagination
                    if total_jobs_found >= max_jobs:
                        print(f"Reached maximum job limit of {max_jobs}. Stopping LinkedIn pagination.")
                        break
                    
                    # If there are more pages, try to click "Next" button or scroll down
                    if page < pages_to_scrape - 1:
                        try:
                            # Try to find and click the "Next" button
                            next_button = None
                            next_selectors = [
                                "button.infinite-scroller__show-more-button",
                                "button.see-more-jobs",
                                "button[aria-label='See more jobs']",
                                ".artdeco-pagination__button--next",
                                "li.artdeco-pagination__indicator--number button"
                            ]
                            
                            for next_selector in next_selectors:
                                try:
                                    next_buttons = self.driver.find_elements(By.CSS_SELECTOR, next_selector)
                                    if next_buttons:
                                        for btn in next_buttons:
                                            if btn.is_displayed() and btn.is_enabled():
                                                # For numbered pagination, find the next page number
                                                if "artdeco-pagination__indicator--number" in next_selector:
                                                    current_page = page + 1
                                                    button_text = btn.text.strip()
                                                    if button_text.isdigit() and int(button_text) == current_page + 1:
                                                        next_button = btn
                                                        break
                                                else:
                                                    next_button = btn
                                                    break
                                        if next_button:
                                            break
                                except:
                                    continue
                            
                            if next_button:
                                print(f"Found 'Next' button for page {page+2}, clicking to load more jobs")
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                                time.sleep(1)
                                next_button.click()
                                time.sleep(4)  # Increased wait time for new results to load
                            else:
                                # If no next button, try scrolling down
                                print("No 'Next' button found, scrolling down to load more jobs")
                                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                                time.sleep(3)  # Wait for scrolling to trigger more results
                        except Exception as e:
                            print(f"Error trying to load more LinkedIn jobs: {e}")
                            # Break the pagination loop if we can't load more
                            break
                
                # Summarize results
                if self.results:
                    linkedin_jobs = [job for job in self.results if job["source"] == "LinkedIn"]
                    job_count = len(linkedin_jobs)
                    titles = ", ".join([job["title"] for job in linkedin_jobs[:3]]) + ("..." if job_count > 3 else "")
                    print(f"Successfully scraped {job_count} jobs from LinkedIn. Examples: {titles}")
                else:
                    print("No jobs were successfully parsed from LinkedIn")
            
            except Exception as e:
                print(f"Error during LinkedIn pagination: {e}")
                
        except TimeoutException:
            print("Timeout while loading LinkedIn jobs")
        except WebDriverException as e:
            print(f"WebDriver error: {e}")
        except Exception as e:
            print(f"Error scraping LinkedIn: {str(e)}")
    
    def save_results(self):
        """Save scraped job listings to a JSON file."""
        try:
            # Each run creates a new file with timestamp, no need to read existing one
            print(f"Saving results to new file: {self.output_file}")

            # Filter out jobs with "Not available" as title or company
            filtered_data = []
            for job in self.results:
                # Skip jobs with missing/unavailable titles or companies
                if job.get("title") in ["Not available", "Not specified"] or job.get("company") in ["Not available", "Not specified"]:
                    print(f"Skipping job with title '{job.get('title')}' at company '{job.get('company')}' - incomplete data")
                    continue
                filtered_data.append(job)
            
            print(f"Filtered out {len(self.results) - len(filtered_data)} jobs with missing title or company data")
            
            # Remove duplicates based on job link within the filtered results
            unique_data = []
            seen_links = set()
            for job in filtered_data:
                if job["link"] not in seen_links:
                    # Clean up any excessive whitespace in text fields
                    for field in ["title", "company", "location"]:
                        if field in job and isinstance(job[field], str):
                            job[field] = " ".join(job[field].split())
                    
                    unique_data.append(job)
                    seen_links.add(job["link"])
            
            if len(unique_data) < len(filtered_data):
                print(f"Removed {len(filtered_data) - len(unique_data)} duplicate records")
            
            # Sort the json output by source and date
            unique_data.sort(key=lambda x: (x.get("source", ""), x.get("date_posted", "")), reverse=True)
            
            # Save to the timestamped file with nice formatting
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(unique_data, f, indent=4, ensure_ascii=False, sort_keys=False)
            
            print(f"Results saved to {self.output_file} ({len(unique_data)} jobs total)")
            return self.output_file
        except Exception as e:
            print(f"Error saving results: {e}")
            return None
    
    def scrape_jobs(self, job_title, locations, experience=None):
        """Main function to scrape jobs from LinkedIn."""
        if not isinstance(locations, list):
            locations = [locations]
        
        # Clear previous results before starting a new search
        self.results = []
        
        # Create a more human-readable filename with search parameters
        current_date = datetime.now()
        date_str = current_date.strftime('%b%d_%Y')  # e.g., Feb27_2025
        time_str = current_date.strftime('%H%M')  # e.g., 1435
        
        # Format the job title and location for the filename
        job_slug = job_title.lower().replace(' ', '_')[:20]  # Limit length
        if isinstance(locations, list) and len(locations) == 1:
            location_slug = locations[0].lower().replace(' ', '_')[:15]  # Limit length
        else:
            location_slug = 'multiple_locations'
            
        # Create the filename with search parameters
        self.output_file = os.path.join(
            self.output_dir, 
            f"{job_slug}_{location_slug}_{date_str}_{time_str}.json"
        )
        print(f"Results will be saved to: {self.output_file}")
        
        for location in locations:
            # Attempt LinkedIn with retry mechanism
            max_retries = 3
            retry_count = 0
            success = False
            
            while retry_count < max_retries and not success:
                try:
                    # Start with LinkedIn
                    if retry_count > 0:
                        print(f"Retry attempt {retry_count}/{max_retries} for LinkedIn scraping...")
                    
                    self.scrape_linkedin(job_title, location, experience)
                    
                    # Consider it a success if we got at least one result
                    linkedin_count = len(self.results)
                    if linkedin_count > 0:
                        success = True
                        print(f"Successfully scraped {linkedin_count} jobs from LinkedIn")
                    else:
                        retry_count += 1
                        print(f"No LinkedIn results found. Retrying in 5 seconds...")
                        time.sleep(5)
                except Exception as e:
                    retry_count += 1
                    print(f"Error scraping LinkedIn: {e}")
                    print(f"Retrying in 5 seconds... ({retry_count}/{max_retries})")
                    time.sleep(5)
            
            # If all retries failed, log a message
            if not success:
                print(f"Failed to scrape LinkedIn jobs for {job_title} in {location} after {max_retries} attempts")
        
        # Sort by date, with most recent first
        # This is a simplistic approach since date formats vary
        self.results.sort(key=lambda x: x.get('date_posted', "") if x.get('date_posted', "") != "Not specified" else "", reverse=True)
        
        # Show distribution of jobs by source
        source_counts = {}
        for job in self.results:
            source = job.get("source", "Unknown")
            source_counts[source] = source_counts.get(source, 0) + 1
        
        for source, count in source_counts.items():
            print(f"Found {count} jobs from {source}")
            
        print(f"Keeping all {len(self.results)} jobs found")
        
        # Save results to file
        filename = self.save_results()
        
        return filename
    
    def close(self):
        """Close the Selenium driver."""
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
                print("Selenium WebDriver closed successfully")
            except Exception as e:
                print(f"Error closing WebDriver: {e}")


def load_config():
    """Load search parameters from config.json file."""
    config_file = "config.json"
    
    # Use default values if config file doesn't exist
    default_config = {
        "job_titles": ["Software Engineer"],
        "locations": ["New York"],
        "experience_levels": ["0-1"]
    }
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                print(f"Loaded configuration from {config_file}")
                return config
        else:
            print(f"Config file {config_file} not found. Using default values.")
            return default_config
    except Exception as e:
        print(f"Error loading config file: {e}. Using default values.")
        return default_config


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Job Portal Scraper")
    
    parser.add_argument("--title", "-t", help="Specific job title to search for")
    parser.add_argument("--location", "-l", help="Specific location to search in")
    parser.add_argument("--experience", "-e", help="Specific experience level to filter by (e.g., '0-1', '3-5')")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug mode with verbose output")
    
    return parser.parse_args()


def main():
    # Parse command line arguments
    args = parse_args()
    
    # Enable debug mode with verbose output if requested
    if args.debug:
        print("Debug mode enabled")
    
    # Load search parameters from config file
    config = load_config()
    
    # Override with command line arguments if provided
    job_titles = [args.title] if args.title else config["job_titles"]
    locations = [args.location] if args.location else config["locations"]
    experience_levels = [args.experience] if args.experience else config["experience_levels"]
    
    # Display search parameters
    print("\nSearch Parameters:")
    print(f"Job Titles: {', '.join(job_titles)}")
    print(f"Locations: {', '.join(locations)}")
    print(f"Experience Levels: {', '.join(experience_levels)}")
    
    # Create a single instance of JobScraper to reuse
    scraper = JobScraper()
    print("Job scraper initialized.")
    print(f"Output will be saved to: {scraper.output_file}")
    
    try:
        # Each run now creates a new timestamped output file
        output_file = scraper.output_file
        
        # Instead of nested loops, create a simpler list of job searches
        searches = []
        for job_title in job_titles:
            for location in locations:
                for experience in experience_levels:
                    searches.append((job_title, location, experience))
        
        print(f"\nWill perform {len(searches)} different job searches...")
        
        # Perform each search one by one
        for i, (job_title, location, experience) in enumerate(searches, 1):
            print(f"\n[{i}/{len(searches)}] Searching for: {job_title} in {location} with {experience} years experience...")
            
            # Run the scraper for this combination with retries
            scraper.scrape_jobs(job_title, location, experience)
            
            # Add a small delay between searches
            if i < len(searches):  # Don't delay after the last search
                delay = random.uniform(3, 5)
                print(f"Waiting {delay:.1f} seconds before next search...")
                time.sleep(delay)
        
        print(f"\nAll job searches completed! Results saved to: {output_file}")
    
    except KeyboardInterrupt:
        print("\nSearch interrupted by user. Saving current results...")
        scraper.save_results()
        print("Partial results saved.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        # Always close the browser
        print("Closing browser...")
        scraper.close()
        print("Done!")


if __name__ == "__main__":
    main()
