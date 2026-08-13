"""
주문 시나리오 — 정보입력 → 확인 → 완료

정상 완료 경로뿐 아니라 필수값 누락, 중간 취소 같은
정상 흐름에서 벗어나는 경로도 함께 검증합니다.
"""
from BaseAction import BaseAction
from ele_cart import CartPage
from ele_checkout import CheckoutComplete, CheckoutStepOne, CheckoutStepTwo
from ele_inventory import ITEM_BACKPACK, ITEM_BIKE_LIGHT, Header, InventoryPage

FIRST_NAME = "Sujin"
LAST_NAME = "Lee"
POSTAL_CODE = "06236"


def _go_to_checkout(base, items):
    """상품을 담고 주문 정보 입력 화면까지 이동"""
    for item in items:
        base.click(InventoryPage.add_to_cart(item))
    base.click(Header.cart_link)
    base.wait_url_contains("cart.html")
    base.click(CartPage.checkout)
    base.wait_url_contains("checkout-step-one.html")


def test_checkout_complete(logged_in):
    """주문 전체 플로우가 완료 화면까지 도달해야 한다"""
    driver, base = logged_in

    _go_to_checkout(base, [ITEM_BACKPACK])

    base.send_keys(CheckoutStepOne.first_name, FIRST_NAME)
    base.send_keys(CheckoutStepOne.last_name, LAST_NAME)
    base.send_keys(CheckoutStepOne.postal_code, POSTAL_CODE)
    base.click(CheckoutStepOne.continue_button)

    base.wait_url_contains("checkout-step-two.html")
    base.click(CheckoutStepTwo.finish_button)

    base.wait_url_contains("checkout-complete.html")
    assert "Thank you for your order" in base.get_text(CheckoutComplete.header)


def test_checkout_required_fields(logged_in):
    """필수값을 비우면 다음 단계로 넘어가면 안 된다"""
    driver, base = logged_in

    _go_to_checkout(base, [ITEM_BACKPACK])

    # 이름만 입력하고 진행
    base.send_keys(CheckoutStepOne.first_name, FIRST_NAME)
    base.click(CheckoutStepOne.continue_button)

    message = base.get_text(CheckoutStepOne.error_message)
    assert "Last Name is required" in message, f"예상과 다른 메시지: {message}"
    assert "checkout-step-two" not in driver.current_url


def test_checkout_summary_matches_cart(logged_in):
    """
    주문 확인 화면의 상품이 장바구니와 일치해야 한다.

    화면 간 데이터가 어긋나는 결함을 잡기 위해
    '담은 것'과 '확인 화면에 보이는 것'을 대조한다.
    """
    driver, base = logged_in

    _go_to_checkout(base, [ITEM_BACKPACK, ITEM_BIKE_LIGHT])

    base.send_keys(CheckoutStepOne.first_name, FIRST_NAME)
    base.send_keys(CheckoutStepOne.last_name, LAST_NAME)
    base.send_keys(CheckoutStepOne.postal_code, POSTAL_CODE)
    base.click(CheckoutStepOne.continue_button)
    base.wait_url_contains("checkout-step-two.html")

    summary_names = sorted(base.get_texts(CheckoutStepTwo.item_name))
    assert len(summary_names) == 2, f"확인 화면 상품 수가 다릅니다: {summary_names}"


def test_checkout_cancel_keeps_cart(logged_in):
    """
    주문 도중 취소해도 장바구니 내용은 남아 있어야 한다.

    되돌리는 동작에서 데이터가 유실되는지 확인한다.
    """
    driver, base = logged_in

    _go_to_checkout(base, [ITEM_BACKPACK])

    base.click(CheckoutStepOne.cancel_button)
    base.wait_url_contains("cart.html")

    assert base.count(CartPage.item) == 1, "주문 취소 후 장바구니가 비워졌습니다"


def test_order_complete_clears_cart(logged_in):
    """주문 완료 후에는 장바구니가 비워져야 한다"""
    driver, base = logged_in

    _go_to_checkout(base, [ITEM_BACKPACK])

    base.send_keys(CheckoutStepOne.first_name, FIRST_NAME)
    base.send_keys(CheckoutStepOne.last_name, LAST_NAME)
    base.send_keys(CheckoutStepOne.postal_code, POSTAL_CODE)
    base.click(CheckoutStepOne.continue_button)
    base.click(CheckoutStepTwo.finish_button)
    base.wait_url_contains("checkout-complete.html")

    assert base.is_absent(Header.cart_badge), "주문이 완료되었는데 장바구니에 수량이 남아 있습니다"
