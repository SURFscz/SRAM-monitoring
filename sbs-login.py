#!/usr/bin/env python

from selenium.webdriver import Remote, ChromeOptions, FirefoxOptions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.expected_conditions import (staleness_of, presence_of_element_located,
                                                            title_contains)
from selenium.webdriver.common.by import By

import sys
import yaml
import json
import time
import traceback
import requests

if len(sys.argv) < 3:
    sys.exit(sys.argv[0] + "  <argument>")

print(f"= READING {sys.argv[1:]} ====", file=sys.stderr)
with open(sys.argv[1], 'r') as f:
    try:
        config = yaml.load(f, Loader=yaml.FullLoader)
    except yaml.YAMLError as exc:
        print(exc)

KEY = 'sbs_login'
config = config[KEY]

xpath_login_button = '//button[span[text()="Log in"]]'
xpath_logo = '//a[@class="logo"]//span[text()="Research Access Management"]'

browser = sys.argv[2]
print(f"= Starting Browser {browser} ===", file=sys.stderr)
if browser == "chrome":
    options = ChromeOptions()
elif browser == "firefox":
    options = FirefoxOptions()
else:
    print('Bad Browser')
    exit

options.add_argument('--headless')

try:
    for (url, login) in config.items():
        print(url, file=sys.stderr)
        for (account, name) in login.items():
            browser = Remote("http://127.0.0.1:4444", options=options)
            browser.implicitly_wait(10)
            wait = WebDriverWait(browser, timeout=10)

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
                body = requests.get(health)
                state = body.json()
                status = state.get("status")
                time.sleep(1)

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
            browser.quit()

        print("OK")
    print("============", file=sys.stderr)
    exit(0)

except Exception as e:
    # url = browser.current_url
    # print(f"url: {url}")

    tr = traceback.extract_tb(e.__traceback__)[0]
    print(f"error {type(e).__name__} on line {tr.lineno} of '{tr.filename}'")
    browser.save_screenshot("screenshot.png")
    browser.quit()

    print("", end="", flush=True)
    exit(1)
