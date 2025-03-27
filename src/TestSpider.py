import scrapy

import DownloadSpider


class TestSpider(DownloadSpider.DownloadSpider):
    name = "healthTest"

    def start_requests(self):
        # GET request
        yield scrapy.Request("https://zdrake.net/_status/health")

    def parse(self, response, **kwargs):
        super().save_response(response)
        # 'response' contains the page as seen by the browser
        return {"url": response.url}

class TestSpider2(DownloadSpider.DownloadSpider):
    name = "test2"

    def start_requests(self):
        # GET request
        yield scrapy.Request("https://google.de", meta={"playwright": True})


    def parse(self, response, **kwargs):
        super().save_response(response)
        # 'response' contains the page as seen by the browser
        return {"url": response.url}