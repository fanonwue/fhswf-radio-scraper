# Radio Scraper

Zur Installation am besten ein virtuel environment anlegen. Benötigt wird `scrapy` und `scrapy-playwright`. Die können via
folgendem Befehl installiert werden:

````pip install -r requirements.txt````

Scrapy übernimmt das eigentlich scrapen der Seiten. Dazu am besten die Dokumentation anschauen: https://docs.scrapy.org/en/latest/
Eine einzelne Unit nennt man dabei "Spider". Ich habe die Basisspider `DownloadSpider` erstellt, damit könnt ihr die
rohen HTML-Dateien einfach abspeichern. Siehe dafür die beiden Test Spiders in `TestSpider.py`.

Playwright ist ähnlich wie Selenium. Damit wird ein Browser im Headless-Modus gestartet (standardmäßig Chromium), um dynamische
Webseiten, die kein SSR verwenden, zu scrapen. Es läuft also wie in einem Browser ab. Das ist aber aufwändiger, weswegen
man das nur nutzen sollte, wenn es notwendig ist. In eurem Spider müsst ihr das explizit
über die Meta-Variable `playwright` aktivieren, siehe dazu `TestSpider2`.

Damit euer Spider ausgeführt wird, müsst ihr diesen zum Crawler-Prozess hinzufügen. Siehe dazu die `run()` Funktion in `main.py`.