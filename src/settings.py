from os import path

SETTINGS = {
    "DOWNLOADER_MIDDLEWARES": {
        #"middlewares.SaveHtmlMiddleware.SaveHtmlMiddleware": 1000
    },
    "DOWNLOAD_HANDLERS": {
        "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    },
}

DATA_PATH = path.join(path.dirname(__file__), '../', "data")