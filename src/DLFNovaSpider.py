from DownloadSpider import DownloadSpider
import scrapy
import re
import os
import json
from datetime import date, datetime, time
from zoneinfo import ZoneInfo
from settings import DATA_PATH

class DLFNovaSpider(DownloadSpider):
    name = "DLFNova"
    # run daily
    interval = 60 * 60 * 24
    compress = True

    custom_settings = {
        'DOWNLOAD_DELAY': 5, # Wenn der Delay zu kurz ist, wird der Aufruf mit einem 500-Fehler abgelehnt!
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }

    def start_requests(self):
        yield scrapy.Request("https://www.deutschlandfunknova.de/playlist")

    def parse(self, response, **kwargs):
        super().save_response(response)
        # 'response' contains the page as seen by the browser

        playlist_data = []

        playlist_items = response.css('ul.playlist.day1 li.item figure figcaption')

        if not playlist_items:
            self.logger.warning(f"No playlist items found on {response.url}")

        for item in playlist_items:
            date_time = item.css('small::text').get()
            if not date_time:
                self.logger.warning(f"Missing time attribute in item on {response.url}")
                continue

            matches = re.search("((\\d+)\\. ([a-zA-Z]+))[\\s]*\\|[\\s]*((\\d+):(\\d+))", date_time)
            if not matches:
                self.logger.warning(f"Missing time attribute in item on {response.url}")
                continue

            day = int(matches[2])
            hour = int(matches[5])
            minute = int(matches[6])
            month = 0
            # I am sorry but this is the easiert way without adding any more dependencies...
            match matches[3]:
                case "Januar":
                    month = 1
                case "Februar":
                    month = 2
                case "März":
                    month = 3
                case "April":
                    month = 4
                case "Mai":
                    month = 5
                case "Juni":
                    month = 6
                case "Juli":
                    month = 7
                case "August":
                    month = 8
                case "September":
                    month = 9
                case "Oktober":
                    month = 10
                case "November":
                    month = 11
                case "Dezember":
                    month = 12
                case _:
                    self.logger.warning(f"Missing time attribute in item on {response.url}")
                    continue
            
            try:
                dt = datetime(2025, month, day, hour, minute, tzinfo=ZoneInfo("Europe/Berlin"))
                iso_ts = dt.isoformat(timespec="minutes")
            except ValueError as e:
                self.logger.error(f"Error parsing datetime string '{date_time}': {e}. Using raw value.")
                iso_ts = date_time

            title = item.css('h3 div.title::text').get()
            performer = item.css('h3 div.artist::text').get()

            playlist_data.append({
                'datetime': iso_ts,
                'title': title.strip() if title else None,
                'performer': performer.strip() if performer else None
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
