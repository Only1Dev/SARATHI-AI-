#!/usr/bin/env bash
python telegram_bot.py &
gunicorn --bind 0.0.0.0:${PORT:-5000} --timeout 120 server:app
