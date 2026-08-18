"""
로그인 / 로그아웃 시나리오

- 정상 로그인 후 로그아웃까지 왕복 확인
- 진입이 차단되어야 하는 조건은 한 곳에 모아 데이터로 관리
"""
import pytest

from BaseAction import BaseAction
from conftest import LOCKED_OUT_USER, PASSWORD, STANDARD_USER
from ele_inventory import Header, InventoryPage
from ele_login import LoginPage

# 진입이 차단되어야 하는 조건들.
#
# 케이스마다 함수를 따로 두면 확인 절차가 복사되어 흩어지고, 조건이 늘 때마다
# 같은 코드를 다시 쓰게 된다. 조건은 데이터로 두고 절차는 하나만 둔다.
# 새 조건이 생기면 이 표에 한 줄을 추가한다.
REJECTED_LOGINS = [
    pytest.param(LOCKED_OUT_USER, PASSWORD, "locked out", id="잠긴계정"),
    pytest.param(STANDARD_USER, "wrong_password", "do not match", id="비밀번호불일치"),
    pytest.param("wrong_user", PASSWORD, "do not match", id="없는계정"),
    pytest.param("", PASSWORD, "Username is required", id="아이디미입력"),
    pytest.param(STANDARD_USER, "", "Password is required", id="비밀번호미입력"),
    pytest.param("", "", "Username is required", id="둘다미입력"),
]


@pytest.mark.smoke
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


@pytest.mark.regression
@pytest.mark.parametrize("username, password, expected", REJECTED_LOGINS)
def test_login_rejected(driver, username, password, expected):
    """
    차단되어야 하는 조건에서는 진입이 막히고 사유가 안내되어야 한다.

    '들어가지지 않는다'만 보면 사유가 뒤바뀌어도 통과한다.
    아이디 미입력에 비밀번호 안내가 뜨는 식의 결함을 잡기 위해
    **어떤 사유로 막혔는지**까지 확인한다.
    """
    base = BaseAction(driver)

    base.send_keys(LoginPage.username, username)
    base.send_keys(LoginPage.password, password)
    base.click(LoginPage.login_button, until=LoginPage.error_message)

    message = base.get_text(LoginPage.error_message)
    assert expected in message, f"예상과 다른 안내 문구: {message}"
    assert "inventory.html" not in driver.current_url, "차단되어야 할 조건에서 진입되었습니다"


@pytest.mark.regression
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
