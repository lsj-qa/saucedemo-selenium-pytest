"""주문(체크아웃) 화면 element 정의 — 정보입력 / 확인 / 완료 3단계"""
from selenium.webdriver.common.by import By


class CheckoutStepOne:
    """배송 정보 입력"""
    first_name = (By.ID, "first-name")
    last_name = (By.ID, "last-name")
    postal_code = (By.ID, "postal-code")
    continue_button = (By.ID, "continue")
    cancel_button = (By.ID, "cancel")
    error_message = (By.CSS_SELECTOR, "h3[data-test='error']")


class CheckoutStepTwo:
    """주문 내역 확인"""
    title = (By.CLASS_NAME, "title")
    item = (By.CLASS_NAME, "cart_item")
    item_name = (By.CLASS_NAME, "inventory_item_name")
    subtotal = (By.CLASS_NAME, "summary_subtotal_label")
    tax = (By.CLASS_NAME, "summary_tax_label")
    total = (By.CLASS_NAME, "summary_total_label")
    finish_button = (By.ID, "finish")
    cancel_button = (By.ID, "cancel")


class CheckoutComplete:
    """주문 완료"""
    header = (By.CLASS_NAME, "complete-header")
    text = (By.CLASS_NAME, "complete-text")
    back_home = (By.ID, "back-to-products")
