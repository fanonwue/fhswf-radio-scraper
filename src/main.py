import json
from datetime import date, datetime, timezone, timedelta
import SRF3PlaylistSpider
import SWR1RpPlaylistSpider
import SWR3PlaylistSpider
import SWR1RpLandingPage
import SWR3LandingPage
import SRF3LandingPage
import WdrSpider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.reactor import install_reactor
from OffizielleChartsSpider import OffizielleChartsSpider
from DLFNovaSpider import DLFNovaSpider
from NRWLokalradiosSpider import NRWLokalradiosSpider
from settings import SETTINGS
import os.path


def run():
    update_last_runs_list = []
    last_run_list = get_last_runs()

    install_reactor("twisted.internet.asyncioreactor.AsyncioSelectorReactor")
    process = CrawlerProcess(SETTINGS)
    
    # Set the start and end dates for the playlist retrieval
    # TODO: Download once a day, for the previous day. eg. cron every day at 01:00
    start_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = start_date
    # process.crawl(SWR1RpPlaylistSpider.SWR1RpPlaylistSpider, start_date_param=start_date, end_date_param=end_date)
    #process.crawl(SWR3PlaylistSpider.SWR3PlaylistSpider, start_date_param=start_date, end_date_param=end_date)
    #process.crawl(SRF3PlaylistSpider.SRF3PlaylistSpider, start_date_param=start_date, end_date_param=end_date)

    spiders_to_run = []
    spiders_to_run.append({'spider': SWR1RpPlaylistSpider.SWR1RpPlaylistSpider, 'args': {'start_date_param': start_date, 'end_date_param': end_date}})
    spiders_to_run.append({'spider': SWR3PlaylistSpider.SWR3PlaylistSpider, 'args': {'start_date_param': start_date, 'end_date_param': end_date}})
    spiders_to_run.append({'spider': SRF3PlaylistSpider.SRF3PlaylistSpider, 'args': {'start_date_param': start_date, 'end_date_param': end_date}})
    spiders_to_run.append({'spider': SWR1RpLandingPage.SWR1RpLandingPage, 'args': {}})
    spiders_to_run.append({'spider': SWR3LandingPage.SWR3LandingPage, 'args': {}})
    spiders_to_run.append({'spider': SRF3LandingPage.SRF3LandingPage, 'args': {}})
    spiders_to_run.append({'spider': OffizielleChartsSpider, 'args': {}})
    spiders_to_run.append({'spider': DLFNovaSpider, 'args': {}})
    spiders_to_run.append({'spider': WdrSpider.Wdr1Spider, 'args': {}})
    spiders_to_run.append({'spider': WdrSpider.Wdr2Spider, 'args': {}})
    spiders_to_run.append({'spider': NRWLokalradiosSpider, 'args': {}})

    for spider_to_run in spiders_to_run:
        if spider_can_run(last_run_list, spider_to_run['spider'].name, spider_to_run['spider'].interval):
            try:
                process.crawl(spider_to_run['spider'], **spider_to_run['args'])
                update_last_runs_list.append(spider_to_run['spider'].name)
            except Exception as e:
                print(f"Error when running spider {spider_to_run['spider'].name}!")
                print(str(e))
        else:
            print(f"Skipping spider {spider_to_run['spider'].name}, interval not reached.")

    try:
        process.start()
    except Exception as e:
        print(f"Error while running scrapy!")
        print(str(e))
    update_last_runs(update_last_runs_list)


def get_last_runs() -> dict:
    if not os.path.isfile("data/last_runs.json"):
        return {}
    else:
        with open("data/last_runs.json", "r") as f:
            try:
                return json.load(f)
            except Exception:
                return {}


def update_last_runs(last_runs_list: list):
    time = datetime.now(timezone.utc).timestamp()
    last_runs = get_last_runs()
    for last_run in last_runs_list:
        last_runs[last_run] = time
    with open("data/last_runs.json", "w") as f:
        json.dump(last_runs, f)


def spider_can_run(last_run_list: dict, spider_name: str, interval: int) -> bool:
    current_time = datetime.now(timezone.utc)
    delta = timedelta(seconds=interval)
    try:
        spider_last_run_time = last_run_list[spider_name]
    except KeyError:
        return True

    spider_last_run_time_parsed = datetime.fromtimestamp(
        spider_last_run_time, timezone.utc
    )
    return spider_last_run_time_parsed + delta < current_time


if __name__ == "__main__":
    run()
