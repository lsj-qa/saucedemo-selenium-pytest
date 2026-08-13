"""
pytest 공통 설정 — WebDriver 생성/종료 및 공용 fixture

원본(Appium) 구조에서 드라이버 계층만 Selenium 으로 교체한 파일입니다.
테스트 함수는 driver 를 직접 만들지 않고 fixture 로 주입받습니다.
"""
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from BaseAction import BaseAction
from ele_login import LoginPage

BASE_URL = "https://www.saucedemo.com/"

# 데모 사이트 공개 계정 (사이트 첫 화면에 게시된 값)
STANDARD_USER = "standard_user"
LOCKED_OUT_USER = "locked_out_user"
PASSWORD = "secret_sauce"


def pytest_addoption(parser):
    parser.addoption(
        "--headless",
        action="store_true",
        default=False,
        help="브라우저 창 없이 실행 (CI 용)",
    )


@pytest.fixture()
def driver(request):
    """Chrome WebDriver 생성 → 테스트 종료 시 자동 종료."""
    options = Options()
    if request.config.getoption("--headless"):
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,900")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-gpu")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    # Selenium 4.6+ 는 드라이버를 자동으로 내려받으므로 별도 설치가 필요 없습니다.
    drv = webdriver.Chrome(options=options)
    drv.get(BASE_URL)

    yield drv

    drv.quit()


@pytest.fixture()
def logged_in(driver):
    """로그인이 전제인 테스트에서 사용하는 fixture. (driver, BaseAction) 반환."""
    base = BaseAction(driver)
    base.send_keys(LoginPage.username, STANDARD_USER)
    base.send_keys(LoginPage.password, PASSWORD)
    base.click(LoginPage.login_button)
    base.wait_url_contains("inventory.html")
    return driver, base
