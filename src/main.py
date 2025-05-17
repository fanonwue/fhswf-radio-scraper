import json
from datetime import datetime, timezone, timedelta

from scrapy.crawler import CrawlerProcess
from scrapy.utils.reactor import install_reactor
from OffizielleChartsSpider import OffizielleChartsSpider
from DLFNovaSpider import DLFNovaSpider
from settings import SETTINGS
import os.path


def run():
    update_last_runs_list = []
    last_run_list = get_last_runs()

    install_reactor("twisted.internet.asyncioreactor.AsyncioSelectorReactor")
    process = CrawlerProcess(SETTINGS)

    spiders_to_run = []
    spiders_to_run.append(OffizielleChartsSpider)
    spiders_to_run.append(DLFNovaSpider)

    for spider_to_run in spiders_to_run:
        if spider_can_run(last_run_list, spider_to_run.name, spider_to_run.interval):
            process.crawl(spider_to_run)
            update_last_runs_list.append(spider_to_run.name)
        else:
            print(f"Skipping spider {spider_to_run.name}, interval not reached.")

    process.start()
    update_last_runs(update_last_runs_list)


def get_last_runs() -> dict:
    if not os.path.isfile("last_runs.json"):
        return {}
    else:
        with open("last_runs.json", "r") as f:
            try:
                return json.load(f)
            except Exception:
                return {}


def update_last_runs(last_runs_list: list):
    time = datetime.now(timezone.utc).timestamp()
    last_runs = get_last_runs()
    for last_run in last_runs_list:
        last_runs[last_run] = time
    with open("last_runs.json", "w") as f:
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
