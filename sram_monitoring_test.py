#!/usr/bin/env python

from selenium.webdriver import Remote, ChromeOptions, FirefoxOptions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.expected_conditions import (staleness_of, presence_of_element_located,
                                                            title_contains, url_contains)
from selenium.webdriver.common.by import By

import sys
import yaml
import json

if len(sys.argv) < 3:
    sys.exit(sys.argv[0] + "  <argument>")

print(f"= READING {sys.argv[1:]} ====", file=sys.stderr)
with open(sys.argv[1], 'r') as f:
    try:
        config = yaml.load(f, Loader=yaml.FullLoader)
    except yaml.YAMLError as exc:
        print(exc)


KEY = 'sram_monitoring'
config = config[KEY]

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


def test_user(start, user, userinfo):
    browser = Remote("http://127.0.0.1:4444/wd/hub", options=options)
    browser.implicitly_wait(2)
    wait = WebDriverWait(browser, timeout=2)

    print("============", file=sys.stderr)
    print(f"user: {user}", file=sys.stderr)
    print(f"userinfo: {userinfo}", file=sys.stderr)

    try:
        # Start browser on RP
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

        wait.until(url_contains('test-idp.sram.surf.nl'))

        # Login as user
        browser.find_element(By.ID, 'username').send_keys(user['name'])
        browser.find_element(By.ID, 'password').send_keys(user['password'])
        browser.find_element(By.NAME, 'f').submit()

        # Wait for user profile to appear
        wait.until(presence_of_element_located((By.ID, "data")), 'Timeout waiting for user userinfo')

        # Test userinfo
        data_element = browser.find_elements(By.ID, "data")[0].text
        data = json.loads(data_element)
        for key, value in userinfo.items():
            if isinstance(value, list):
                for item in value:
                    # print(f"Testing {key}: {item}")
                    assert (item in data.get(key)), f"{user['name']}, {key}: {item} not found"
            else:
                # print(f"Testing {key}: {value}")
                assert (value in data.get(key)), f"{user['name']}, {key}: {value} not found"

    except Exception as e:
        # print the type of exception and the message, but not the stacktrace
        print(f"Exception: {type(e).__name__}: {e}", file=sys.stderr)

        print(f"Last page encountered: {browser.current_url}", file=sys.stderr)
        print(f"FAILED on user={user['name']} page={start}", file=sys.stderr)
        print(f"FAILED on user={user['name']} page={start}")
        # page = browser.page_source
        # print("page: {}".format(page))
        browser.quit()

        # exit without error, so that the next tests will still run
        exit(0)

    print("= OK =======", file=sys.stderr)
    browser.quit()


user = {}
for startpage, accounts in config.items():
    # print(f"start: {startpage}")
    for account, userinfo in accounts.items():
        (username, password) = account.split('.')
        user['name'] = username
        user['password'] = password
        test_user(startpage, user, userinfo)

print('OK')
