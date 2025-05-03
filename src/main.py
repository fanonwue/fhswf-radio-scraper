from scrapy.crawler import CrawlerProcess
from scrapy.utils.reactor import install_reactor
from OffizielleChartsSpider import OffizielleChartsSpider
from settings import SETTINGS

def run():
    install_reactor('twisted.internet.asyncioreactor.AsyncioSelectorReactor')
    process = CrawlerProcess(SETTINGS)
    # process.crawl(TestSpider)
    # process.crawl(TestSpider2)
    process.crawl(OffizielleChartsSpider)
    process.start()

if __name__ == '__main__':
    run()