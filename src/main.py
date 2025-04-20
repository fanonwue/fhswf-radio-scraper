from scrapy.crawler import CrawlerProcess
from scrapy.utils.reactor import install_reactor
from TestSpider import TestSpider, TestSpider2
from WdrSpider import Wdr1Spider, Wdr2Spider
from settings import SETTINGS

def run():
    install_reactor('twisted.internet.asyncioreactor.AsyncioSelectorReactor')
    process = CrawlerProcess(SETTINGS)
    process.crawl(Wdr1Spider)
    process.crawl(Wdr2Spider)
    process.crawl(TestSpider)
    process.crawl(TestSpider2)
    process.start()

if __name__ == '__main__':
    run()