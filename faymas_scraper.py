"""
Faymas AI Image & Prompt 24/7 Continuous Scraper Bot
====================================================
Features:
- Continuous 24/7 monitoring daemon for Linux servers / VPS / Docker / Local.
- Instant deduplication using SQLite Database + JSON + CSV sync.
- Automatically detects new prompts on Faymas.in and downloads high-res images + prompt text.
- Supports multi-category polling, sitemap archive scraping, and single URL downloads.
- Graceful shutdown, rotating logs, and webhook notification support.
"""

import os
import sys
import io
import re
import json
import csv
import time
import signal
import sqlite3
import logging
import argparse
from datetime import datetime
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup

# Ensure UTF-8 output encoding for console
if sys.stdout and hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except Exception:
        pass

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

CATEGORIES = ["photography", "portrait", "anime", "cinematic", "fashion", "3d"]

class FaymasScraper:
    def __init__(self, output_dir="scraped_data", download_images=True, webhook_url=None):
        self.output_dir = output_dir
        self.images_dir = os.path.join(output_dir, "images")
        self.download_images = download_images
        self.webhook_url = webhook_url
        self.running = True
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        
        os.makedirs(self.output_dir, exist_ok=True)
        if self.download_images:
            os.makedirs(self.images_dir, exist_ok=True)

        self.db_path = os.path.join(self.output_dir, "prompts.db")
        self.json_path = os.path.join(self.output_dir, "prompts.json")
        self.csv_path = os.path.join(self.output_dir, "prompts.csv")
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database for deduplication and indexing."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE,
                    slug TEXT,
                    title TEXT,
                    category TEXT,
                    prompt TEXT,
                    image_url TEXT,
                    local_image_path TEXT,
                    author TEXT,
                    author_url TEXT,
                    tags TEXT,
                    date_published TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def is_already_scraped(self, url):
        """Check if URL already exists in database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM prompts WHERE url = ?", (url,))
            return cursor.fetchone() is not None

    def get_total_scraped_count(self):
        """Return total number of items stored in database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM prompts")
            return cursor.fetchone()[0]

    def extract_prompt_details(self, prompt_url):
        """Extract prompt text, image url, and metadata from a prompt page."""
        try:
            resp = self.session.get(prompt_url, timeout=15)
            if resp.status_code != 200:
                logging.warning(f"[!] Failed to fetch {prompt_url} (HTTP {resp.status_code})")
                return None
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            slug = prompt_url.rstrip("/").split("/")[-1]
            
            data = {
                "url": prompt_url,
                "slug": slug,
                "title": "",
                "prompt": "",
                "image_url": "",
                "author": "",
                "author_url": "",
                "category": "",
                "tags": [],
                "date_published": "",
            }

            # 1. Parse JSON-LD metadata
            ld_scripts = soup.find_all('script', type='application/ld+json')
            for script in ld_scripts:
                try:
                    ld_data = json.loads(script.string)
                    graph = ld_data.get('@graph', [ld_data]) if isinstance(ld_data, dict) else []
                    for item in graph:
                        if item.get('@type') == 'CreativeWork':
                            data["title"] = item.get("name", "")
                            data["prompt"] = item.get("text", "")
                            data["category"] = item.get("genre", "")
                            data["date_published"] = item.get("datePublished", "")
                            
                            # Images
                            img_list = item.get("image", [])
                            if isinstance(img_list, list) and len(img_list) > 0:
                                if isinstance(img_list[0], dict):
                                    data["image_url"] = img_list[0].get("url", "")
                                elif isinstance(img_list[0], str):
                                    data["image_url"] = img_list[0]
                                    
                            # Author
                            author = item.get("author", {})
                            if isinstance(author, dict):
                                data["author"] = author.get("name", "")
                                data["author_url"] = author.get("url", "")
                            
                            # Tags / Keywords
                            keywords = item.get("keywords", "")
                            if keywords:
                                data["tags"] = [k.strip() for k in keywords.split(",") if k.strip()]
                            break
                except Exception:
                    pass

            # 2. Fallback to OpenGraph / Meta tags
            if not data["image_url"]:
                og_img = soup.find('meta', property='og:image')
                if og_img and og_img.get('content'):
                    data["image_url"] = og_img['content']
                    
            if not data["title"]:
                og_title = soup.find('meta', property='og:title')
                if og_title and og_title.get('content'):
                    data["title"] = og_title['content'].replace(" | Faymas", "").strip()
                elif soup.title:
                    data["title"] = soup.title.string.replace(" | Faymas", "").strip()

            if not data["prompt"]:
                og_desc = soup.find('meta', property='og:description')
                if og_desc and og_desc.get('content'):
                    data["prompt"] = og_desc['content']

            # Clean fallback title
            if not data["title"]:
                data["title"] = slug.replace("-", " ").title()

            return data
        except Exception as e:
            logging.error(f"[!] Error extracting {prompt_url}: {e}")
            return None

    def download_image_file(self, image_url, base_name):
        """Download high-res image and return saved file path."""
        if not image_url:
            return None
        try:
            safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', base_name)[:70].strip('_')
            ext = os.path.splitext(urlparse(image_url).path)[1]
            if not ext or len(ext) > 5:
                ext = ".webp"
            
            filename = f"{safe_name}{ext}"
            filepath = os.path.join(self.images_dir, filename)
            
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                return filepath

            r = self.session.get(image_url, stream=True, timeout=20)
            if r.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                return filepath
        except Exception as e:
            logging.error(f"[!] Error downloading image {image_url}: {e}")
        return None

    def save_single_entry(self, data):
        """Save a new prompt to SQLite DB, local txt file, and append to JSON & CSV."""
        # 1. Save to SQLite
        tags_str = ", ".join(data.get("tags", [])) if isinstance(data.get("tags"), list) else str(data.get("tags", ""))
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO prompts (url, slug, title, category, prompt, image_url, local_image_path, author, author_url, tags, date_published)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get("url"),
                data.get("slug"),
                data.get("title"),
                data.get("category"),
                data.get("prompt"),
                data.get("image_url"),
                data.get("local_image_path"),
                data.get("author"),
                data.get("author_url"),
                tags_str,
                data.get("date_published")
            ))
            conn.commit()

        # 2. Sync / append to prompts.json
        all_prompts = []
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    all_prompts = json.load(f)
            except Exception:
                all_prompts = []
        
        # Check if URL already in json
        if not any(p.get("url") == data.get("url") for p in all_prompts):
            all_prompts.insert(0, data)
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(all_prompts, f, ensure_ascii=False, indent=2)

        # 3. Append to prompts.csv
        file_exists = os.path.exists(self.csv_path)
        fields = ["title", "category", "prompt", "image_url", "local_image_path", "author", "tags", "date_published", "url"]
        with open(self.csv_path, 'a', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
            if not file_exists:
                writer.writeheader()
            row_copy = dict(data)
            row_copy["tags"] = tags_str
            writer.writerow(row_copy)

    def process_prompt_url(self, url, index_prefix=None):
        """Scrape, download image, write txt, and persist prompt."""
        if self.is_already_scraped(url):
            return None

        data = self.extract_prompt_details(url)
        if not data:
            return None

        # Base naming for files
        slug = data.get("slug") or "prompt"
        prefix = f"{index_prefix:04d}_" if index_prefix is not None else f"{int(time.time())}_"
        file_base_name = f"{prefix}{slug}"

        # Download high-res image
        if self.download_images and data.get("image_url"):
            saved_img_path = self.download_image_file(data["image_url"], file_base_name)
            data["local_image_path"] = saved_img_path
            
            # Save companion text file
            txt_filename = f"{file_base_name}.txt"
            txt_path = os.path.join(self.images_dir, txt_filename)
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"Title: {data['title']}\n")
                f.write(f"Category: {data['category']}\n")
                f.write(f"Author: {data['author']}\n")
                f.write(f"Source URL: {data['url']}\n")
                f.write(f"Date: {data['date_published']}\n\n")
                f.write(f"=== PROMPT ===\n{data['prompt']}\n")

        self.save_single_entry(data)
        logging.info(f"[+] NEW PROMPT SCRAPED: {data['title']} ({data['category']})")
        
        # Webhook notification (Optional Discord / Custom)
        if self.webhook_url:
            self._send_webhook(data)

        return data

    def _send_webhook(self, data):
        """Send notification webhook when a new prompt is scraped."""
        try:
            payload = {
                "content": f"🎨 **New AI Prompt Scraped!**\n**Title:** {data['title']}\n**Category:** {data['category']}\n**Prompt:** {data['prompt'][:250]}...\n{data['url']}"
            }
            requests.post(self.webhook_url, json=payload, timeout=5)
        except Exception as e:
            logging.debug(f"Webhook notification failed: {e}")

    def get_prompt_urls_from_listing(self, listing_url):
        """Extract prompt URLs from a category or listing page."""
        try:
            resp = self.session.get(listing_url, timeout=15)
            if resp.status_code != 200:
                return []
            soup = BeautifulSoup(resp.text, 'html.parser')
            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/prompt/' in href and not href.endswith('/prompts') and not href.endswith('/ai-image-prompts'):
                    if not href.startswith('http'):
                        href = 'https://faymas.in' + href
                    if href not in links:
                        links.append(href)
            return links
        except Exception as e:
            logging.error(f"[!] Error fetching listing {listing_url}: {e}")
            return []

    def get_sitemap_urls(self, limit=None):
        """Fetch prompt URLs from sitemap.xml."""
        sitemap_url = "https://faymas.in/sitemap.xml"
        try:
            logging.info(f"[*] Fetching sitemap: {sitemap_url}...")
            resp = self.session.get(sitemap_url, timeout=25)
            if resp.status_code == 200:
                urls = re.findall(r'https://faymas\.in/prompt/[^\s<]+', resp.text)
                logging.info(f"[*] Total prompts found in sitemap: {len(urls)}")
                if limit:
                    return urls[:limit]
                return urls
        except Exception as e:
            logging.error(f"[!] Error reading sitemap: {e}")
        return []

    def run_once(self, limit=None, category=None):
        """Run a single scrape batch."""
        if category == "sitemap":
            urls = self.get_sitemap_urls(limit=limit)
        elif category and category in CATEGORIES:
            urls = self.get_prompt_urls_from_listing(f"https://faymas.in/category/{category}")
        else:
            urls = self.get_prompt_urls_from_listing("https://faymas.in/prompts/ai-image-prompts")

        if limit:
            urls = urls[:limit]

        new_count = 0
        total = len(urls)
        logging.info(f"[*] Checking {total} prompts...")

        for idx, url in enumerate(urls, 1):
            if self.is_already_scraped(url):
                continue
            res = self.process_prompt_url(url, index_prefix=self.get_total_scraped_count() + 1)
            if res:
                new_count += 1
            time.sleep(0.4)

        logging.info(f"[✓] Batch finished! New items added: {new_count}. Total in DB: {self.get_total_scraped_count()}")

    def run_daemon(self, interval_seconds=60):
        """Run continuously 24/7 on a server, checking feeds periodically for new prompts."""
        logging.info(f"[*] Starting Faymas 24/7 Continuous Daemon (Check interval: {interval_seconds}s)")
        logging.info(f"[*] Data directory: {os.path.abspath(self.output_dir)}")
        logging.info(f"[*] Current stored prompts in DB: {self.get_total_scraped_count()}")

        def handle_signal(sig, frame):
            logging.info("\n[*] Shutdown signal received. Stopping daemon gracefully...")
            self.running = False

        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        cycle = 0
        while self.running:
            cycle += 1
            start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logging.info(f"\n--- [Cycle #{cycle} @ {start_time}] Checking feeds for new prompts ---")
            
            # 1. Check latest prompts feed
            all_check_urls = self.get_prompt_urls_from_listing("https://faymas.in/prompts/ai-image-prompts")
            
            # 2. Check each category feed periodically
            for cat in CATEGORIES:
                if not self.running:
                    break
                cat_urls = self.get_prompt_urls_from_listing(f"https://faymas.in/category/{cat}")
                for u in cat_urls:
                    if u not in all_check_urls:
                        all_check_urls.append(u)
                time.sleep(0.3)

            # Filter out already scraped
            new_urls = [u for u in all_check_urls if not self.is_already_scraped(u)]
            logging.info(f"[*] Found {len(all_check_urls)} feed items | New unseen items: {len(new_urls)}")

            # Process new items
            new_count = 0
            for u in new_urls:
                if not self.running:
                    break
                res = self.process_prompt_url(u, index_prefix=self.get_total_scraped_count() + 1)
                if res:
                    new_count += 1
                time.sleep(0.5)

            logging.info(f"[*] Cycle #{cycle} completed. {new_count} new prompts downloaded. Total in DB: {self.get_total_scraped_count()}")

            # Sleep until next check
            for _ in range(interval_seconds):
                if not self.running:
                    break
                time.sleep(1)

        logging.info("[*] Daemon stopped cleanly.")


def setup_logger(log_dir="scraped_data"):
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "scraper.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    parser = argparse.ArgumentParser(description="Faymas AI Image & Prompt 24/7 Scraper Bot")
    parser.add_argument("--daemon", action="store_true", help="Run 24/7 in continuous background mode")
    parser.add_argument("--interval", type=int, default=60, help="Daemon check interval in seconds (default: 60)")
    parser.add_argument("--limit", type=int, default=5, help="Number of prompts to scrape in single run (default: 5)")
    parser.add_argument("--category", type=str, default="all", help="Category: all, photography, portrait, anime, cinematic, fashion, 3d, sitemap")
    parser.add_argument("--url", type=str, help="Single prompt URL to scrape directly")
    parser.add_argument("--output", type=str, default="scraped_data", help="Output directory (default: scraped_data)")
    parser.add_argument("--webhook", type=str, default=os.getenv("WEBHOOK_URL"), help="Optional Discord/Telegram notification webhook URL")
    parser.add_argument("--no-images", action="store_true", help="Skip downloading images")
    
    args = parser.parse_args()
    setup_logger(args.output)

    scraper = FaymasScraper(
        output_dir=args.output,
        download_images=not args.no_images,
        webhook_url=args.webhook
    )

    if args.daemon:
        scraper.run_daemon(interval_seconds=args.interval)
    elif args.url:
        scraper.process_prompt_url(args.url)
    else:
        scraper.run_once(limit=args.limit, category=args.category)


if __name__ == "__main__":
    main()
