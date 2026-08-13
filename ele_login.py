"""로그인 화면 element 정의"""
from selenium.webdriver.common.by import By


class LoginPage:
    username = (By.ID, "user-name")
    password = (By.ID, "password")
    login_button = (By.ID, "login-button")
    error_message = (By.CSS_SELECTOR, "h3[data-test='error']")
    error_close = (By.CSS_SELECTOR, ".error-button")
    logo = (By.CLASS_NAME, "login_logo")
