import mimetypes
import os.path
from os import PathLike
from datetime import datetime, timezone
import scrapy
from scrapy.http import Response
from settings import DATA_PATH


class DownloadSpider(scrapy.Spider):
    def generate_name(self, response: Response) -> str:
        time = datetime.now(timezone.utc).isoformat(timespec="seconds")
        type_raw = response.headers.get("Content-Type")
        extension = ".html"
        if type_raw is not None:
            type = type_raw.decode("utf-8").split(';')[0]
            extension = mimetypes.guess_extension(type, False)
        return f"{self.name}_{time}{extension}"

    def save_response(self, response: Response, path: PathLike|None = None, **kwargs):
        if path is None:
            path = self.generate_name(response)

        with open(os.path.join(DATA_PATH, path), "wb") as f:
            f.write(response.body)
