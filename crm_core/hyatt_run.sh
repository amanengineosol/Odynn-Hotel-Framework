#!/bin/bash

# Start virtual display
Xvfb :99 -screen 0 1280x1024x24 &

# Small wait to ensure Xvfb starts
sleep 2

# Run your app
celery -A crm_core worker -n hyatt_worker -Q Hyatt --loglevel=INFO