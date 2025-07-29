from DownloadSpider import DownloadSpider
import scrapy
import re
import os
import json
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from settings import DATA_PATH

class NRWLokalradiosSpider(DownloadSpider):
    name = "NRWLokalradios"
    # run daily
    interval = 60 * 60 * 24
    compress = True

    custom_settings = {
        'DOWNLOAD_DELAY': 5, # Wenn der Delay zu kurz ist, wird der Aufruf mit einem 500-Fehler abgelehnt!
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }

    def start_requests(self):
        start_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        url = f"https://api-prod.nrwlokalradios.com/playlist/title?station=28&req_station=28&searchterm=&datefrom={start_date}%2000:00:00&dateto={start_date}%2023:59:59&pagesize=1000"
        yield scrapy.Request(url)

    def parse(self, response, **kwargs):
        super().save_response(response)

        playlist_data = []

        json_response = json.loads(response.text)

        if not json_response:
            self.logger.warning(f"No playlist items found on {response.url}")

        for item in json_response:
            playlist_data.append({
                'datetime': item['timeslot_iso'],
                'title': item['title'],
                'performer': item['artist']
            })

        json_filename = self.generate_name(response, extension = ".json").replace(".html", ".json")
        path = os.path.join(DATA_PATH, self.name, 'parsed', json_filename)

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(playlist_data, f, ensure_ascii=False, indent=4)
            self.logger.info(f"Wrote {len(playlist_data)} entries to {path}")
        except IOError as e:
            self.logger.error(f"Could not write JSON to {path}: {e}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred while writing JSON to {path}: {e}")

        return {"url": response.url}