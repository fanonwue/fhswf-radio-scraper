import scrapy
from scrapy.http.response.html import HtmlResponse
import json
import os
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from scrapy_playwright.page import PageMethod

from DownloadSpider import DownloadSpider
from settings import DATA_PATH

"""
SRF3PlaylistSpider ist ein Scrapy-Spider, der die Playlist-Daten von SRF3 abruft.
Es geht nicht unendlich weit in die Vergangenheit zurück!
Stand 14.05.2025 ist die Abfrage bis zum 30.04.2025 möglich.
"""
class SRF3PlaylistSpider(DownloadSpider):
    name = "srf3_playlist"
    # run daily
    interval = 60 * 60 * 24
    compress = True

    def __init__(self, start_date_param=None, end_date_param=None, *args, **kwargs):
        """
        Initialisiert den Spider. Verarbeitet die übergebenen Start- und Enddaten,
        um eine Liste von Daten zu erstellen, für die Playlists abgerufen werden sollen.
        Erstellt das Datenverzeichnis, falls es nicht existiert.

        Parameter:
            start_date_param (str, optional): Das Startdatum für den Abruf im Format `YYYY-MM-DD`.
                                        Wenn `None`, wird das heutige Datum verwendet.
            end_date_param (str, optional): Das Enddatum für den Abruf im Format `YYYY-MM-DD`.
                                      Wenn `None`, wird das heutige Datum verwendet.
            *args: Variable Argumentenliste, die an die Superklasse `DownloadSpider` weitergegeben wird.
            **kwargs: Variable Keyword-Argumentenliste, die an die Superklasse `DownloadSpider`
                      weitergegeben wird.

        Löst aus:
            ValueError: Wenn `start_date_param` oder `end_date_param` ein ungültiges Format haben oder
                        wenn `end_date_param` vor `start_date_param` liegt.
        """
        super().__init__(*args, **kwargs)

        today = datetime.now(ZoneInfo("Europe/Zurich")).date()

        if start_date_param:
            try:
                start = datetime.strptime(start_date_param, "%Y-%m-%d").date()
                print(f"Startdatum: {start}")
            except ValueError:
                raise ValueError(f"Ungültiges start_date-Format: {start_date_param}, muss YYYY-MM-DD sein.")
        else:
            start = today

        if end_date_param:
            try:
                end = datetime.strptime(end_date_param, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f"Ungültiges end_date-Format: {end_date_param}, muss YYYY-MM-DD sein.")
        else:
            end = today

        if end < start:
            raise ValueError(f"end_date ({end}) darf nicht vor start_date ({start}) liegen.")

        delta_days = (end - start).days
        self.date_list = [start + timedelta(days=i) for i in range(delta_days + 1)]

        if DATA_PATH:
            os.makedirs(DATA_PATH, exist_ok=True)

    def start_requests(self):
        """
        Generiert die initialen Anfragen (Requests) für jede zu verarbeitende Datum.
        Für jedes Datum wird eine Anfrage an die SRF3-Musik-Playlist-Seite gesendet.
        Playwright wird verwendet, um mit der Webseite zu interagieren (Datum auswählen,
        auf das Laden der Inhalte warten).

        Parameter:
            Keine.

        Gibt zurück:
            scrapy.Request: Ein `scrapy.Request` Objekt für jedes Datum in `self.date_list`.
        """
        for date_obj in self.date_list:
            filename_date_str = date_obj.strftime("%Y-%m-%d")
            target_date_input_format = date_obj.strftime("%d.%m.%Y")

            playwright_page_methods = [
                PageMethod("wait_for_selector", "div#song-log", state="visible", timeout=15000),
                PageMethod("fill", "input#js-date-picker__input-field", target_date_input_format),
                PageMethod("press", "input#js-date-picker__input-field", "Enter"),
                PageMethod("wait_for_selector", f"h4.landingpage-heading:has-text('{target_date_input_format}')", state="visible", timeout=20000),
                PageMethod("wait_for_selector", "ol.songlog__list", state="visible", timeout=15000),
            ]

            yield scrapy.Request(
                "https://www.srf.ch/radio-srf-3/gespielte-musik",
                callback=self.parse,
                dont_filter=True,
                meta={
                    "playwright": True,
                    "playwright_page_methods": playwright_page_methods,
                    "filename_date_str": filename_date_str,
                }
            )

    def parse(self, response: HtmlResponse, **kwargs):
        """
        Verarbeitet die Antwort (Response) der Webseite. Speichert zuerst die rohe
        HTML-Antwort in einer Datei. Extrahiert dann die Song-Informationen
        (Zeit, Titel, Interpret) aus der HTML-Struktur. Die extrahierten
        Song-Daten werden in einer JSON-Datei gespeichert.

        Parameter:
            response (HtmlResponse): Das von Scrapy empfangene Antwortobjekt, das den
                                     HTML-Inhalt der Seite enthält.
            **kwargs: Zusätzliche Keyword-Argumente, die von Scrapy übergeben werden könnten.

        Meta-Parameter (aus `response.meta`):
            filename_date_str (str): Das Datum (im Format `YYYY-MM-DD`), das dieser
                                     Antwort zugeordnet ist, wird aus den Metadaten
                                     der Anfrage extrahiert.
        """
        filename_date_str = response.meta.get("filename_date_str")

        if DATA_PATH:
            os.makedirs(DATA_PATH, exist_ok=True)
        super().save_response(response)

        html_filename = f"srf3_{filename_date_str}.html"
        html_path = os.path.join(DATA_PATH, html_filename)
    
        try:
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
        except IOError as e:
            self.logger.error(f"Could not write HTML to {html_path}: {e}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred while writing HTML to {html_path}: {e}")

        songs = []
        for entry in response.css('ol.songlog__list li.songlog__entry'):
            time_str = entry.css('.songlog__time::text').get()
            title = entry.css('.songlog__song-title::text').get()
            artist = entry.css('.songlog__artist::text').get()
            if time_str and title and artist:
                songs.append({
                    "time": time_str.strip(),
                    "title": title.strip(),
                    "artist": artist.strip(),
                })

        self.log(f"Extrahierte {len(songs)} Songs für Datum {filename_date_str}.")

        if songs:
            filename = f"{SRF3PlaylistSpider.name}_{filename_date_str}.json"
            filepath = os.path.join(DATA_PATH, self.name, 'parsed', filename)
            try:    
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(songs, f, ensure_ascii=False, indent=4)
                self.log(f"Song-Daten gespeichert in {filepath}")
            except IOError as e:
                self.logger.error(f"Could not write JSON to {filepath}: {e}")
            except Exception as e:
                self.logger.error(f"An unexpected error occurred while writing JSON to {filepath}: {e}")
        else:
            self.log(f"Keine Songs gefunden für {filename_date_str}.")

