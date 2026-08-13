"""
Visits the deployed Streamlit app with a real (headless) browser so it
registers as traffic and doesn't hit the 12h sleep threshold. If the app
was already asleep, clicks the "Yes, get this app back up!" button.

Run manually with: python keep_alive.py
"""

from playwright.sync_api import sync_playwright

APP_URL = "https://your-app-name.streamlit.app"  # <-- replace with your real app URL


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(APP_URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(5000)

        wake_button = page.get_by_text("Yes, get this app back up!")
        if wake_button.count() > 0:
            print("App was asleep - clicking wake-up button.")
            wake_button.first.click()
            page.wait_for_timeout(15000)
        else:
            print("App was already awake.")

        browser.close()


if __name__ == "__main__":
    main()
