#!/bin/bash

DAEMON_PATH="/home/pi/METEO/"

cd $DAEMON_PATH
python storage.py &
runuser -l pi -c '/home/pi/METEO/meteo.py &'
python wdt.py 0 30 127.0.0.1 1883 &
