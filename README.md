# 🚀 Faymas AI Prompt & High-Res Image 24/7 Scraper Bot (Scraper-4.0)

A powerful, production-ready, 24/7 continuous scraper bot that monitors and downloads high-resolution AI images, full AI prompts, and structured metadata from [Faymas.in](https://faymas.in/prompts/ai-image-prompts).

---

## 🌟 Key Features

- **⚡ 24/7 Continuous Monitoring Daemon**: Continuously watches Faymas feeds (Latest, Photography, Anime, Portrait, Cinematic, Fashion, 3D, etc.) and auto-downloads any newly published prompt.
- **🛡️ Instant Deduplication**: Built-in **SQLite Database** (`prompts.db`) ensures zero duplicate downloads even across restarts.
- **🖼️ High-Resolution Image Downloader**: Fetches uncompressed original images directly from the CDN (`.webp` / `.png` / `.jpg`).
- **📝 Companion TXT Prompt Generator**: Creates a companion `.txt` file containing the complete prompt alongside every image.
- **📊 Multi-Format Export**: Auto-syncs all collected data in real-time to:
  - `scraped_data/prompts.json`
  - `scraped_data/prompts.csv`
  - `scraped_data/prompts.db` (SQLite)
  - `scraped_data/images/` (Original image + TXT prompt)
- **🐳 Docker & Docker Compose Ready**: One-command background deployment with automatic restart and volume persistence.
- **🐧 Linux Systemd Service**: Ready-to-use `.service` file for Ubuntu, Debian, CentOS, or VPS servers.
- **🔔 Optional Webhook Support**: Real-time notifications to Discord / Telegram when new prompts are scraped.

---

## 📁 Output Directory Structure

```text
scraped_data/
├── images/
│   ├── 0001_red_shadow.webp       <-- High-resolution image
│   ├── 0001_red_shadow.txt        <-- Full AI prompt & details
│   ├── 0002_maroon_attitude.webp
│   └── 0002_maroon_attitude.txt
├── prompts.json                   <-- JSON database with all prompts
├── prompts.csv                    <-- CSV / Excel spreadsheet
├── prompts.db                     <-- SQLite database with indexes
└── scraper.log                    <-- Rotating execution logs
```

---

## 🚀 Quick Start (Local & Linux Server)

### 1. Requirements
- Python 3.9+ (or `uv` package runner)
- Git

### 2. Installation
```bash
# Clone repository
git clone https://github.com/RukshanAmodya/Scraper-4.0.git
cd Scraper-4.0

# Install dependencies
pip install -r requirements.txt
```

---

## 💻 Usage Commands

### 🟢 1. Run 24/7 Continuous Daemon (Auto-detect & download new prompts)
```bash
# Check feeds every 60 seconds (default)
python faymas_scraper.py --daemon --interval 60
```

### 🟢 2. Run Single Scrape Batch
```bash
# Scrape latest 10 prompts
python faymas_scraper.py --limit 10

# Scrape specific category (anime, photography, portrait, cinematic, fashion, 3d)
python faymas_scraper.py --category anime --limit 25

# Scrape sitemap archive (10,000+ available prompts)
python faymas_scraper.py --category sitemap --limit 100
```

### 🟢 3. Scrape a Single Prompt URL
```bash
python faymas_scraper.py --url "https://faymas.in/prompt/romantic-couple-portrait-in-matching-football-jerseys-02146c9a"
```

---

## 🐳 Docker Deployment (Recommended for VPS / Cloud)

Deploy in background with persistent volume:

```bash
# Start container in detached mode
docker-compose up -d --build

# View real-time logs
docker-compose logs -f

# Stop scraper
docker-compose down
```

---

## 🐧 Linux Server Deployment via Systemd (Ubuntu / Debian VPS)

To run as a permanent background service that automatically restarts on system reboot:

```bash
# 1. Copy project to /opt
sudo cp -r . /opt/faymas-scraper
cd /opt/faymas-scraper

# 2. Install dependencies
sudo pip3 install -r requirements.txt

# 3. Copy systemd service file
sudo cp faymas-scraper.service /etc/systemd/system/

# 4. Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable faymas-scraper
sudo systemctl start faymas-scraper

# 5. Check service status & logs
sudo systemctl status faymas-scraper
sudo journalctl -u faymas-scraper -f
```

---

## ⚙️ CLI Arguments Reference

| Argument | Description | Default |
|---|---|---|
| `--daemon` | Runs continuously in 24/7 monitoring mode | `False` |
| `--interval` | Poll interval in seconds between feed checks | `60` |
| `--limit` | Number of items to scrape in batch mode | `5` |
| `--category` | Category filter (`all`, `photography`, `anime`, `portrait`, `cinematic`, `fashion`, `3d`, `sitemap`) | `all` |
| `--url` | Specific Faymas prompt URL to scrape | `None` |
| `--output` | Output folder for data & images | `scraped_data` |
| `--webhook` | Discord / Custom Webhook URL for new prompt alerts | `None` |
| `--no-images` | Scrape metadata and prompts only (skip downloading images) | `False` |

---

## 📜 License
MIT License. Built for AI researchers, prompt engineers, and developers.
