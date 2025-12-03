from playwright.sync_api import sync_playwright

def verify_frontend():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Navigating to frontend...")
        page.goto("http://localhost:5173")

        # Wait for map container
        page.wait_for_selector("#map")
        print("Map container found.")

        # Wait for canvas (DeckGL)
        page.wait_for_selector("canvas", timeout=10000)
        print("DeckGL Canvas found.")

        # Wait a bit for tiles/points to load
        page.wait_for_timeout(3000)

        # Take screenshot
        output_path = "verification.png"
        page.screenshot(path=output_path)
        print(f"Screenshot saved to {output_path}")

        browser.close()

if __name__ == "__main__":
    verify_frontend()
