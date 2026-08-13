"""
상품 목록 시나리오

- 목록 노출 확인
- 정렬 기능이 실제로 정렬된 결과를 내는지 값으로 검증
"""
from BaseAction import BaseAction
from ele_inventory import InventoryPage


def _prices(base):
    """'$29.99' 형태의 텍스트를 float 리스트로 변환"""
    return [float(t.replace("$", "")) for t in base.get_texts(InventoryPage.item_price)]


def test_product_list_displayed(logged_in):
    """로그인 후 상품 목록이 노출되고 항목 수가 0보다 커야 한다"""
    driver, base = logged_in

    assert base.get_text(InventoryPage.title) == "Products"
    assert base.count(InventoryPage.item) > 0, "상품이 하나도 노출되지 않았습니다"


def test_sort_price_low_to_high(logged_in):
    """가격 낮은 순 정렬 — 화면 표시가 아니라 실제 값의 순서를 확인"""
    driver, base = logged_in

    base.select_by_value(InventoryPage.sort_select, "lohi")
    prices = _prices(base)

    assert prices == sorted(prices), f"오름차순으로 정렬되지 않았습니다: {prices}"


def test_sort_price_high_to_low(logged_in):
    """가격 높은 순 정렬"""
    driver, base = logged_in

    base.select_by_value(InventoryPage.sort_select, "hilo")
    prices = _prices(base)

    assert prices == sorted(prices, reverse=True), f"내림차순으로 정렬되지 않았습니다: {prices}"


def test_sort_name_z_to_a(logged_in):
    """이름 역순 정렬"""
    driver, base = logged_in

    base.select_by_value(InventoryPage.sort_select, "za")
    names = base.get_texts(InventoryPage.item_name)

    assert names == sorted(names, reverse=True), f"역순 정렬되지 않았습니다: {names}"


def test_sort_does_not_change_item_count(logged_in):
    """
    정렬을 바꿔도 상품 수는 달라지면 안 된다.

    정렬 로직에 필터가 섞여 들어가는 결함을 잡기 위한 케이스.
    """
    driver, base = logged_in

    before = base.count(InventoryPage.item)

    for option in ("za", "lohi", "hilo", "az"):
        base.select_by_value(InventoryPage.sort_select, option)
        after = base.count(InventoryPage.item)
        assert after == before, f"'{option}' 정렬 후 상품 수가 {before} → {after} 로 변경되었습니다"
