"""
장바구니 시나리오 — 담기 / 제거 / 상태 유지

원본(모바일 앱) 자동화에서 '공고 등록 → 수정 → 삭제' 로 구성했던
생명주기 검증을 이 사이트의 '담기 → 변경 → 제거' 로 옮긴 것입니다.
"""
from BaseAction import BaseAction
from ele_cart import CartPage
from ele_inventory import ITEM_BACKPACK, ITEM_BIKE_LIGHT, Header, InventoryPage


def test_add_to_cart(logged_in):
    """상품을 담으면 배지 수량이 증가하고 장바구니에 노출되어야 한다"""
    driver, base = logged_in

    base.click(InventoryPage.add_to_cart(ITEM_BACKPACK))
    assert base.get_text(Header.cart_badge) == "1"

    base.click(Header.cart_link)
    base.wait_url_contains("cart.html")

    names = base.get_texts(CartPage.item_name)
    assert len(names) == 1
    assert base.get_text(CartPage.item_quantity) == "1"


def test_add_multiple_items(logged_in):
    """여러 상품을 담으면 수량이 누적되어야 한다"""
    driver, base = logged_in

    base.click(InventoryPage.add_to_cart(ITEM_BACKPACK))
    base.click(InventoryPage.add_to_cart(ITEM_BIKE_LIGHT))

    assert base.get_text(Header.cart_badge) == "2"

    base.click(Header.cart_link)
    assert base.count(CartPage.item) == 2


def test_remove_from_cart(logged_in):
    """장바구니에서 제거하면 배지가 사라져야 한다"""
    driver, base = logged_in

    base.click(InventoryPage.add_to_cart(ITEM_BACKPACK))
    base.click(Header.cart_link)
    base.wait_url_contains("cart.html")

    base.click(CartPage.remove(ITEM_BACKPACK))

    assert base.count(CartPage.item) == 0
    assert base.is_absent(Header.cart_badge), "장바구니를 비웠는데 수량 배지가 남아 있습니다"


def test_cart_kept_after_navigation(logged_in):
    """
    목록 ↔ 장바구니를 오가도 담은 내용이 유지되어야 한다.

    화면 전환 시 상태가 초기화되는 결함을 잡기 위한 케이스.
    """
    driver, base = logged_in

    base.click(InventoryPage.add_to_cart(ITEM_BACKPACK))
    base.click(Header.cart_link)
    base.wait_url_contains("cart.html")

    base.click(CartPage.continue_shopping)
    base.wait_url_contains("inventory.html")

    assert base.get_text(Header.cart_badge) == "1", "목록으로 돌아오자 장바구니가 초기화되었습니다"

    base.click(Header.cart_link)
    assert base.count(CartPage.item) == 1


def test_add_remove_repeat(logged_in):
    """
    담기와 제거를 반복해도 수량이 어긋나지 않아야 한다.

    단발 동작으로는 드러나지 않는 상태 누적 결함을 확인한다.

    버튼을 누른 직후 배지를 바로 읽으면 화면이 다시 그려지는 시점과 겹쳐
    결과가 일정하지 않다. 그래서 '버튼이 전환되었는지'를 먼저 확인한 뒤
    수량을 검증한다.
    """
    driver, base = logged_in

    for i in range(1, 4):
        base.click(InventoryPage.add_to_cart(ITEM_BACKPACK))
        assert base.is_displayed(InventoryPage.remove(ITEM_BACKPACK)), \
            f"{i}회차: 담기 후 제거 버튼으로 전환되지 않았습니다"
        assert base.get_text(Header.cart_badge) == "1", \
            f"{i}회차: 수량이 1이 아닙니다"

        base.click(InventoryPage.remove(ITEM_BACKPACK))
        assert base.is_displayed(InventoryPage.add_to_cart(ITEM_BACKPACK)), \
            f"{i}회차: 제거 후 담기 버튼으로 복귀하지 않았습니다"
        assert base.is_absent(Header.cart_badge), f"{i}회차: 제거 후에도 수량 배지가 남아 있습니다"
