#!/usr/bin/env bash

# change the working directory into the directory where this script is located
cd "$(dirname "$0")"

docker run --rm --ipc=host --user 1000 --init --security-opt seccomp=seccomp_profile.json --volume ./data:/opt/scraper/data fhswf/scraper python src/main.py