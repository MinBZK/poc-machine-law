#!/usr/bin/env python3
"""Take screenshots of all pages to analyze the UI"""

import os
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Create screenshots directory
SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Setup Chrome in headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--force-device-scale-factor=2")  # For retina quality


def take_screenshot(driver, url, filename, wait_selector=None):
    """Take a screenshot of a page"""
    print(f"📸 Taking screenshot of {url}")
    driver.get(url)

    # Wait for page to load
    if wait_selector:
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector)))
        except:
            print(f"⚠️  Warning: Could not find selector {wait_selector}")
    else:
        time.sleep(2)  # Basic wait

    # Take screenshot
    filepath = os.path.join(SCREENSHOT_DIR, filename)
    driver.save_screenshot(filepath)
    print(f"✅ Saved: {filepath}")

    # Also get page title and some info
    title = driver.title
    print(f"   Title: {title}")

    # Check for any 404 errors in console
    logs = driver.get_log("browser")
    errors = [log for log in logs if "404" in log.get("message", "")]
    if errors:
        print(f"   ⚠️  Found {len(errors)} 404 errors")
        for error in errors[:3]:
            print(f"      - {error['message'][:100]}...")

    return filepath


def main():
    print(f"🚀 Starting screenshot capture at {datetime.now().strftime('%H:%M:%S')}")

    # Create driver
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # 1. Homepage (burger.nl)
        take_screenshot(driver, "http://localhost:8000/", "01_homepage_burger.png", ".card")

        # 2. Wetten index
        take_screenshot(driver, "http://localhost:8000/wetten/", "02_wetten_index.png", ".law-item")

        # 3. Law detail (Zorgtoeslag - light/bovenwater)
        take_screenshot(
            driver, "http://localhost:8000/wetten/BWBR0018451", "03_law_detail_zorgtoeslag.png", "#Artikel1"
        )

        # Scroll to show more content
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(1)
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "03b_law_detail_scrolled.png"))

        # 4. YAML detail (Zorgtoeslag - dark/onderwater)
        take_screenshot(
            driver,
            "http://localhost:8000/wetten/BWBR0018451/yaml/law/zorgtoeslagwet/TOESLAGEN-2025-01-01.yaml",
            "04_yaml_detail_zorgtoeslag.png",
            ".rule-section",
        )

        # Scroll to show regelspraak
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(1)
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "04b_yaml_detail_scrolled.png"))

        # 5. Test navigation flow - click through
        print("\n🧭 Testing navigation flow...")

        # Go back to homepage
        driver.get("http://localhost:8000/")
        time.sleep(1)

        # Click on Zorgtoeslag card
        zorgtoeslag_card = driver.find_element(By.XPATH, "//h3[contains(text(), 'Zorgtoeslag')]")
        zorgtoeslag_card.click()
        time.sleep(1)
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "05_clicked_zorgtoeslag.png"))

        # Click on "Bekijk wettekst" if we're on the homepage
        try:
            wettekst_btn = driver.find_element(By.XPATH, "//a[contains(text(), 'Bekijk wettekst')]")
            wettekst_btn.click()
            time.sleep(1)
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "06_law_page_from_burger.png"))
        except:
            print("Already on law page")

        # Click on "Bekijk in Regelspraak" for an article
        try:
            regelspraak_btn = driver.find_element(By.XPATH, "//a[contains(text(), 'Bekijk in Regelspraak')]")
            regelspraak_btn.click()
            time.sleep(2)
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "07_yaml_from_law.png"))
        except:
            print("Could not find Regelspraak button")

        # Check if we can go back to law text
        try:
            back_btn = driver.find_element(By.XPATH, "//a[contains(text(), 'Terug naar Wettekst')]")
            back_btn.click()
            time.sleep(1)
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "08_back_to_law.png"))
        except:
            print("Could not find back button")

        print(f"\n✅ All screenshots captured! Check the '{SCREENSHOT_DIR}' directory")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
