#!/bin/bash
# Start lightweight HTTP server in background
cd /var/www/solax && python -m http.server 8080 &

# Run main Python script
python /app/solaxmonitor.py