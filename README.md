# KingShot Auto Gift Code Redeemer

> **Automatically detects new gift codes from kingshot.net and redeems them
> for all your players on ks-giftcode.centurygame.com — fully hands-free.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Selenium](https://img.shields.io/badge/Selenium-4.20-green.svg)](https://selenium-python.readthedocs.io/)

---

## ⚠️ Before You Use

- This tool is for **personal use** only — to redeem codes for your own player IDs.
- Do **not** abuse or spam the redemption site.
- Gift codes expire; the tool skips codes it has already processed.

---

## How It Works

```
Every 15 minutes:
  → Fetch https://kingshot.net/api/gift-codes
  → Compare with seen_codes.json
  → If NEW code found:
      → Loop through all playerIDs.txt
      → Selenium redeems the code on centurygame.com per player
      → Log results
      → Mark code as done (won't retry same code)
```

---

## Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/Gopi360/GiftCode-Redeem-Automation.git
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Install Google Chrome

- **Ubuntu/Debian:**
  ```bash
  wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
  echo "deb http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
  sudo apt update && sudo apt install -y google-chrome-stable
  ```
- **Windows/Mac:** Download from https://www.google.com/chrome/

### 4. Add your players

Create a file called `playerIDs.txt` — one player per line:
```
876734319   PlayerOne
123456756   PlayerTwo
```
> ⚠️ **Do not share your `playerIDs.txt`** — it contains your private player IDs.
> It is listed in `.gitignore` so it won't be accidentally committed.

### 5. Run
```bash
python main.py
```

---

## File Structure

| File | Purpose |
|------|---------|
| `main.py` | Scheduler — polls API, detects new codes |
| `redeemer.py` | Selenium logic — redeems on centurygame.com |
| `playerIDs.txt` | **You create this** — your player IDs (gitignored) |
| `seen_codes.json` | Auto-created — tracks redeemed codes (gitignored) |
| `logs/` | Daily log files |
| `screenshots/` | Auto-saved on errors for debugging |

---

## Configuration

Edit the top of `main.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `CHECK_INTERVAL` | `15` | Minutes between API polls |

Edit the top of `redeemer.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `POST_LOGIN_WAIT` | `3` | Seconds to wait after login loads |
| `POST_CONFIRM_WAIT` | `3` | Seconds to wait after clicking Confirm |
| `BETWEEN_PLAYERS` | `2` | Pause between each player |
| `headless` | `True` | Set `False` to see the browser window live |

---

## Deployment (24/7 Running)

### Option A — DigitalOcean Droplet (~$4/month, Recommended)
1. Create a $4/mo Ubuntu 24.04 droplet at https://digitalocean.com
2. SSH in and clone this repo
3. Install Chrome + Python deps (see Quick Start above)
4. Keep it running after logout with `screen`:
   ```bash
   screen -S kingshot
   python main.py
   # Press Ctrl+A then D to detach
   # Reattach anytime with: screen -r kingshot
   ```

### Option B — systemd Service (Best for VPS, auto-restarts on reboot)
Create `/etc/systemd/system/kingshot.service`:
```ini
[Unit]
Description=KingShot Auto Gift Code Redeemer
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/kingshot-auto-redeemer
ExecStart=/usr/bin/python3 /home/ubuntu/kingshot-auto-redeemer/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```
Then enable and start it:
```bash
sudo systemctl enable kingshot
sudo systemctl start kingshot
sudo systemctl status kingshot
```

### Option C — Railway.app (Free tier, easiest cloud option)
1. Push this repo to your GitHub
2. Connect it at https://railway.app
3. Create a `Procfile` in the root:
   ```
   worker: python main.py
   ```
4. Railway runs it 24/7 for free within their free tier limits (~500 hrs/month).

### Option D — Your Own PC (Simplest, not reliable)
```bash
python main.py
```
> Stops when your PC shuts down or sleeps.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Script crashes immediately | Make sure `playerIDs.txt` exists |
| Code not being redeemed | Set `headless=False` in `redeemer.py` to watch the browser |
| Element not found errors | The site may have updated its HTML — check XPATHs in `redeemer.py` |
| Chrome not found | Reinstall Google Chrome and ensure it's in your PATH |

- **Error screenshots** are saved automatically to `screenshots/`
- **Logs** are written to `logs/run_YYYYMMDD.log`

---

## Contributing

Pull requests are welcome! If the gift code site changes its layout and breaks the XPATHs, feel free to open an issue or submit a fix.

1. Fork this repo
2. Create a branch: `git checkout -b fix/xpath-update`
3. Commit and push your changes
4. Open a Pull Request

---

## License

Copyright (c) 2025 **[Gopi / Gopi360]**

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

You are free to use, copy, modify, and distribute this software, but you **must** keep the original copyright notice. You may **not** claim this as your own original work.

---

## Author

Made by **[Supriya Gope (Gopi)]** — [github.com/Gopi360](https://github.com/Gopi360)

If this helped you, consider giving the repo a ⭐ on GitHub!