"""
redeemer.py
-----------
Playwright-based gift code redeemer.
Bypasses 403 authorization walls by running a modern headless browser engine.
"""

import time
from playwright.sync_api import sync_playwright

SITE_URL = "https://ks-giftcode.centurygame.com/"
BETWEEN_PLAYERS = 2.0  # Human-like delay pacing between inputs


def build_driver(headless: bool = True):
    """Maintains backward compatibility interface for main.py."""
    return MockDriver()


class MockDriver:
    """Mock interface fallback."""
    def quit(self):
        pass


def redeem_code_for_all_players(code: str, players: list, log):
    """Launches a headless browser to physically input codes on the website."""
    success_count = 0
    fail_count = 0
    start_time = time.time()

    log.info("🚀 Launching Cloud-Optimized Browser Environment...")

    with sync_playwright() as p:
        # Launch headless Chromium browser instance
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
        )
        
        # Create an isolated browser context with a human-like viewport and user agent
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        
        page = context.new_page()

        for pid, username in players:
            try:
                # 1. Navigate to the official redemption gateway page
                page.goto(SITE_URL, timeout=30000)
                page.wait_for_load_state("networkidle")

                # 2. Locate and fill the Player ID text input box
                # (Matches common input field structures; will fall back cleanly)
                id_input = page.locator("input[placeholder*='ID'], input[type='text']").first
                id_input.click()
                id_input.fill("")  # Clear field
                id_input.type(str(pid), delay=50)

                # 3. Locate and fill the Gift Code / CDK text input box
                code_input = page.locator("input[placeholder*='code'], input[placeholder*='CDK']").first
                code_input.click()
                code_input.fill("")  # Clear field
                code_input.type(str(code), delay=50)

                # 4. Locate and click the Submit/Redeem button
                redeem_btn = page.locator("button:has-text('Redeem'), button:has-text('Confirm'), [class*='btn']").first
                redeem_btn.click()

                # 5. Brief wait to let the success/error pop-up render on-screen
                time.sleep(1.5)

                # 6. Read the feedback popup message (Common alert container text elements)
                feedback_element = page.locator("[class*='dialog'], [class*='alert'], [class*='toast'], [class*='msg']").first
                if feedback_element.is_visible():
                    msg = feedback_element.inner_text().strip().replace('\n', ' ')
                else:
                    msg = "Submitted (Popup cleared or inline response)"

                log.info(f"    ✅ PROCESSED — {username} ({pid}) -> Result: {msg}")
                success_count += 1

            except Exception as e:
                log.warning(f"    ❌ ERROR — {username} ({pid}) -> Operation failed: {str(e)}")
                fail_count += 1

            # Safe human pacing buffer before moving to the next account
            time.sleep(BETWEEN_PLAYERS)

        # Gracefully shutter browser processes
        context.close()
        browser.close()

    elapsed = time.time() - start_time
    log.info(f"\n  Summary for code {code}:")
    log.info(f"    Total Players processed: {len(players)}")
    log.info(f"    Successes/Processed: {success_count} | Failures: {fail_count}")
    log.info(f"    Time elapsed: {elapsed:.2f} seconds")
