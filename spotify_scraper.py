import requests
import json
from datetime import datetime
from bs4 import BeautifulSoup
import re
import os

# --- Configuration ---
ARTIST_ID = "4RYaFaZPwHFQpNUr6mW6OW"
ARTIST_URL = f"https://open.spotify.com/artist/{ARTIST_ID}"
JSON_FILE = "listeners_history.json"

# --- Utility Functions ---

def clean_listener_count(text):
    """
    Parses a string like '3,456,789 monthly listeners' into an integer.
    Handles 'K' and 'M' abbreviations if they appear.
    """
    if not text:
        return 0
    
    # Example description: 'Artist Name · 3,456,789 monthly listeners'
    try:
        # Find the number part of the string
        match = re.search(r'([\d,]+\.?\d*[MK]?) monthly listeners', text)
        if match:
            number_str = match.group(1).replace(',', '').strip()
            
            # Convert abbreviated numbers (e.g., 3.4M or 500K)
            if 'M' in number_str:
                return int(float(number_str.replace('M', '')) * 1_000_000)
            elif 'K' in number_str:
                return int(float(number_str.replace('K', '')) * 1_000)
            else:
                return int(number_str)
        
        print("Warning: Could not find monthly listener count pattern in metadata.")
        return 0

    except Exception as e:
        print(f"Error cleaning listener count: {e}")
        return 0

def fetch_monthly_listeners(url):
    """Fetches the monthly listener count from the Spotify artist page."""
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() 
        
        soup = BeautifulSoup(response.text, 'html.parser')
        meta_tag = soup.find("meta", property="og:description")
        
        if meta_tag:
            description = meta_tag.get('content', '')
            print(f"Found og:description: {description}")
            
            listeners = clean_listener_count(description)
            return listeners
        else:
            print("Error: og:description meta tag not found.")
            return 0
            
    except requests.exceptions.RequestException as e:
        print(f"HTTP Request Error: {e}")
        return 0
    except Exception as e:
        print(f"An unexpected error occurred during scraping: {e}")
        return 0

def update_json_data(listeners):
    """Loads existing JSON, appends new data, and saves it."""
    
    timestamp = datetime.now().isoformat()
    new_data = {
        "date": timestamp,
        "listeners": listeners
    }
    
    data = []
    if os.path.exists(JSON_FILE) and os.path.getsize(JSON_FILE) > 0:
        try:
            with open(JSON_FILE, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: {JSON_FILE} is corrupted or empty. Starting new history.")

    if listeners > 0:
        # Check if the last entry is the same
        if data and data[-1]['listeners'] == listeners:
            print("Listener count hasn't changed since last run. Skipping update.")
            return

        data.append(new_data)
        print(f"Successfully scraped {listeners} listeners. Appending to history.")

        with open(JSON_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Successfully updated {JSON_FILE}.")
    else:
        print("Scrape failed (listeners=0). Skipping JSON update.")

# The unit test block can be removed if you don't need it after initial testing
def run_unit_tests():
    print("\n--- Running Unit Tests for clean_listener_count ---")
    tests = [
        ("Some Artist · 1,234,567 monthly listeners", 1234567, "Full comma-separated number"),
        ("Another Artist · 5.5M monthly listeners", 5500000, "Million abbreviated (5.5M)"),
    ]
    success = True
    for input_str, expected, description in tests:
        result = clean_listener_count(input_str)
        if result != expected:
            success = False
    return success

if __name__ == "__main__":
    if run_unit_tests():
        print("Parsing tests passed. Proceeding with live scrape.")
        listener_count = fetch_monthly_listeners(ARTIST_URL)
        update_json_data(listener_count)
    else:
        print("Parsing tests failed. Stopping execution.")
