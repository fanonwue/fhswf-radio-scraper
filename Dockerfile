FROM mcr.microsoft.com/playwright/python:v1.54.0-noble

ARG TZ=Europe/Berlin

COPY src/ /opt/scraper/src/
COPY requirements.txt /opt/scraper/

WORKDIR /opt/scraper/

RUN pip install -r requirements.txt

RUN playwright install --with-deps chromium
