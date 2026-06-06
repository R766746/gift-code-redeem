"""
redeemer.py
-----------
Handles Selenium-based gift code redemption on
https://ks-giftcode.centurygame.com/

Flow per player:
  1. Load page
  2. Enter Player ID → click Login → wait for profile to appear
  3. Enter Gift Code
  4. Click Confirm → wait for result popup
  5. Log result and move to next player
"""

import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

SITE_URL = "https://ks-giftcode.centurygame.com/"

# Delays (seconds) — adjust if site is too slow or too fast
WAIT_TIMEOUT       = 15   # Max wait for any element
POST_LOGIN_WAIT    = 3    # Wait after login loads profile
POST_CONFIRM_WAIT  = 3    # Wait after clicking Confirm
BETWEEN_PLAYERS    = 2    # Pause between players


def build_driver(headless: bool = True) -> webdriver.Chrome:
    """Build and return a Chromium WebDriver instance using native Selenium core."""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1280,800")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    # Point Selenium directly to the Chromium binary provided by Nixpacks
    chrome_options.binary_location = "/usr/bin/chromium"

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def wait_for_element(wait, by, value, description="element"):
    """Wait for an element and return it, raising a clear error if not found."""
    try:
        return wait.until(EC.presence_of_element_located((by, value)))
    except TimeoutException:
        raise TimeoutException(f"Timed out waiting for {description}")


def wait_for_clickable(wait, by, value, description="button"):
    """Wait for an element to be clickable and return it."""
    try:
        return wait.until(EC.element_to_be_clickable((by, value)))
    except TimeoutException:
        raise TimeoutException(f"Timed out waiting for clickable {description}")


def get_result_message(driver, wait) -> str:
    """
    Try to grab the result popup/toast message after clicking Confirm.
    Returns the text or a fallback string.
    """
    selectors = [
        (By.XPATH, '//*[contains(@class,"result") or contains(@class,"toast") or contains(@class,"modal") or contains(@class,"tip") or contains(@class,"message")]'),
        (By.XPATH, '//div[contains(@class,"popup")]'),
        (By.XPATH, '//div[contains(@class,"dialog")]'),
    ]
    time.sleep(POST_CONFIRM_WAIT)
    for by, xpath in selectors:
        try:
            elements = driver.find_elements(by, xpath)
            for el in elements:
                text = el.text.strip()
                if text and len(text) > 3:
                    return text
        except Exception:
            continue
    return "(no response message captured from website)"


def redeem_single(driver, wait, pid: str, username: str, code: str, log) -> tuple[bool, str]:
    """
    Redeem one gift code for one player.
    Returns a tuple of (is_success, exact_website_response).
    """
    log.info(f"  ▶ Player: {username} (ID: {pid})")

    try:
        # ── Step 1: Load the page ──────────────────────────────────────────────
        driver.get(SITE_URL)

        # ── Step 2: Enter Player ID ────────────────────────────────────────────
        player_input = wait_for_element(
            wait, By.XPATH, '//input[@placeholder="Player ID"]', "Player ID input"
        )
        player_input.clear()
        player_input.send_keys(pid)

        # ── Step 3: Click Login ────────────────────────────────────────────────
        login_btn = wait_for_clickable(
            wait,
            By.XPATH,
            '//div[contains(@class,"login_btn") and contains(@class,"btn")]',
            "Login button"
        )
        login_btn.click()

        # ── Step 4: Wait for profile to load ───────────────────────────────────
        try:
            wait.until(EC.invisibility_of_element_located(
                (By.XPATH, '//*[contains(@class,"loading")]')
            ))
        except TimeoutException:
            pass

        wait_for_element(
            wait, By.XPATH, '//input[@placeholder="Enter Gift Code"]', "Gift Code input"
        )
        time.sleep(POST_LOGIN_WAIT)

        # ── Step 5: Enter Gift Code ────────────────────────────────────────────
        code_input = driver.find_element(By.XPATH, '//input[@placeholder="Enter Gift Code"]')
        code_input.clear()
        code_input.send_keys(code)

        # ── Step 6: Click Confirm ──────────────────────────────────────────────
        confirm_btn = wait_for_clickable(
            wait,
            By.XPATH,
            '//div[contains(@class,"exchange_btn") and contains(text(),"Confirm")]',
            "Confirm button"
        )
        driver.execute_script("arguments[0].click();", confirm_btn)

        # ── Step 7: Capture result ─────────────────────────────────────────────
        result_text = get_result_message(driver, wait)

        result_lower = result_text.lower()
        failed_keywords = ["expired", "invalid", "error", "fail", "already", "used", "wrong"]
        is_success = not any(kw in result_lower for kw in failed_keywords)

        return is_success, result_text

    except TimeoutException as e:
        _save_screenshot(driver, pid, username, "timeout")
        return False, f"Timeout Error: {str(e)}"
    except NoSuchElementException as e:
        _save_screenshot(driver, pid, username, "missing_element")
        return False, f"Element Missing Error: {str(e)}"
    except Exception as e:
        _save_screenshot(driver, pid, username, "error")
        return False, f"Unexpected System Error: {str(e)}"


def _save_screenshot(driver, pid, username, reason):
    """Save a debug screenshot to the screenshots/ folder."""
    try:
        os.makedirs("screenshots", exist_ok=True)
        fname = f"screenshots/debug_{pid}_{username}_{reason}.png"
        driver.save_screenshot(fname)
    except Exception:
        pass


def redeem_code_for_all_players(code: str, players: list, log):
    """
    Redeem `code` for every (pid, username) pair in `players`.
    Uses a single browser session for all players.
    """
    driver = build_driver(headless=True)
    wait = WebDriverWait(driver, WAIT_TIMEOUT)

    success_count = 0
    fail_count    = 0
    start_time    = time.time()

    try:
        for pid, username in players:
            success, exact_msg = redeem_single(driver, wait, pid, username, code, log)
            
            # This directly prints what the website returned to your console output!
            if success:
                log.info(f"    ✅ SUCCESS — {username} ({pid}) -> Website says: '{exact_msg}'")
                success_count += 1
            else:
                log.warning(f"    ❌ FAILED  — {username} ({pid}) -> Website says: '{exact_msg}'")
                fail_count += 1
                
            time.sleep(BETWEEN_PLAYERS)
    finally:
        driver.quit()

    elapsed = time.time() - start_time
    log.info(f"\n  Summary for code [{code}]:")
    log.info(f"  ✅ Success : {success_count}")
    log.info(f"  ❌ Failed  : {fail_count}")
    log.info(f"  ⏱  Time    : {elapsed:.1f}s")
