from DownloadSpider import DownloadSpider
import scrapy

class OffizielleChartsSpider(DownloadSpider):
    name = "OffizielleCharts"
    # run daily
    interval = 60 * 60 * 24

    def start_requests(self):
        yield scrapy.Request("https://www.offiziellecharts.de/charts/single")

    def parse(self, response, **kwargs):
        super().save_response(response)
        # 'response' contains the page as seen by the browser
        return {"url": response.url}