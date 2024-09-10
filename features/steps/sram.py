from behave import given, when, then
from selenium.webdriver.support.expected_conditions import (
    presence_of_element_located, url_contains, element_to_be_clickable)
from selenium.webdriver.common.by import By
import requests
import time
import json
import re


@given('SBS health UP')
def step_impl(context):
    # Environment
    url = context.env['sbs']['url']
    health = f"{url}health"

    status = ""
    tries = 0
    while status != "UP" and tries < 5:
        tries += 1
        body = requests.get(health)
        state = body.json()
        status = state.get("status")
        time.sleep(1)


@given('we visit monitoring {endpoint}')
def step_impl(context, endpoint):
    # Environment
    url = context.env['monitoring'][endpoint]

    context.browser.get(url)


@given('we visit profile')
def step_impl(context):
    # Environment
    url = context.env['sbs']['url']
    profile = f"{url}profile"

    context.browser.get(profile)


@given('we call pam start')
def step_impl(context):
    # Environment
    url = context.env['sbs']['url']
    start = f"{url}pam-weblogin/start"
    token = context.env['pam']['token']

    regex = r"(https?://.*)\s"
    start_payload = {
        "attribute": "username",
        "cache_duration": 60,
        "GIT_COMMIT": "monitor",
        "JSONPARSER_GIT_COMMIT": "monitor",
    }
    headers = {
        "Authorization": f"Bearer {token}",
    }

    r = requests.post(start, json=start_payload, headers=headers)
    j = json.loads(r.text)

    context.session_id = j['session_id']
    challenge = j['challenge']
    context.link = re.findall(regex, challenge)[0]


@given('we use link to login')
def step_impl(context):
    xpath_login_button = "//span[@class='textual' and text()='Log in']"

    context.browser.get(context.link)

    # Wait for loginpage to load
    context.wait.until(presence_of_element_located((By.XPATH, xpath_login_button)),
                       'Timeout waiting for Profile')
    # Click login
    context.browser.find_element(By.XPATH, xpath_login_button).click()


@given('we choose {idp}')
def step_impl(context, idp):
    # Wait for discovery to load
    context.wait.until(presence_of_element_located((By.XPATH, "//p[@class='subtitleRA21']")),
                       'Timeout waiting for discovery')

    search = context.wait.until(element_to_be_clickable((By.ID, 'searchinput')),
                                'Timeout waiting for searchinput')
    search.send_keys(idp)

    xpath = f"//div[@class='text-truncate label primary' and text()='{idp}']"
    target = context.browser.find_element(By.XPATH, xpath)

    # Choose IdP
    target.click()


@when('we login as {user}')
def step_impl(context, user):
    # Environment
    password = context.env['accounts'][user]['password']

    context.wait.until(url_contains('test-idp.sram.surf.nl'))

    # Login as user
    context.browser.find_element(By.ID, 'username').send_keys(user)
    context.browser.find_element(By.ID, 'password').send_keys(password)
    context.browser.find_element(By.NAME, 'f').submit()


@then('we use code to check pam check-pin')
def step_impl(context):
    # Environment
    url = context.env['sbs']['url']
    check_pin = f"{url}pam-weblogin/check-pin"
    token = context.env['pam']['token']

    xpath_code_element = "//span[@class='value']"
    headers = {
        "Authorization": f"Bearer {token}",
    }

    # Wait for Verification code to load
    context.wait.until(presence_of_element_located((By.XPATH, xpath_code_element)),
                       'Timeout waiting for Profile')

    # Test admin attributes
    code = context.browser.find_elements(By.XPATH, xpath_code_element)[0].text

    pin_payload = {
        "session_id": context.session_id,
        "pin": code,
    }

    r = requests.post(check_pin, json=pin_payload, headers=headers)
    j = json.loads(r.text)

    result = j['result']
    assert (result == "SUCCESS"), "Login did not return SUCCESS"


@then('{user} name in profile')
def step_impl(context, user):
    # Environment
    name = context.env['accounts'][user]['name']

    # Wait for Profile to load
    context.wait.until(presence_of_element_located((By.XPATH, "//h2[text()='Your profile']")),
                       'Timeout waiting for Profile')

    # Test user attributes
    attributes = context.browser.find_elements(By.XPATH, "//table[@class='my-attributes']/*/*/*")
    print(name)
    for a in attributes:
        print(a.text)
    assert (name in [a.text for a in attributes]), "No valid user profile found"


@then('test userdata for {user} in {endpoint}')
def step_impl(context, user, endpoint):
    # Environment
    userdata = context.env['user_data'][user][endpoint]

    data_element = context.browser.find_elements(By.ID, "data")[0].text
    data = json.loads(data_element)

    for key, value in userdata.items():
        if isinstance(value, list):
            for item in value:
                assert (item in data.get(key)), f"{user['name']}, {key}: {item} not found"
        else:
            assert (value in data.get(key)), f"{user['name']}, {key}: {value} not found"
