#!/usr/bin/env python

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.expected_conditions import staleness_of, title_is, presence_of_element_located
from selenium.webdriver.common.by import By

import yaml

KEY = 'sbs_ci'

with open("config.yml", 'r') as f:
    try:
        config = yaml.load(f, Loader=yaml.FullLoader)
    except yaml.YAMLError as exc:
        print(exc)

start = config[KEY]['start']
user = config[KEY]['user']
password = config[KEY]['password']

options = Options()
options.headless = True
options.add_argument('ignore-certificate-errors')
browser = Chrome(executable_path='./chromedriver_86', options=options)
browser.implicitly_wait(2)
wait = WebDriverWait(browser, timeout=2)

try:
    # Start browser
    browser.get(start)

    # Wait for SBS to load
    wait.until(title_is('Research Access Management'), 'Timeout waiting for landing page')

    # Click login
    login = browser.find_element_by_xpath("//a[@href='/login' and text()='Login']")
    login.click()

    # Wait for login button to disappear
    wait.until(staleness_of(login), 'Timeout waiting for login page')

    # Login as user
    browser.find_element_by_id('usernames').send_keys(user)
    browser.find_element_by_id('password').send_keys(password)
    browser.find_element_by_tag_name('form').submit()

    # Wait for user profile to appear
    wait.until(presence_of_element_located((By.XPATH, "//li[@class='user-profile']")), 'Timeout waiting for user profile')

    # Test SBS title
    title = browser.title
    assert(title == "Research Access Management"), "Error loading SBS return url"

    # Click profile dropdown
    profile = browser.find_element_by_xpath("//li[@class='user-profile']/a/span").click()

    # Test user attributes
    attributes = browser.find_elements_by_xpath("//ul[@class='user-profile']/li/span[@class='value']")
    assert(user in [a.text for a in attributes]), "No valid user profile found"

    # Close browser
    browser.close()
    print('OK')

except Exception as e:
    page = browser.page_source
    print(e)
    print("page: {}".format(page))
    browser.close()
    exit(1)

