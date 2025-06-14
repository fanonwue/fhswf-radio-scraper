from datetime import date, datetime, timedelta
import SRF3PlaylistSpider
import SWR1RpPlaylistSpider
import SWR3PlaylistSpider
import SWR1RpLandingPage
import SWR3LandingPage
import SRF3LandingPage
from scrapy.crawler import CrawlerProcess
from scrapy.utils.reactor import install_reactor
from settings import SETTINGS

def run():
    install_reactor('twisted.internet.asyncioreactor.AsyncioSelectorReactor')
    process = CrawlerProcess(SETTINGS)
    
    # Set the start and end dates for the playlist retrieval
    # TODO: Download once a day, for the previous day. eg. cron every day at 01:00
    start_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = start_date
    process.crawl(SWR1RpPlaylistSpider.SWR1RpPlaylistSpider, start_date_param=start_date, end_date_param=end_date)
    #process.crawl(SWR3PlaylistSpider.SWR3PlaylistSpider, start_date_param=start_date, end_date_param=end_date)
    #process.crawl(SRF3PlaylistSpider.SRF3PlaylistSpider, start_date_param=start_date, end_date_param=end_date)
    
    # TODO: Now: E.g. download hourly to collect the current host, headlines etc.
    process.crawl(SWR1RpLandingPage.SWR1RpLandingPage)
    process.crawl(SWR3LandingPage.SWR3LandingPage)
    process.crawl(SRF3LandingPage.SRF3LandingPage)

    process.start()

if __name__ == '__main__':
    run()