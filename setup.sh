#!/usr/bin/env bash

pip install poetry
poetry install
poetry run playwright install

echo "BeeBot is now set up"