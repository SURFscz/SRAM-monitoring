#!/bin/sh
if [ -z $1 ]; then
  echo "Environment not set"
  exit 1
fi

ENV=$1
if [ ! -f ${ENV}.yml ]; then
  echo "Environment config not available"
  exit 1
fi

docker run --rm -d --name chrome -p 4444:4444 selenium/standalone-chrome >/dev/null 2>&1
while ! curl --output /dev/null --silent --head http://localhost:4444/wd/hub; do
#   echo -n "."
  sleep 1
done
# echo " Up!"

OUTPUT=$(./bin/python sram_monitoring_test.py ${ENV}.yml)
RESULT=$?

docker stop chrome >/dev/null 2>&1
# echo "Down"

echo $OUTPUT > status/${ENV}.log
exit $RESULT
