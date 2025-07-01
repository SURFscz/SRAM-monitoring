#!/bin/bash

function ok {
	if [ "$1" == "0" ]; then
		echo "OK"
	else
		echo "ERROR"
	fi
}

if [ -z "$1" ]; then
	echo "Please specify an environment"
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
if [ ! -f "${ENV}.yml" ]; then
	echo "Environment config file '${ENV}.yml' not available"
	exit 1
fi

echo "Stopping container"
docker container rm -f browser || true
echo "Starting $BROWSER container"
docker run --shm-size=2g --rm -d --name browser -p 4444:4444 -p 7900:7900 "selenium/standalone-${BROWSER}"

i=0
while ! curl --output /dev/null --silent --head http://localhost:4444/wd/hub/status
do
	echo -n "."
	sleep 1
	i=$(( i + 1 ))
	if [ $i -gt 60 ]
	then
		echo "TIMEOUT!"
		exit 1
	fi
done
echo " Up!"

LOGFILE="status/${ENV}.log"

# date
NOW=$(date --utc +"%s")

# Run behave tests
# shellcheck disable=SC2129
for retry in 1 2 3
do
	echo "$NOW" > "${LOGFILE}.new"

	behave features/01_monitoring.feature -D ENV="${ENV}.yml" -D BROWSER="$BROWSER"
	echo "login=$(ok $?)" >> "${LOGFILE}.new"
	behave features/02_sbs.feature -D ENV="${ENV}.yml" -D BROWSER="$BROWSER"
	echo "sbs_login=$(ok $?)" >> "${LOGFILE}.new"
	behave features/03_pam-weblogin.feature -D ENV="${ENV}.yml" -D BROWSER="$BROWSER"
	echo "pam_weblogin=$(ok $?)" >> "${LOGFILE}.new"
	echo "browser=$BROWSER" >> "${LOGFILE}.new"
	echo "tries=$retry" >> "${LOGFILE}.new"

	cat "${LOGFILE}.new"

	# only retry if one of the tests failed
	ok_count=$( grep -c '=OK' "${LOGFILE}.new" )
	if [ "$ok_count" = "3" ]; then
		break
	fi
	echo "check failed, retrying (attempt $retry)..."
done

# only write the file when everything is ok, or we have run out of retries
mv "${LOGFILE}.new" "${LOGFILE}"


docker stop browser >/dev/null 2>&1
docker container rm browser >/dev/null 2>&1
echo "End of  $BROWSER test"
