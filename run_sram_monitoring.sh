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

echo "Starting chrome container"
docker run --shm-size=2g --rm -d --name chrome -p 4444:4444 selenium/standalone-chrome >/dev/null 2>&1
i=0
while ! curl --output /dev/null --silent --head http://localhost:4444/wd/hub/status; do
    echo -n "."
    sleep 1
    i=$(( $i + 1 ))
    if [ $i -gt 60 ]
    then
        echo "TIMEOUT!"
        exit 1
    fi
done
echo " Up!"

LOGFILE="status/${ENV}.log"

#date
date --utc +"%s" > ${LOGFILE}.new

# Service login test
OUTPUT=$(python3 sram_monitoring_test.py ${ENV}.yml)
echo login=$OUTPUT >> ${LOGFILE}.new

# SBS login test
OUTPUT=$(python3 sbs-login.py ${ENV}.yml)
echo sbs_login=$OUTPUT >> ${LOGFILE}.new

# PAM weblogin test
OUTPUT=$(python3 pam-monitor.py ${ENV}.yml)
echo pam_weblogin=$OUTPUT >> ${LOGFILE}.new

mv ${LOGFILE}.new ${LOGFILE}

docker stop chrome >/dev/null 2>&1
# echo "Down"
