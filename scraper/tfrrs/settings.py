from pathlib import Path

BOT_NAME = "tfrrs"

SPIDER_MODULES = ["tfrrs.spiders"]
NEWSPIDER_MODULE = "tfrrs.spiders"

ROBOTSTXT_OBEY = True

DEFAULT_REQUEST_HEADERS = {
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/78.0.3904.87 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

ITEM_PIPELINES = {
    "tfrrs.pipelines.TfrrsPipeline": 300,
}

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 30
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# Write scraped results next to the Streamlit app by default.
REPO_ROOT = Path(__file__).resolve().parents[2]
RACE_DB_PATH = str(REPO_ROOT / "app" / "racedata.db")
SCRAPE_ERROR_LOG = str(REPO_ROOT / "data" / "scrape_errors.log")

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
