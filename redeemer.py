"""
redeemer.py
-----------
Optimized API-based gift code redeemer.
Bypasses heavy Selenium Chrome engines by sending direct HTTP requests 
to the CenturyGame gift code server endpoint.
"""

import time
import requests

SITE_URL = "https://ks-giftcode.centurygame.com/"
# Endpoint derived from form submissions on the official redemption gateway
REDEEM_API_URL = "https://ks-giftcode.centurygame.com/api/redeem" 

WAIT_TIMEOUT = 15
BETWEEN_PLAYERS = 1.0  # Safe pacing delay (seconds) to prevent rate limits


def build_driver(headless: bool = True):
    """
    Mock function kept to maintain compatibility with main.py 
    without requiring modifications to the orchestrator.
    """
    return MockDriver()


class MockDriver:
    """Fake driver structure to keep main.py from throwing AttributeError."""
    def quit(self):
        pass


def redeem_single_api(session, pid, username, code, log):
    """Sends a direct web request payload to redeem the code for a player."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Referer": SITE_URL
    }
    
    payload = {
        "playerId": str(pid),
        "cdk": str(code),
        "lang": "en"
    }

    try:
        # Submit the network request directly to the backend redemption service
        response = session.post(REDEEM_API_URL, json=payload, headers=headers, timeout=WAIT_TIMEOUT)
        
        if response.status_code == 200:
            res_json = response.json()
            # Handle typical backend response structures (adjust keys based on actual API payload)
            msg = res_json.get("msg", res_json.get("message", "No response message"))
            code_status = res_json.get("code", -1)
            
            if code_status == 0 or "success" in msg.lower():
                return True, f"Success: {msg}"
            else:
                return False, f"Rejected: {msg}"
        else:
            return False, f"HTTP Error {response.status_code}"
            
    except Exception as e:
        return False, f"Network Connection Error: {str(e)}"


def redeem_code_for_all_players(code: str, players: list, log):
    """Iterates through all players using a persistent connection session."""
    success_count = 0
    fail_count = 0
    start_time = time.time()

    # Use a requests Session to reuse connection sockets (makes it incredibly fast)
    with requests.Session() as session:
        for pid, username in players:
            success, reason = redeem_single_api(session, pid, username, code, log)
            
            if success:
                log.info(f"    ✅ SUCCESS — {username} ({pid}) -> {reason}")
                success_count += 1
            else:
                log.warning(f"    ❌ FAILED  — {username} ({pid}) -> {reason}")
                fail_count += 1
                
            time.sleep(BETWEEN_PLAYERS)

    elapsed = time.time() - start_time
    log.info(f"\n  Summary for code {code}:")
    log.info(f"    Total Players processed: {len(players)}")
    log.info(f"    Successes: {success_count} | Failures: {fail_count}")
    log.info(f"    Time elapsed: {elapsed:.2f} seconds")
