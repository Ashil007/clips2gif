@echo off
title Video to GIF Web App Server
echo Starting Video to GIF Web Server...
start "" "http://localhost:5000"
python web_server.py
pause
