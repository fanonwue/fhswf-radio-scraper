import mimetypes
import os.path
from os import PathLike
from datetime import datetime, timezone
import scrapy
from scrapy.http import Response
from settings import DATA_PATH
from pathlib import Path


class DownloadSpider(scrapy.Spider):
    name = None

    def generate_name(self, response: Response) -> str:
        time = datetime.now(timezone.utc).isoformat(timespec="seconds")
        type_raw = response.headers.get("Content-Type")
        extension = ".html"
        if type_raw is not None:
            type = type_raw.decode("utf-8").split(';')[0]
            extension = mimetypes.guess_extension(type, False)
        return f"{self.name}_{time}{extension}"

    def save_response(self, response: Response, path: PathLike|None = None, **kwargs):
        if self.name is None:
            raise Exception("The spider must have a valid name attribute. Please add name to the class.")

        if path is None:
            path = self.generate_name(response)

        directory = os.path.join(DATA_PATH, self.name).__str__()
        Path(directory).mkdir(parents=True, exist_ok=True)

        with open(os.path.join(directory, path), "wb") as f:
            f.write(response.body)
