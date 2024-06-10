#!/bin/sh
if [ -z $1 ]; then
	echo "Environment not set"
	exit 1
fi

if [ "$2" != "chrome" ] && [ "$2" != "firefox" ]; then
	echo "Warning: browser not set (chrome or firefox)"
	echo "Defaulting to chrome"
	BROWSER="chrome"
else
	BROWSER=$2
fi

ENV=$1
if [ ! -f ${ENV}.yml ]; then
	echo "Environment config not available"
	exit 1
fi

echo "Starting $BROWSER container"
if [ "$BROWSER" = "chrome" ]; then
	docker run --shm-size=2g --rm -d --name browser -p 4444:4444 -p 7900:7900 selenium/standalone-chrome >/dev/null 2>&1
fi
if [ "$BROWSER" = "firefox" ]; then
	docker run --shm-size=2g --rm -d --name browser -p 4444:4444 -p 7900:7900 selenium/standalone-firefox >/dev/null 2>&1
fi

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
OUTPUT=$(python3 sram_monitoring_test.py "${ENV}.yml" "$BROWSER")
echo login=$OUTPUT >> ${LOGFILE}.new

# SBS login test
OUTPUT=$(python3 sbs-login.py "${ENV}.yml" "$BROWSER")
echo sbs_login=$OUTPUT >> ${LOGFILE}.new

# PAM weblogin test
OUTPUT=$(python3 pam-monitor.py "${ENV}.yml" "$BROWSER")
echo pam_weblogin=$OUTPUT >> ${LOGFILE}.new

echo "browser=$BROWSER" >> ${LOGFILE}.new

cat ${LOGFILE}.new
mv ${LOGFILE}.new ${LOGFILE}

docker stop browser >/dev/null 2>&1
echo "End of  $BROWSER test"
