import scrapy
from scrapy.http.response.html import HtmlResponse
import json
import os
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import urlencode

from DownloadSpider import DownloadSpider
from settings import DATA_PATH

"""
SWR1RpPlaylistSpider ist ein Scrapy-Spider, der die Playlist-Daten von SWR1-Rp abruft.

Es geht nicht unendlich weit in die Vergangenheit zurück!
Stand 14.05.2025 ist die Abfrage bis zum 14.04.2025 möglich.
"""
class SWR1RpPlaylistSpider(DownloadSpider):
    name = "swr1_rp_playlist"
    # run daily
    interval = 60 * 60 * 24
    compress = True

    custom_settings = {
        'DOWNLOAD_DELAY': 5, # Wenn der Delay zu kurz ist, wird der Aufruf mit einem 500-Fehler abgelehnt!
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }

    def __init__(self, start_date_param=None, end_date_param=None, *args, **kwargs):
        """
        Initialisiert den Spider. Verarbeitet die übergebenen Start- und Enddaten
        (`start_date_param`, `end_date_param`), um den Datumsbereich für den Abruf
        festzulegen. Stellt Standardwerte bereit, wenn keine Daten angegeben werden.
        Erstellt das Datenverzeichnis (`DATA_PATH`), falls es nicht existiert.

        Parameter:
            start_date_param (str, optional): Das Startdatum für den Abruf im Format `YYYY-MM-DD`.
                                            Wenn `None`, wird das heutige Datum verwendet.
            end_date_param (str, optional): Das Enddatum für den Abruf im Format `YYYY-MM-DD`.
                                          Wenn `None` und `start_date_param` in der Vergangenheit
                                          liegt, wird das heutige Datum verwendet; andernfalls
                                          wird `start_date_param` als Enddatum verwendet.
            *args: Variable Argumentenliste, die an die Superklasse `DownloadSpider` weitergegeben wird.
            **kwargs: Variable Keyword-Argumentenliste, die an die Superklasse `DownloadSpider`
                      weitergegeben wird.

        Löst aus:
            ValueError: Wenn `start_date_param` oder `end_date_param` ein ungültiges Format haben.
        """
        super().__init__(*args, **kwargs)
        self.today = date.today()
        
        if start_date_param:
            try:
                self.start_date = datetime.strptime(start_date_param, "%Y-%m-%d").date()
            except ValueError:
                self.logger.error(f"Ungültiges start_date_param Format ('{start_date_param}'). Muss YYYY-MM-DD sein.")
                raise ValueError("start_date_param Format muss YYYY-MM-DD sein.")
        else:
            self.start_date = self.today
            self.logger.info(f"Kein start_date_param angegeben. Verwende aktuelles Datum als Startdatum: {self.start_date}")
        
        if end_date_param:
            try:
                self.end_date = datetime.strptime(end_date_param, "%Y-%m-%d").date()
            except ValueError:
                self.logger.error(f"Ungültiges end_date_param Format ('{end_date_param}'). Muss YYYY-MM-DD sein.")
                raise ValueError("end_date_param Format muss YYYY-MM-DD sein.")
        elif self.start_date < self.today and end_date_param is None:
            self.end_date = self.today
            self.logger.info(f"Kein end_date_param angegeben. Verwende aktuelles Datum als Enddatum: {self.end_date}")
        else:
            self.end_date = self.start_date 
            self.logger.info(f"Kein end_date_param angegeben. Verwende Startdatum ({self.start_date}) als Enddatum.")

        if DATA_PATH:
            os.makedirs(DATA_PATH, exist_ok=True)

        self.logger.info(f"SWR1RpPlaylistSpider initialisiert für Datumsbereich: {self.start_date} bis {self.end_date}")

    def start_requests(self):
        """
        Generiert die initialen Anfragen (Requests) für jede Stunde innerhalb des
        festgelegten Datumsbereichs. Für jedes Datum und jede Stunde wird eine
        Anfrage an die SWR1-RP-Playlist-Seite gesendet. Die Methode berücksichtigt,
        ob das Datum in der Vergangenheit, Gegenwart oder Zukunft liegt, um die
        relevanten Stunden für den Abruf zu bestimmen.

        Parameter:
            Keine.

        Gibt zurück:
            scrapy.Request: Ein `scrapy.Request` Objekt für jede zu verarbeitende Stunde,
                            das die URL der Playlist-Seite, den Callback `self.parse_playlist_page`
                            und Metadaten (Datum und Zeit der Playlist) enthält.
        """
        headers = {}
        user_agent = self.settings.get('USER_AGENT')
        if user_agent:
            headers['User-Agent'] = user_agent

        all_possible_time_options = [f"{h:02d}:00" for h in range(24)]
        base_url = "https://www.swr.de/swr1/rp/programm/musikrecherche-swr1-rp-detail-100.html"
        
        current_processing_date = self.start_date
        while current_processing_date <= self.end_date:
            date_value_str_for_request = current_processing_date.strftime("%Y-%m-%d")
            time_options_for_this_date = []

            if current_processing_date == self.today:
                now_berlin = datetime.now(ZoneInfo("Europe/Berlin"))
                current_hour_berlin = now_berlin.hour
                
                if current_processing_date == self.start_date:
                    time_options_for_this_date.append("00:00")

                for time_opt in all_possible_time_options:
                    if current_processing_date == self.start_date and time_opt == "00:00":
                        continue

                    try:
                        option_hour = int(time_opt.split(":")[0])
                        if option_hour < current_hour_berlin:
                            if time_opt not in time_options_for_this_date:
                                time_options_for_this_date.append(time_opt)
                    except ValueError:
                        self.logger.warning(f"Konnte Stunde nicht aus generierter Zeitoption parsen: {time_opt}. Überspringe.")
                
                if not time_options_for_this_date:
                    self.logger.info(f"Für heute ({date_value_str_for_request}), aktuelle Stunde ist {current_hour_berlin}. "
                                     f"Keine (weiteren) vergangenen Zeitfenster für heute zu verarbeiten.")
            
            elif current_processing_date < self.today:
                time_options_for_this_date = all_possible_time_options
                self.logger.info(f"Verarbeite vergangenes Datum ({date_value_str_for_request}). "
                                 f"Versuche alle {len(all_possible_time_options)} Zeitoptionen.")
            
            elif current_processing_date > self.today:
                time_options_for_this_date = all_possible_time_options
                self.logger.info(f"Verarbeite zukünftiges Datum ({date_value_str_for_request}). "
                                 f"Versuche alle {len(all_possible_time_options)} Zeitoptionen (Daten sind möglicherweise nicht verfügbar).")
            
            if time_options_for_this_date:
                self.logger.info(f"Für Datum {date_value_str_for_request}, verarbeite Zeiten: {time_options_for_this_date}")
                for time_value in time_options_for_this_date:
                    params = {
                        'swx_date': date_value_str_for_request,
                        'swx_time': time_value
                    }
                    playlist_url = f"{base_url}?{urlencode(params)}"
                    
                    self.logger.info(f"Fordere Playlist an für Datum {date_value_str_for_request}, Zeit {time_value} unter {playlist_url}")
                    
                    yield scrapy.Request(
                        playlist_url, 
                        callback=self.parse_playlist_page,
                        headers=headers,
                        meta={'playlist_date': date_value_str_for_request, 'playlist_time': time_value}
                    )
            else:
                self.logger.info(f"Keine Zeitoptionen für Datum {date_value_str_for_request} zu verarbeiten.")
            
            current_processing_date += timedelta(days=1)

    def parse_playlist_page(self, response: HtmlResponse):
        """
        Verarbeitet die Antwort (Response) einer Playlist-Seite für eine spezifische Stunde.
        Speichert zuerst die rohe HTML-Antwort. Extrahiert dann Song-Informationen
        (Zeitstempel, Titel, Interpret) aus der HTML-Struktur. Die extrahierten
        Song-Daten werden in einer JSON-Datei gespeichert, deren Name das Datum
        und die Stunde der Playlist enthält.

        Parameter:
            response (HtmlResponse): Das von Scrapy empfangene Antwortobjekt, das den
                                     HTML-Inhalt der Playlist-Seite für eine bestimmte
                                     Stunde enthält.

        Meta-Parameter (aus `response.meta`):
            playlist_date (str): Das Datum der Playlist (im Format `YYYY-MM-DD`).
            playlist_time (str): Die Startzeit der Playlist-Stunde (im Format `HH:MM`).
        """
        playlist_date = response.meta.get('playlist_date', 'unknown_date')
        playlist_time_for_filename = response.meta.get('playlist_time', 'unknown_time').replace(":", "-")

        self.logger.info(f"Parsing playlist page for {playlist_date} {playlist_time_for_filename}: {response.url}")
        
        super().save_response(response, prefix=f"{playlist_date}_{playlist_time_for_filename}_")

        # Playlist in JSON extraktieren.
        items = response.css('ul.list-group.list-playlist li.list-group-item')
        playlist_data = []
        
        if not items:
            self.logger.warning(f"No playlist items found on {response.url}")

        for item in items:
            time_attr = item.css('time::attr(datetime)').get()
            if not time_attr:
                self.logger.warning(f"Missing time attribute in item on {response.url}")
                continue
            
            iso_ts = None
            try:
                dt = datetime.fromisoformat(time_attr)
                dt_berlin = dt.astimezone(ZoneInfo("Europe/Berlin")) if dt.tzinfo else dt.replace(tzinfo=ZoneInfo("Europe/Berlin"))
                iso_ts = dt_berlin.isoformat(timespec="minutes")
            except ValueError as e:
                self.logger.error(f"Error parsing datetime string '{time_attr}': {e}. Using raw value.")
                iso_ts = time_attr

            title = item.css('dd.playlist-item-song::text').get()
            performer = item.css('dd.playlist-item-artist::text').get()

            playlist_data.append({
                'datetime': iso_ts,
                'title': title.strip() if title else None,
                'performer': performer.strip() if performer else None
            })

        json_filename = f"{SWR1RpPlaylistSpider.name}_{playlist_date}_{playlist_time_for_filename}.json"
        path = os.path.join(DATA_PATH, self.name, 'parsed', json_filename)
        
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(playlist_data, f, ensure_ascii=False, indent=4)
            self.logger.info(f"Wrote {len(playlist_data)} entries to {path}")
        except IOError as e:
            self.logger.error(f"Could not write JSON to {path}: {e}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred while writing JSON to {path}: {e}")