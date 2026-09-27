@echo off
title Faymas AI Prompt & Image Scraper Bot
echo ======================================================
echo       Faymas AI Image & Prompt Scraper Bot
echo ======================================================
echo.
echo 1. Scrape Latest Prompts (Default: 10 items)
echo 2. Scrape Specific Category (Photography, Anime, etc.)
echo 3. Scrape by Custom Count (e.g. 5, 20, 50, 100)
echo 4. Scrape Single Prompt URL
echo 5. Bulk Scrape Archive from Sitemap (10,000+ available)
echo 6. Exit
echo.
set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" (
    uv run --with requests,beautifulsoup4 python faymas_scraper.py --limit 10
)
if "%choice%"=="2" (
    echo Available categories: photography, portrait, anime, cinematic, fashion, 3d
    set /p cat="Enter category name: "
    set /p count="Enter number of items to scrape: "
    uv run --with requests,beautifulsoup4 python faymas_scraper.py --category %cat% --limit %count%
)
if "%choice%"=="3" (
    set /p count="Enter number of prompts to scrape: "
    uv run --with requests,beautifulsoup4 python faymas_scraper.py --limit %count%
)
if "%choice%"=="4" (
    set /p target_url="Enter Faymas prompt URL: "
    uv run --with requests,beautifulsoup4 python faymas_scraper.py --url %target_url%
)
if "%choice%"=="5" (
    set /p count="Enter number of archive prompts to scrape (e.g. 50, 100, 500): "
    uv run --with requests,beautifulsoup4 python faymas_scraper.py --category sitemap --limit %count%
)
if "%choice%"=="6" (
    exit
)

echo.
echo ======================================================
echo Done! Data saved in the 'scraped_data' folder.
echo ======================================================
pause
