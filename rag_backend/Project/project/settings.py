import scrapy_poet
import scrapy_zyte_api

BOT_NAME = "project"

SPIDER_MODULES = ["project.spiders"]
NEWSPIDER_MODULE = "project.spiders"

ADDONS = {
    scrapy_poet.Addon: 300,
    scrapy_zyte_api.Addon: 500,
}

SCRAPY_POET_DISCOVER = ["project.pages"]

#ZYTE_API_TOKEN = "YOUR_API_TOKEN"
ZYTE_API_KEY = "aa9711ba11aa46c591fab5e83b00f12d"
