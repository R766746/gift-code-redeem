"""
redeemer.py
-----------
Optimized API-based gift code redeemer.
Spoofs browser contexts to bypass CenturyGame 403 authorization walls.
"""

import time
import requests

SITE_URL = "https://ks-giftcode.centurygame.com/"
REDEEM_API_URL = "https://ks-giftcode.centurygame.com/api/redeem" 

WAIT_TIMEOUT = 15
BETWEEN_PLAYERS = 1.5  # Strategic human-like delay pacing


def build_driver(headless: bool = True):
    """Maintains backward compatibility interface for main.py."""
    return MockDriver()


class MockDriver:
    """Mock interface fallback."""
    def quit(self):
        pass


def redeem_single_api(session, pid, username, code, log):
    """Sends browser-identical headers to look like a direct web form submit."""
    
    # Complete browser handshake fingerprint to resolve HTTP 403
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://ks-giftcode.centurygame.com",
        "Referer": "https://ks-giftcode.centurygame.com/",
        "Sec-CH-UA": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Connection": "keep-alive"
    }
    
    # Exact payload naming conventions accepted by CenturyGame endpoint interfaces
    payload = {
        "playerId": str(pid).strip(),
        "cdk": str(code).strip(),
        "lang": "en"
    }

    try:
        # Perform the direct post request passing our tracking simulation footprint
        response = session.post(REDEEM_API_URL, json=payload, headers=headers, timeout=WAIT_TIMEOUT)
        
        if response.status_code == 200:
            res_json = response.json()
            
            # The game uses a 'code' value status (0 is typically success, 400+ error)
            status_code = res_json.get("code", -1)
            msg = res_json.get("msg", res_json.get("message", "Unknown Status"))
            
            if status_code == 0 or "success" in msg.lower():
                return True, f"Success — {msg}"
            else:
                return False, f"Server Rejected: {msg} (Status Code: {status_code})"
                
        elif response.status_code == 403:
            return False, "403 Forbidden: Server requires interactive token/cookie verification."
        else:
            return False, f"HTTP Error {response.status_code} — {response.text[:100]}"
            
    except Exception as e:
        return False, f"Connection failure: {str(e)}"


def redeem_code_for_all_players(code: str, players: list, log):
    """Iterates through all loaded players using a pooled connection state."""
    success_count = 0
    fail_count = 0
    start_time = time.time()

    # Pre-heat connection pool to look like a continuous user session
    with requests.Session() as session:
        # Establish base cookies from the main landing page first
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
