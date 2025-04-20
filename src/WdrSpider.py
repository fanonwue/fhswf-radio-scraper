import scrapy
from scrapy.http.response.html import HtmlResponse
import json
import os
import mimetypes
from datetime import datetime, timezone

import DownloadSpider
from settings import DATA_PATH


class WdrSpider(DownloadSpider.DownloadSpider):

    def parse_wdr_time(self, time_str: str) -> str:
        # Convert the time string to a datetime object
        dt = datetime.strptime(time_str, r"%d.%m.%Y,%H.%M Uhr")
        # Convert to UTC timezone
        dt_utc = dt.replace(tzinfo=timezone.utc)
        # Format the datetime object as a string in ISO 8601 format
        return dt_utc.isoformat(timespec="seconds")

    def parse(self, response: HtmlResponse, **kwargs):
        super().save_response(response)
        

        playlistTable = response.css('#searchPlaylistResult')
        # Extract rows from the playlist table
        rows = playlistTable.css('tr.data')[1:] # discard the first row, which is a header

        # Initialize an empty list to store the extracted data
        playlist_data = []

        # Iterate over each row and extract the relevant data
        for row in rows:
            date_time = row.css('th.entry.datetime::text').getall()
            date_time = ''.join(date_time).strip().replace('\n', '').replace('<br>', ' ')
            date_time = self.parse_wdr_time(date_time)

            title = row.css('td.entry.title::text').get().strip()
            performer = row.css('td.entry.performer::text').get().strip()

            # Append the extracted data as a dictionary
            playlist_data.append({
            'datetime': date_time,
            'title': title,
            'performer': performer
            })

        json_path = self.generate_name(response) + '.json'
        with open(os.path.join(DATA_PATH, json_path), "wb") as f:
            f.write(json.dumps(playlist_data, indent=4).encode('utf-8'))


class Wdr2Spider(WdrSpider):
    name = "wdr2"

    def start_requests(self):
        # GET request
        yield scrapy.Request("https://www1.wdr.de/radio/wdr2/musik/playlist/index.jsp")

class Wdr1Spider(WdrSpider):
    name = "1live"

    def start_requests(self):
        # GET request
        yield scrapy.Request("https://www1.wdr.de/radio/1live/musik/playlist/index.jsp")