#!/usr/bin/env python

from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.expected_conditions import (staleness_of, presence_of_element_located,
                                                            title_contains)
from selenium.webdriver.common.by import By

import sys
import yaml
import json
import time
import traceback

if len(sys.argv) < 2:
    sys.exit(sys.argv[0] + "  <argument>")

print(f"= READING {sys.argv[1]} ====", file=sys.stderr)
with open(sys.argv[1], 'r') as f:
    try:
        config = yaml.load(f, Loader=yaml.FullLoader)
    except yaml.YAMLError as exc:
        print(exc)

KEY = 'sbs_login'
config = config[KEY]

xpath_login_button = '//button[span[text()="Log in"]]'
xpath_logo = '//a[@class="logo"]//span[text()="Research Access Management"]'

print("= Starting Chrome ===", file=sys.stderr)
options = ChromeOptions()
options.add_argument('--headless')
browser = Remote("http://127.0.0.1:4444", options=options)
send_command = ('POST', '/session/$sessionId/chromium/send_command')
browser.command_executor._commands['SEND_COMMAND'] = send_command
browser.implicitly_wait(1)
wait = WebDriverWait(browser, timeout=2)


try:
    for (url, login) in config.items():
        print(url, file=sys.stderr)
        for (account, name) in login.items():
            (username, password) = account.split('.')
            print("============", file=sys.stderr)
            print(username, name, file=sys.stderr)
            # print(password, file=sys.stderr)
            # print(name, file=sys.stderr)

            health = f'{url}health'
            start = f'{url}profile'

            # Wait for SBS health up
            status = ""
            while status != "UP":
                browser.get(health)
                state = json.loads(browser.find_element(By.XPATH, "//pre").text)
                status = state.get("status")
                time.sleep(1)

            # Clear cookies
            browser.execute('SEND_COMMAND', dict(cmd='Network.clearBrowserCookies', params={}))

            # Get SBS profile page
            browser.get(start)

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

            # Wait for Profile to load
            wait.until(presence_of_element_located((By.XPATH, "//h2[text()='Your profile']")),
                       'Timeout waiting for Profile')

            # Test admin attributes
            attributes = browser.find_elements(By.XPATH, "//table[@class='my-attributes']/*/*/*")
            # for a in attributes:
            #     print(f"a.text: {a.text}")
            assert (name in [a.text for a in attributes]), "No valid admin profile found"
            print("= OK =======", file=sys.stderr)
        print("OK")
    browser.quit()
    print("============", file=sys.stderr)
    exit(0)

except Exception as e:
    # url = browser.current_url
    # print(f"url: {url}")

    tr = traceback.extract_tb(e.__traceback__)[0]
    print(f"error {type(e).__name__} on line {tr.lineno} of '{tr.filename}'")
    browser.quit()

    print("", end="", flush=True)
    exit(1)
