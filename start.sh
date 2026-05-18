#!/bin/sh
set -eu

exec gunicorn app:app --bind "0.0.0.0:${PORT:-5000}" --preload --timeout 120 --keep-alive 5 --log-level info
