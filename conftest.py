"""
pytest 공통 설정 — WebDriver 생성/종료 및 공용 fixture

원본(Appium) 구조에서 드라이버 계층만 Selenium 으로 교체한 파일입니다.
테스트 함수는 driver 를 직접 만들지 않고 fixture 로 주입받습니다.
"""
import re
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from BaseAction import BaseAction
from ele_login import LoginPage

BASE_URL = "https://www.saucedemo.com/"

# 실패한 순간의 화면과 HTML 을 남겨 둘 위치.
# 다른 환경(CI)에서만 재현되는 실패는 로그만으로 원인을 좁히기 어렵다.
FAILURE_DIR = Path(__file__).parent / "failures"

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
    # CI 리눅스 서버는 공유 메모리 영역이 작아 브라우저가 도중에 죽는 경우가 있다.
    options.add_argument("--disable-dev-shm-usage")
    # 화면 없이 돌릴 때 브라우저가 창을 '가려진 상태'로 판정하면 키 입력이
    # 화면에 전달되지 않는 경우가 있다. 그 판정 자체를 하지 않도록 한다.
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-features=CalculateNativeWinOcclusion")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    # Selenium 4.6+ 는 드라이버를 자동으로 내려받으므로 별도 설치가 필요 없습니다.
    drv = webdriver.Chrome(options=options)
    drv.get(BASE_URL)

    yield drv

    drv.quit()


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    """테스트가 실패하면 그 시점의 화면과 HTML 을 파일로 남긴다."""
    report = yield

    if report.when == "call" and report.failed:
        drv = item.funcargs.get("driver")
        if drv is not None:
            FAILURE_DIR.mkdir(exist_ok=True)
            name = re.sub(r"[^\w.-]", "_", item.name)
            try:
                drv.save_screenshot(str(FAILURE_DIR / f"{name}.png"))
                (FAILURE_DIR / f"{name}.html").write_text(
                    drv.page_source, encoding="utf-8"
                )
            except Exception as exc:  # 저장 실패가 테스트 결과를 덮어쓰지 않도록 한다
                print(f"[실패 화면 저장 실패] {name}: {exc}")

    return report


@pytest.fixture()
def logged_in(driver):
    """로그인이 전제인 테스트에서 사용하는 fixture. (driver, BaseAction) 반환."""
    base = BaseAction(driver)
    base.send_keys(LoginPage.username, STANDARD_USER)
    base.send_keys(LoginPage.password, PASSWORD)
    base.click(LoginPage.login_button, until="inventory.html")
    return driver, base
