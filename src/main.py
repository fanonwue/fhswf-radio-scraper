from datetime import date, datetime
import SRF3PlaylistSpider
import SWR3PlaylistSpider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.reactor import install_reactor
from settings import SETTINGS

def run():
    install_reactor('twisted.internet.asyncioreactor.AsyncioSelectorReactor')
    process = CrawlerProcess(SETTINGS)
    
    # Set the start and end dates for the playlist retrieval
    start_date = date.today().strftime("%Y-%m-%d")
    end_date = None
    
    process.crawl(SWR3PlaylistSpider.SWR3PlaylistSpider, start_date_param=start_date, end_date_param=end_date)
    process.crawl(SRF3PlaylistSpider.SRF3PlaylistSpider, start_date_param=start_date, end_date_param=end_date)
    process.start()

if __name__ == '__main__':
    run()