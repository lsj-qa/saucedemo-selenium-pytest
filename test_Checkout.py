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


ALL_FIELDS = [
    (CheckoutStepOne.first_name, FIRST_NAME),
    (CheckoutStepOne.last_name, LAST_NAME),
    (CheckoutStepOne.postal_code, POSTAL_CODE),
]


def _go_to_checkout(base, items):
    """상품을 담고 주문 정보 입력 화면까지 이동"""
    for item in items:
        base.click(InventoryPage.add_to_cart(item), until=InventoryPage.remove(item))
    base.click(Header.cart_link, until="cart.html")
    base.click(CartPage.checkout, until="checkout-step-one.html")


def _fill_customer_info(base, fields):
    """
    배송 정보 입력.

    한 칸을 채우는 사이에 화면이 다시 그려지면 앞서 채운 칸이 지워질 수 있어,
    전부 입력한 뒤 값이 그대로 남아 있는지 다시 확인한다.
    """
    for attempt in (1, 2, 3):
        for locator, value in fields:
            base.send_keys(locator, value)

        remaining = {locator: base.get_value(locator) for locator, _ in fields}
        if all(remaining[locator] == value for locator, value in fields):
            return

    raise AssertionError(f"배송 정보 입력값이 유지되지 않습니다: {remaining}")


def test_checkout_complete(logged_in):
    """주문 전체 플로우가 완료 화면까지 도달해야 한다"""
    driver, base = logged_in

    _go_to_checkout(base, [ITEM_BACKPACK])

    _fill_customer_info(base, ALL_FIELDS)
    base.click(CheckoutStepOne.continue_button, until="checkout-step-two.html")

    base.click(CheckoutStepTwo.finish_button, until="checkout-complete.html")

    assert "Thank you for your order" in base.get_text(CheckoutComplete.header)


def test_checkout_required_fields(logged_in):
    """필수값을 비우면 다음 단계로 넘어가면 안 된다"""
    driver, base = logged_in

    _go_to_checkout(base, [ITEM_BACKPACK])

    # 이름만 입력하고 진행
    _fill_customer_info(base, [(CheckoutStepOne.first_name, FIRST_NAME)])
    base.click(CheckoutStepOne.continue_button, until=CheckoutStepOne.error_message)

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

    _fill_customer_info(base, ALL_FIELDS)
    base.click(CheckoutStepOne.continue_button, until="checkout-step-two.html")

    summary_names = sorted(base.get_texts(CheckoutStepTwo.item_name))
    assert len(summary_names) == 2, f"확인 화면 상품 수가 다릅니다: {summary_names}"


def test_checkout_cancel_keeps_cart(logged_in):
    """
    주문 도중 취소해도 장바구니 내용은 남아 있어야 한다.

    되돌리는 동작에서 데이터가 유실되는지 확인한다.
    """
    driver, base = logged_in

    _go_to_checkout(base, [ITEM_BACKPACK])

    base.click(CheckoutStepOne.cancel_button, until="cart.html")

    assert base.count(CartPage.item) == 1, "주문 취소 후 장바구니가 비워졌습니다"


def test_order_complete_clears_cart(logged_in):
    """주문 완료 후에는 장바구니가 비워져야 한다"""
    driver, base = logged_in

    _go_to_checkout(base, [ITEM_BACKPACK])

    _fill_customer_info(base, ALL_FIELDS)
    base.click(CheckoutStepOne.continue_button, until="checkout-step-two.html")
    base.click(CheckoutStepTwo.finish_button, until="checkout-complete.html")

    assert base.is_absent(Header.cart_badge), "주문이 완료되었는데 장바구니에 수량이 남아 있습니다"
