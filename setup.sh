#!/usr/bin/env bash

pip install poetry
poetry install
poetry run playwright install
docker compose up -d

echo "BeeBot is now set up"