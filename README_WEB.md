# LinkedIn Job Scraper Web Interface

A web interface for the LinkedIn Job Scraper that allows users to run the scraper and view the results through a browser.

## Features

- Clean, responsive web interface built with Express and EJS
- View the latest scraped job listings in a table format
- Run the scraper with custom parameters through a web form
- Mobile-friendly design using Bootstrap

## Prerequisites

- Node.js (v14 or later recommended)
- NPM (v6 or later recommended)
- Python 3.6+ (for the underlying job scraper script)
- Chrome browser (for the underlying scraper)

## Installation

1. Make sure you have already set up the LinkedIn Job Scraper (see the main README.md)
2. Install the required Node.js dependencies:

```bash
npm install
```

## Usage

1. Start the web server:

```bash
npm start
```

2. Open your browser and navigate to:

```
http://localhost:3000
```

3. Use the web interface to:
   - View previously scraped job listings
   - Run the scraper with new parameters
   - Access job listing details directly

## Development

For development with auto-reload:

```bash
npm run dev
```

## How It Works

The web interface connects to the existing Python-based LinkedIn Job Scraper:

1. The Express server loads and displays job listings from the output directory
2. When you run the scraper through the web form, it executes the Python script with your parameters
3. After the scraper completes, the page reloads to show the latest results

## Notes

- Running the scraper through the web interface may take several minutes
- The browser will wait for the scraper to complete before showing results
- For best results, don't refresh the page while the scraper is running

## License

This tool is provided for educational purposes only. Using web scrapers might violate the Terms of Service of the websites being scraped. Use at your own risk. 