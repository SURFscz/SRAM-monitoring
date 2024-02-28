#!/usr/bin/env python
import sys
import time
import yaml
import requests
import json
import re
import traceback

from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.expected_conditions import (staleness_of, presence_of_element_located,
                                                            title_contains)
from selenium.webdriver.common.by import By

if len(sys.argv) < 2:
    sys.exit(sys.argv[0] + "  <argument>")

print(f"= READING {sys.argv[1]} ====", file=sys.stderr)
with open(sys.argv[1], 'r') as f:
    try:
        config = yaml.load(f, Loader=yaml.FullLoader)
    except yaml.YAMLError as exc:
        print(exc)

KEY = 'pam_monitor'
config = config[KEY]

start_payload = {
    # "user_id": "ascz",
    "attribute": "username",
    "cache_duration": 60,
    "GIT_COMMIT": "monitor",
    "JSONPARSER_GIT_COMMIT": "monitor",
}
regex = r"(https?://.*)\s"
xpath_login_button = "//span[@class='textual' and text()='Log in']"
xpath_code_element = "//span[@class='value']"


print("= Starting Chrome ===", file=sys.stderr)
options = ChromeOptions()
options.add_argument('--headless')
browser = Remote("http://127.0.0.1:4444", options=options)
send_command = ('POST', '/session/$sessionId/chromium/send_command')
browser.command_executor._commands['SEND_COMMAND'] = send_command
browser.implicitly_wait(1)
wait = WebDriverWait(browser, timeout=2)


try:
    for url, values in config.items():
        token = values['token']
        account = values['account']
        (username, password) = account.split('.')
        # print(f"{url}, {token}", file=sys.stderr)
        # print(f"{username}:{password}", file=sys.stderr)
        health = f'{url}health'
        headers = {
            "Authorization": f"Bearer {token}",
        }

        r = requests.post(f"{url}pam-weblogin/start", json=start_payload, headers=headers)
        j = json.loads(r.text)

        session_id = j['session_id']
        challenge = j['challenge']
        link = re.findall(regex, challenge)[0]
        print(link, file=sys.stderr)
        # break

        # Wait for SBS health up
        status = ""
        while status != "UP":
            browser.get(health)
            state = json.loads(browser.find_element(By.XPATH, "//pre").text)
            status = state.get("status")
            time.sleep(1)

        # Clear cookies
        browser.execute('SEND_COMMAND', dict(cmd='Network.clearBrowserCookies', params={}))

        # Get SBS link page
        browser.get(link)

        # Wait for loginpage to load
        wait.until(presence_of_element_located((By.XPATH, xpath_login_button)),
                   'Timeout waiting for Profile')

        # Click login
        browser.find_element(By.XPATH, xpath_login_button).click()

        # Wait for discovery to load
        wait.until(title_contains('SURF Research Access Management'),
                   'Timeout waiting for discovery')

        # Choose Monitoring IdP
        try:
            xpath = "//div[@class='primary' and text()='SRAM Monitoring IdP']"
            monitor = browser.find_element(By.XPATH, xpath)
        except Exception:
            search = browser.find_element(By.ID, 'searchinput')
            search.send_keys('monitoring')
            xpath = "//div[@class='text-truncate label primary' and text()='SRAM Monitoring IdP']"
            monitor = browser.find_element(By.XPATH, xpath)

        monitor.click()

        wait.until(staleness_of(monitor))

        # Login as user
        browser.find_element(By.ID, 'username').send_keys(username)
        browser.find_element(By.ID, 'password').send_keys(password)
        browser.find_element(By.NAME, 'f').submit()

        # Wait for Verification code to load
        wait.until(presence_of_element_located((By.XPATH, xpath_code_element)),
                   'Timeout waiting for Profile')

        # Test admin attributes
        code = browser.find_elements(By.XPATH, xpath_code_element)[0].text

        print(f"code: {code}", file=sys.stderr)

        pin_payload = {
            "session_id": session_id,
            "pin": code,
        }

        r = requests.post(f"{url}pam-weblogin/check-pin", json=pin_payload, headers=headers)
        j = json.loads(r.text)

        result = j['result']

        if not result == "SUCCESS":
          raise Exception("FAIL")

        print(f"result: {result}", file=sys.stderr)
        print("= OK =======", file=sys.stderr)

    print("OK")
    browser.quit()

except Exception as e:
    tr = traceback.extract_tb(e.__traceback__)[0]
    print(f"error {type(e).__name__} on line {tr.lineno} of '{tr.filename}'")
    browser.quit()
    exit(1)
