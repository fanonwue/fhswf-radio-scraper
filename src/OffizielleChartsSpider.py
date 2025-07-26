from DownloadSpider import DownloadSpider
import scrapy
import re
import os
import datetime
import json
from zoneinfo import ZoneInfo
from settings import DATA_PATH

class OffizielleChartsSpider(DownloadSpider):
    name = "OffizielleCharts"
    # run weekly
    interval = 60 * 60 * 24 * 7
    compress = True

    custom_settings = {
        'DOWNLOAD_DELAY': 5, # Wenn der Delay zu kurz ist, wird der Aufruf mit einem 500-Fehler abgelehnt!
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }

    def start_requests(self):
        yield scrapy.Request("https://www.offiziellecharts.de/charts/single")

    def parse(self, response, **kwargs):
        super().save_response(response)
        # 'response' contains the page as seen by the browser


        chartlist_data = []
        chartlist_date = response.css('span.ch-header').get()
        print(chartlist_date)

        iso_ts_from = None
        iso_ts_to = None

        matches = re.search("<strong>([\\d]+\\.[\\d]+\\.[\\d]+)</strong>[\\s]+-[\\s]+<strong>([\\d]+\\.[\\d]+\\.[\\d]+)</strong>", chartlist_date)
        if not matches:
            self.logger.warning(f"Missing time attribute in item on {response.url}")
        else:
            date_from = datetime.datetime.strptime(matches[1], "%d.%m.%Y").replace(tzinfo=ZoneInfo("Europe/Berlin"))
            date_to = datetime.datetime.strptime(matches[2], "%d.%m.%Y").replace(tzinfo=ZoneInfo("Europe/Berlin"))
            iso_ts_from = date_from.isoformat(timespec="minutes")
            iso_ts_to = date_to.isoformat(timespec="minutes")
            print(iso_ts_from)
            print(iso_ts_to)
        
        chartlist_items = response.css('table.chart-table tr')
        for index, item in enumerate(chartlist_items):
            performer = item.css('td.ch-info span.info-artist::text').get()
            title = item.css('td.ch-info span.info-title::text').get()
            position = item.css('td.ch-pos span.this-week::text').get()
            position_old = item.css('td.ch-trend span.last-week::text').get()
            
            chartlist_data.append({
                'datetime_from': iso_ts_from,
                'datetime_to': iso_ts_to,
                'position': position.strip() if position else index,
                'position_old': position_old.strip() if position_old else None,
                'perfomer': performer.strip() if performer else None,
                'title': title.strip() if title else None,
            })

        json_filename = self.generate_name(response, extension = ".json").replace(".html", ".json")
        path = os.path.join(DATA_PATH, self.name, 'parsed', json_filename)

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(chartlist_data, f, ensure_ascii=False, indent=4)
            self.logger.info(f"Wrote {len(chartlist_data)} entries to {path}")
        except IOError as e:
            self.logger.error(f"Could not write JSON to {path}: {e}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred while writing JSON to {path}: {e}")

        return {"url": response.url}