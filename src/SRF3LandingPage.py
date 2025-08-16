import scrapy
import DownloadSpider # Importiere die Basisklasse
import json
from datetime import datetime
import os
from settings import DATA_PATH
from scrapy_playwright.page import PageMethod

class SRF3LandingPage(DownloadSpider.DownloadSpider):
    """
    Spider zum Scrapen von Daten (Moderator, Schlagzeilen) von der SRF 3-Startseite.
    Nutzt Playwright für dynamische Interaktionen auf der Seite.
    """
    name = "srf3_landing_page"
    # run hourly
    interval = 60 * 60
    compress = True

    def start_requests(self):
        """
        Initiiert die Anfrage an die SRF 3-Webseite.
        Verwendet Playwright, um auf das Laden des Moderators und der Schlagzeilen zu warten,
        bevor die Seite geparst wird.
        """
        yield scrapy.Request(
            "https://www.srf.ch/radio-srf-3",
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_selector", 'div.radio-content-header__slot--third .radio-content-header-teaser__title', timeout=15000),
                    PageMethod("wait_for_selector", 'span.teaser__title', timeout=15000)
                ]
            }
        )

    def parse(self, response, **kwargs):
        """
        Parst die Antwort der SRF 3-Webseite.
        Extrahiert den aktuellen Moderator und die Schlagzeilen.
        Speichert die extrahierten Daten zusammen mit einem Zeitstempel in einer JSON-Datei.
        """
        super().save_response(response)

        # Presenter extrahieren
        presenter = response.css('div.radio-content-header__slot--third .radio-content-header-teaser__title::text').get()
        presenter = presenter.strip() if presenter else None

        # Headlines extrahieren
        headlines_elements = response.css('span.teaser__title::text').getall()
        headlines = [h.strip() for h in headlines_elements if h.strip()]


        # JSON speichern
        data = {
            "presenter": presenter,
            "headlines": headlines,
            "timestamp": datetime.now().isoformat()
        }
        ts = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        fname = f"{SRF3LandingPage.name}_{ts}.json"
        outdir = os.path.join(DATA_PATH, self.name, 'parsed', fname)
        with open(outdir, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return data