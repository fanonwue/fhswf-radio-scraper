from datetime import date, datetime
import SRF3PlaylistSpider
import SWR3PlaylistSpider
import SWR3LandingPage
import SRF3LandingPage
from scrapy.crawler import CrawlerProcess
from scrapy.utils.reactor import install_reactor
from settings import SETTINGS

def run():
    install_reactor('twisted.internet.asyncioreactor.AsyncioSelectorReactor')
    process = CrawlerProcess(SETTINGS)
    
    # Set the start and end dates for the playlist retrieval
    # @To-Do: Download once a day, for the previous day.
    start_date = date.today().strftime("%Y-%m-%d")
    end_date = None
    process.crawl(SWR3PlaylistSpider.SWR3PlaylistSpider, start_date_param=start_date, end_date_param=end_date)
    process.crawl(SRF3PlaylistSpider.SRF3PlaylistSpider, start_date_param=start_date, end_date_param=end_date)
    
    # @To-Do: Now: E.g. download hourly to collect the current host, headlines etc.
    process.crawl(SWR3LandingPage.SWR3LandingPage)
    process.crawl(SRF3LandingPage.SRF3LandingPage)

    process.start()

if __name__ == '__main__':
    run()