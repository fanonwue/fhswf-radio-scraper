import mimetypes
import os.path
import gzip
from os import PathLike
from datetime import datetime, timezone
import scrapy
from scrapy.http.response import Response
from settings import DATA_PATH
from pathlib import Path


class DownloadSpider(scrapy.Spider):
    name = ""
    interval = None
    compress = False

    def generate_name(self, response: Response, extension = ".html") -> str:
        time = datetime.now(timezone.utc).isoformat(timespec="seconds")
        type_raw = response.headers.get("Content-Type")
        if type_raw is not None:
            type = type_raw.decode("utf-8").split(";")[0]
            extension = mimetypes.guess_extension(type, False)
        return f"{self.name}_{time}{extension}"

    def save_response(self, response: Response, path: PathLike | None = None, **kwargs):
        if not self.name:
            raise Exception(
                "The spider must have a valid name attribute. Please add name to the class."
            )

        if path is None:
            path = Path(self.generate_name(response))

        directory = os.path.join(DATA_PATH, self.name).__str__()
        parsed_directory = os.path.join(directory, 'parsed').__str__()
        Path(parsed_directory).mkdir(parents=True, exist_ok=True)

        if self.compress:
            with gzip.open(os.path.join(directory, path) + ".gz", "wb") as f:
                f.write(response.body)
        else:
            with open(os.path.join(directory, path), "wb") as f:
                f.write(response.body)
