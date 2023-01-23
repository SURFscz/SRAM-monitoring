#!/bin/sh
docker run --rm -d --name chrome -p 4444:4444 selenium/standalone-chrome
while ! curl --output /dev/null --silent --head http://localhost:4444/wd/hub; do
  echo -n "."
  sleep 1 # wait for 1/10 of the second before check again
done
echo; echo "Up!"
./sram_monitoring_test.py config.yml
docker stop chrome
echo "Down"
