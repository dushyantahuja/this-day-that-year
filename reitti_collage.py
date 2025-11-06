#!/usr/bin/env python3
"""
Reitti "This Day That Year" Screenshot Collage Generator
Creates a collage of screenshots from the same day/month across multiple years.
"""

import os
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from PIL import Image
import time

# Configuration
REITTI_BASE_URL = os.getenv("REITTI_URL", "http://192.168.79.2:8030/")
REITTI_USERNAME = os.getenv("REITTI_USERNAME", "")
REITTI_PASSWORD = os.getenv("REITTI_PASSWORD", "")
START_YEAR = int(os.getenv("START_YEAR", "2012"))
SCREENSHOT_DIR = "/output/screenshots"
OUTPUT_DIR = "/output/collages"
WAIT_TIME = int(os.getenv("WAIT_TIME", "5"))
LOGIN_WAIT_TIME = int(os.getenv("LOGIN_WAIT_TIME", "3"))
SCREENSHOT_WIDTH = int(os.getenv("SCREENSHOT_WIDTH", "1920"))
SCREENSHOT_HEIGHT = int(os.getenv("SCREENSHOT_HEIGHT", "1080"))
COLUMNS = int(os.getenv("COLLAGE_COLUMNS", "3"))

def setup_driver():
    """Setup headless Chrome driver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(f"--window-size={SCREENSHOT_WIDTH},{SCREENSHOT_HEIGHT}")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def login_to_reitti(driver):
    """Log in to Reitti"""
    if not REITTI_USERNAME or not REITTI_PASSWORD:
        print("ERROR: REITTI_USERNAME and REITTI_PASSWORD environment variables must be set!")
        sys.exit(1)
    
    print(f"Logging in to Reitti as {REITTI_USERNAME}...")
    
    try:
        # Go to base URL (should show login form)
        driver.get(REITTI_BASE_URL)
        time.sleep(LOGIN_WAIT_TIME)
        
        # Find and fill username field by ID
        username_field = driver.find_element("id", "username")
        username_field.clear()
        username_field.send_keys(REITTI_USERNAME)
        
        # Find and fill password field by ID
        password_field = driver.find_element("id", "password")
        password_field.clear()
        password_field.send_keys(REITTI_PASSWORD)
        
        # Find and click the login button
        login_button = driver.find_element("css selector", "button[type='submit']")
        login_button.click()
        
        # Wait for redirect after login
        time.sleep(LOGIN_WAIT_TIME)
        
        # Check if we're still on the login page (login failed)
        if "/login" in driver.current_url or "login-container" in driver.page_source:
            print("  ✗ Login failed - still on login page")
            print("  Please check your username and password")
            return False
        
        print("  ✓ Logged in successfully")
        return True
        
    except Exception as e:
        print(f"  ✗ Login failed: {e}")
        print("\nPlease check:")
        print("  1. REITTI_USERNAME and REITTI_PASSWORD are correct")
        print("  2. Reitti instance is accessible at", REITTI_BASE_URL)
        print("  3. Increase LOGIN_WAIT_TIME if page loads slowly")
        return False

def take_screenshot(driver, date_str, output_path):
    """Take screenshot of Reitti for a specific date"""
    url = f"{REITTI_BASE_URL}?date={date_str}"
    print(f"Capturing: {url}")
    
    try:
        driver.get(url)
        time.sleep(WAIT_TIME)  # Wait for page to fully load
        driver.save_screenshot(output_path)
        print(f"  ✓ Saved to {output_path}")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def create_collage(image_paths, output_path, columns=3):
    """Create a collage from multiple screenshots"""
    images = []
    valid_paths = []
    
    # Load all valid images
    for path in image_paths:
        if os.path.exists(path):
            try:
                img = Image.open(path)
                images.append(img)
                valid_paths.append(path)
            except Exception as e:
                print(f"Error loading {path}: {e}")
    
    if not images:
        print("No valid images to create collage")
        return False
    
    # Calculate dimensions
    img_width, img_height = images[0].size
    rows = (len(images) + columns - 1) // columns
    
    # Create blank canvas
    collage_width = columns * img_width
    collage_height = rows * img_height
    collage = Image.new('RGB', (collage_width, collage_height), 'white')
    
    # Paste images
    for idx, img in enumerate(images):
        row = idx // columns
        col = idx % columns
        x = col * img_width
        y = row * img_height
        
        # Resize image to fit if needed
        if img.size != (img_width, img_height):
            img = img.resize((img_width, img_height), Image.Resampling.LANCZOS)
        
        collage.paste(img, (x, y))
    
    # Save collage
    collage.save(output_path, quality=95)
    print(f"\n✓ Collage saved to: {output_path}")
    return True

def main():
    # Get today's date
    today = datetime.now()
    current_year = today.year
    month = today.month
    day = today.day
    
    # Create output directories
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print(f"=== Reitti 'This Day That Year' Collage Generator ===")
    print(f"Date: {month:02d}-{day:02d}")
    print(f"Years: {START_YEAR} to {current_year}")
    print(f"Base URL: {REITTI_BASE_URL}\n")
    
    # Setup browser
    print("Initializing headless browser...")
    driver = setup_driver()
    
    # Login to Reitti
    if not login_to_reitti(driver):
        driver.quit()
        sys.exit(1)
    
    screenshot_paths = []
    
    try:
        # Take screenshots for each year
        for year in range(START_YEAR, current_year + 1):
            date_str = f"{year}-{month:02d}-{day:02d}"
            screenshot_path = os.path.join(
                SCREENSHOT_DIR, 
                f"reitti_{date_str}.png"
            )
            
            if take_screenshot(driver, date_str, screenshot_path):
                screenshot_paths.append(screenshot_path)
        
        print(f"\n✓ Captured {len(screenshot_paths)} screenshots")
        
        # Create collage
        if screenshot_paths:
            collage_filename = f"reitti_collage_{month:02d}-{day:02d}_{START_YEAR}-{current_year}.png"
            collage_path = os.path.join(OUTPUT_DIR, collage_filename)
            
            print(f"\nCreating collage...")
            create_collage(screenshot_paths, collage_path, columns=COLUMNS)
        
    finally:
        driver.quit()
        print("\n✓ Done!")

if __name__ == "__main__":
    main()