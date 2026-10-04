#!/usr/bin/env bash
python telegram_bot.py &
gunicorn --timeout 120 server:app