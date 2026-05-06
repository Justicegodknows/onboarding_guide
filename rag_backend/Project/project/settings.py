import scrapy_poet
import scrapy_zyte_api
import os

BOT_NAME = "project"
USER_AGENT = "VaultMindScraper/1.0 (+https://vaultmind.local; contact: engineering@vaultmind.local)"
ROBOTSTXT_OBEY = True

SPIDER_MODULES = ["project.spiders"]
NEWSPIDER_MODULE = "project.spiders"

ADDONS = {
    scrapy_poet.Addon: 300,
    scrapy_zyte_api.Addon: 500,
}

SCRAPY_POET_DISCOVER = ["project.pages"]

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1
FEED_EXPORT_ENCODING = "utf-8"

# ZYTE_API_TOKEN = "YOUR_API_TOKEN"
ZYTE_API_KEY = os.getenv("ZYTE_API_KEY", "")
