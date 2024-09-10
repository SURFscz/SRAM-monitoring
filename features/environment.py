from behave import fixture, use_fixture
from selenium.webdriver import Remote, ChromeOptions, FirefoxOptions
from selenium.webdriver.support.wait import WebDriverWait
import yaml


@fixture
def selenium_browser(context, browser):
    if browser == 'chrome':
        options = ChromeOptions()
    else:
        options = FirefoxOptions()

    options.add_argument('--headless')
    # options.add_argument('--ignore-certificate-errors')
    # options.add_argument('--user-data-dir=/tmp/chrome-data')
    context.browser = Remote("http://127.0.0.1:4444", options=options)
    context.browser.implicitly_wait(5)
    context.wait = WebDriverWait(context.browser, timeout=5)

    # Halts all tests on error
    context.config.stop = True
    yield context.browser

    context.browser.quit()


def before_all(context):
    env = context.config.userdata.get("ENV")

    with open(env, 'r') as f:
        try:
            config = yaml.load(f, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    context.env = config


def before_feature(context, feature):
    pass


def before_scenario(context, scenario):
    browser = context.config.userdata.get("BROWSER")
    use_fixture(selenium_browser, context, browser)


def after_scenario(context, scenario):
    pass


def after_step(context, step):
    if step.status == "failed":
        print(context.browser.current_url)
        print(context.browser.page_source)
        context.browser.save_screenshot("screenshot.png")
