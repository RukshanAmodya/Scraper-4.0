module.exports = {
  apps: [
    {
      name: "faymas-scraper",
      script: "faymas_scraper.py",
      interpreter: "python3",
      args: "--daemon --interval 60",
      autorestart: true,
      watch: false,
      max_memory_restart: "500M",
      env: {
        PYTHONUNBUFFERED: "1"
      }
    }
  ]
};
