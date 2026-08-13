"""상품 목록 / 공통 헤더 element 정의"""
from selenium.webdriver.common.by import By


class InventoryPage:
    title = (By.CLASS_NAME, "title")
    item = (By.CLASS_NAME, "inventory_item")
    item_name = (By.CLASS_NAME, "inventory_item_name")
    item_price = (By.CLASS_NAME, "inventory_item_price")
    sort_select = (By.CLASS_NAME, "product_sort_container")

    # 상품 ID 를 받아 버튼 locator 를 만든다.
    # 상품이 늘어나도 element 파일을 고치지 않아도 되도록 함수로 둠.
    @staticmethod
    def add_to_cart(item_id):
        return (By.ID, f"add-to-cart-{item_id}")

    @staticmethod
    def remove(item_id):
        return (By.ID, f"remove-{item_id}")


class Header:
    """모든 화면 상단에 공통으로 존재하는 영역"""
    cart_link = (By.CLASS_NAME, "shopping_cart_link")
    cart_badge = (By.CLASS_NAME, "shopping_cart_badge")
    burger_menu = (By.ID, "react-burger-menu-btn")
    logout_link = (By.ID, "logout_sidebar_link")
    reset_app_link = (By.ID, "reset_sidebar_link")


# 테스트에서 사용하는 상품 ID
ITEM_BACKPACK = "sauce-labs-backpack"
ITEM_BIKE_LIGHT = "sauce-labs-bike-light"
ITEM_TSHIRT = "sauce-labs-bolt-t-shirt"
