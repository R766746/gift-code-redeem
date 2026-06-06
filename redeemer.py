"""
redeemer.py
-----------
Advanced impersonation-based gift code redeemer.
Uses curl_cffi to match low-level browser TLS fingerprints.
"""

import time
# This line is crucial: it grabs the impersonation engine specifically for redeemer.py
from curl_cffi import requests as impersonated_requests

SITE_URL = "https://ks-giftcode.centurygame.com/"
REDEEM_API_URL = "https://ks-giftcode.centurygame.com/api/redeem" 
BETWEEN_PLAYERS = 1.2


def build_driver(headless: bool = True):
    """Maintains seamless compatibility with main.py runner."""
    return MockDriver()


class MockDriver:
    """Mock fallback class interface."""
    def quit(self):
        pass


def redeem_single_api(session, pid, username, code, log):
    """Submits request with an identical hardware TLS fingerprint to Chrome."""
    
    # Matching the exact network body parameters accepted by the portal
    payload = {
        "playerId": str(pid).strip(),
        "cdk": str(code).strip(),
        "lang": "en"
    }

    try:
        # Submit payload with hardware-level impersonation enabled
        response = session.post(
            REDEEM_API_URL, 
            json=payload, 
            timeout=15
        )
        
        if response.status_code == 200:
            res_json = response.json()
            status_code = res_json.get("code", -1)
            msg = res_json.get("msg", res_json.get("message", "Processed"))
            
            if status_code == 0 or "success" in msg.lower():
                return True, f"Success — {msg}"
            else:
                return False, f"Server Rejected: {msg} (Code: {status_code})"
                
        elif response.status_code == 403:
            return False, "403 Forbidden: Protected by higher-level firewall validation rules."
        else:
            return False, f"HTTP Error {response.status_code}"
            
    except Exception as e:
        return False, f"Network exception encountered: {str(e)}"


def redeem_code_for_all_players(code: str, players: list, log):
    """Iterates through account entries utilizing an impersonated Chrome session."""
    success_count = 0
    fail_count = 0
    start_time = time.time()

    # Change requests.Session to impersonated_requests.Session here
    with impersonated_requests.Session(impersonate="chrome") as session:
        # Pre-seed session headers matching normal web interaction
        session.headers.update({
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://ks-giftcode.centurygame.com",
            "Referer": "https://ks-giftcode.centurygame.com/"
        })
        # Hit the home root first to gracefully fetch underlying verification elements
        try:
            session.get(SITE_URL, timeout=5)
        except:
            pass

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
