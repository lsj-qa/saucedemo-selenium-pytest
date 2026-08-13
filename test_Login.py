"""
로그인 / 로그아웃 시나리오

- 정상 로그인 후 로그아웃까지 왕복 확인
- 잠긴 계정, 잘못된 비밀번호 등 실패 경로도 함께 검증
"""
from BaseAction import BaseAction
from conftest import LOCKED_OUT_USER, PASSWORD, STANDARD_USER
from ele_inventory import Header, InventoryPage
from ele_login import LoginPage


def test_login_logout(driver):
    """정상 계정 로그인 → 상품 목록 진입 → 로그아웃 → 로그인 화면 복귀"""
    base = BaseAction(driver)

    base.send_keys(LoginPage.username, STANDARD_USER)
    base.send_keys(LoginPage.password, PASSWORD)
    base.click(LoginPage.login_button, until="inventory.html")

    assert base.get_text(InventoryPage.title) == "Products"

    base.click(Header.burger_menu, until=Header.logout_link)
    base.click(Header.logout_link, until=LoginPage.login_button)

    assert base.is_displayed(LoginPage.login_button), "로그아웃 후 로그인 화면으로 돌아오지 않았습니다"


def test_login_locked_out_user(driver):
    """잠긴 계정은 진입이 차단되고 안내 문구가 노출되어야 한다"""
    base = BaseAction(driver)

    base.send_keys(LoginPage.username, LOCKED_OUT_USER)
    base.send_keys(LoginPage.password, PASSWORD)
    base.click(LoginPage.login_button, until=LoginPage.error_message)

    message = base.get_text(LoginPage.error_message)
    assert "locked out" in message, f"예상과 다른 메시지: {message}"
    assert "inventory.html" not in driver.current_url, "잠긴 계정이 상품 목록에 진입했습니다"


def test_login_wrong_password(driver):
    """비밀번호가 틀리면 로그인되지 않아야 한다"""
    base = BaseAction(driver)

    base.send_keys(LoginPage.username, STANDARD_USER)
    base.send_keys(LoginPage.password, "wrong_password")
    base.click(LoginPage.login_button, until=LoginPage.error_message)

    assert base.is_displayed(LoginPage.error_message)
    assert "inventory.html" not in driver.current_url


def test_login_empty_input(driver):
    """아이디·비밀번호 미입력 시 안내 문구가 노출되어야 한다"""
    base = BaseAction(driver)

    base.click(LoginPage.login_button, until=LoginPage.error_message)

    message = base.get_text(LoginPage.error_message)
    assert "Username is required" in message, f"예상과 다른 메시지: {message}"


def test_logout_then_back_button(driver):
    """
    로그아웃 후 브라우저 뒤로가기로 이전 화면에 접근되면 안 된다.

    조작이 아니라 '이탈 후 재진입'을 검증하는 케이스로,
    세션이 끊긴 뒤에도 화면이 남아 있는지 확인한다.
    """
    base = BaseAction(driver)

    base.send_keys(LoginPage.username, STANDARD_USER)
    base.send_keys(LoginPage.password, PASSWORD)
    base.click(LoginPage.login_button, until="inventory.html")

    base.click(Header.burger_menu, until=Header.logout_link)
    base.click(Header.logout_link, until=LoginPage.login_button)

    driver.back()

    assert base.is_absent(InventoryPage.item), "로그아웃 후 뒤로가기로 상품 목록이 노출되었습니다"
