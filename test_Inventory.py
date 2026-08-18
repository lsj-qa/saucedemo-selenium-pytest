"""
상품 목록 시나리오

- 목록 노출 확인
- 정렬 기능이 실제로 정렬된 결과를 내는지 값으로 검증
"""
import pytest

from ele_inventory import InventoryPage

# 정렬 조건. 화면에 선택된 항목이 아니라 **실제 값의 순서**로 확인한다.
# 정렬은 선택지가 늘어나기 쉬운 기능이라 절차를 하나만 두고 조건만 추가한다.
SORT_CASES = [
    pytest.param("lohi", "price", False, id="가격_낮은순"),
    pytest.param("hilo", "price", True, id="가격_높은순"),
    pytest.param("az", "name", False, id="이름_오름차순"),
    pytest.param("za", "name", True, id="이름_내림차순"),
]


def _prices(base):
    """'$29.99' 형태의 텍스트를 float 리스트로 변환"""
    return [float(t.replace("$", "")) for t in base.get_texts(InventoryPage.item_price)]


@pytest.mark.smoke
def test_product_list_displayed(logged_in):
    """로그인 후 상품 목록이 노출되고 항목 수가 0보다 커야 한다"""
    driver, base = logged_in

    assert base.get_text(InventoryPage.title) == "Products"
    assert base.count(InventoryPage.item) > 0, "상품이 하나도 노출되지 않았습니다"


@pytest.mark.regression
@pytest.mark.parametrize("option, field, reverse", SORT_CASES)
def test_sort(logged_in, option, field, reverse):
    """정렬 결과를 화면 표시가 아니라 실제 값의 순서로 확인한다"""
    driver, base = logged_in

    base.select_by_value(InventoryPage.sort_select, option)

    if field == "price":
        values = _prices(base)
    else:
        values = base.get_texts(InventoryPage.item_name)

    assert values == sorted(values, reverse=reverse), \
        f"'{option}' 정렬 결과가 순서에 맞지 않습니다: {values}"


@pytest.mark.regression
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
