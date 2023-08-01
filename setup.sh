#!/usr/bin/env bash

pip install poetry
poetry install
poetry run playwright install
docker compose run -d

echo "BeeBot is now set up"