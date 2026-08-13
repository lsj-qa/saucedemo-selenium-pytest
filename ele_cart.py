"""장바구니 화면 element 정의"""
from selenium.webdriver.common.by import By


class CartPage:
    title = (By.CLASS_NAME, "title")
    item = (By.CLASS_NAME, "cart_item")
    item_name = (By.CLASS_NAME, "inventory_item_name")
    item_quantity = (By.CLASS_NAME, "cart_quantity")
    continue_shopping = (By.ID, "continue-shopping")
    checkout = (By.ID, "checkout")

    @staticmethod
    def remove(item_id):
        return (By.ID, f"remove-{item_id}")
