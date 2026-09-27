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

## 🚀 Non-Docker 24/7 Deployment Options (Docker නැතුව Run කරන ක්‍රම)

### Option 1: Using PM2 (වඩාත්ම පහසු සහ ජනප්‍රියම ක්‍රමය ⭐)
PM2 මගින් script එක background එකේ run වීම, crash වුවහොත් auto-restart වීම සහ logs බලාගැනීම ඉතාම පහසුය.

```bash
# 1. PM2 install කරගන්න (server එකේ නැත්නම්)
sudo apt install npm -y && sudo npm install -g pm2

# 2. Scraper එක background එකේ run කරන්න
pm2 start ecosystem.config.js
# හෝ කෙලින්ම:
pm2 start faymas_scraper.py --name "faymas-bot" --interpreter python3 -- --daemon --interval 60

# 3. Server reboot වුවත් auto start වීමට
pm2 startup
pm2 save

# Commands:
pm2 logs faymas-scraper    # Live logs බැලීමට
pm2 status                 # Status බැලීමට
pm2 restart faymas-scraper # Restart කිරීමට
pm2 stop faymas-scraper    # Stop කිරීමට
```

---

### Option 2: Using Linux `screen` / `tmux` (තත්පර 5න් Setup කළ හැකි ක්‍රමය)
Terminal එක close කළත් background එකේ run වේ:

```bash
# 1. Screen session එකක් open කරන්න
screen -S faymas_bot

# 2. Scraper එක run කරන්න
python3 faymas_scraper.py --daemon --interval 60

# 3. Detach වීමට (keyboard shortcut):
# Ctrl + A ඔබා පසුව D ඔබන්න.

# නැවත screen එකට ඇතුළු වීමට:
screen -r faymas_bot
```

---

### Option 3: Using `nohup` (Linux Default Command)
කිසිදු අමතර software එකක් install නොකර:

```bash
# Background එකේ run කර log එක save කරගැනීම
nohup python3 faymas_scraper.py --daemon --interval 60 > scraper_output.log 2>&1 &

# Logs බලන්න
tail -f scraper_output.log
```

---

### Option 4: Linux Systemd Service (Ubuntu / Debian VPS)
```bash
sudo cp faymas-scraper.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now faymas-scraper
```

---

## 🐳 Docker Deployment (Optional)

```bash
docker-compose up -d --build
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
