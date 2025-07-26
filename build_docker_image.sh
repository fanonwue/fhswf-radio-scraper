#!/usr/bin/env bash

# change the working directory into the directory where this script is located
cd "$(dirname "$0")"

docker build -t fhswf/scraper .