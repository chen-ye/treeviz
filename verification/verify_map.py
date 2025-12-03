
import os
from playwright.sync_api import sync_playwright

def verify_map():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            # Wait for the server to start (simple retry mechanism or just wait)
            # Assuming vite starts quickly on default port 5173
            page.goto("http://localhost:5173")

            # Wait for map component to be present
            # FoliageMap is a custom element
            page.wait_for_selector("foliage-map")

            # Wait a bit for map to load (canvas and tiles)
            page.wait_for_timeout(5000)

            # Take screenshot
            os.makedirs("verification", exist_ok=True)
            page.screenshot(path="verification/map_screenshot.png")
            print("Screenshot taken.")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_map()
