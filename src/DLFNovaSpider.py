from DownloadSpider import DownloadSpider
import scrapy


class DLFNovaSpider(DownloadSpider):
    name = "DLFNova"
    # run daily
    interval = 60 * 60 * 24
    compress = True

    def start_requests(self):
        yield scrapy.Request("https://www.deutschlandfunknova.de/playlist")

    def parse(self, response, **kwargs):
        super().save_response(response)
        # 'response' contains the page as seen by the browser
        return {"url": response.url}
