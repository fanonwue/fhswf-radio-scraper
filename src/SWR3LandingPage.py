import scrapy
import DownloadSpider # Importiere die Basisklasse
import json
from datetime import datetime
import os
from settings import DATA_PATH
from scrapy_playwright.page import PageMethod

class SWR3LandingPage(DownloadSpider.DownloadSpider):
    """
    Spider zum Scrapen von Daten (Moderator, Schlagzeilen) von der SWR3-Startseite.
    Nutzt Playwright für dynamische Interaktionen auf der Seite.
    """
    name = "swr3_landing_page"
    # run hourly
    interval = 60 * 60
    compress = True

    def start_requests(self):
        """
        Initiiert die Anfrage an die SWR3-Webseite.
        Verwendet Playwright, um auf den Tab "Sendung" zu klicken und auf das Laden des Moderators zu warten,
        bevor die Seite geparst wird.
        """

        yield scrapy.Request(
            "https://www.swr3.de/",
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_selector", selector="#broadcast-tab", state="visible"),
                    PageMethod("evaluate", expression="window.scrollTo(0, 0)"),
                    PageMethod("click", selector="#broadcast-tab"),
                    PageMethod("wait_for_function",
                               expression="""
                                   () => {
                                       const el = document.querySelector('#currentshow .presenter a');
                                       return el && el.textContent && el.textContent.trim().length > 0;
                                   }
                               """,
                               timeout=2000
                    ),
                ]
            }
        )

    def parse(self, response, **kwargs):
        """
        Parst die Antwort der SWR3-Webseite.
        Extrahiert den aktuellen Moderator und die Schlagzeilen.
        Speichert die extrahierten Daten zusammen mit einem Zeitstempel in einer JSON-Datei.
        """
        super().save_response(response)

        # Presenter extrahieren
        presenter = response.css('#currentshow .presenter a::text').get()
        presenter = presenter.strip() if presenter else None

        # Headlines extrahieren
        headlines = response.css('span.headline::text').getall()
        headlines = [h.strip() for h in headlines if h.strip()]

        # Optional: Fallback, falls headline in h2.hgroup > a > span.headline
        if not headlines:
            headlines = response.css('h2.hgroup span.headline::text').getall()
            headlines = [h.strip() for h in headlines if h.strip()]

        # JSON speichern
        data = {
            "presenter": presenter,
            "headlines": headlines,
            "timestamp": datetime.now().isoformat()
        }
        ts = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        fname = f"{SWR3LandingPage.name}_{ts}.json"
        outdir = os.path.join(DATA_PATH, self.name, 'parsed', fname)
        with open(outdir, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return data