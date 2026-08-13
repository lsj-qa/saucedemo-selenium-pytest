"""
공통 동작 정의 — 클릭, 입력, 텍스트 조회, 대기 등

테스트 코드가 Selenium API 를 직접 호출하지 않도록 한 단계 감쌌습니다.
대기 방식이나 예외 처리를 바꿔야 할 때 이 파일만 수정하면 됩니다.
"""
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


class BaseAction:
    def __init__(self, driver, timeout=10):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout, poll_frequency=0.5)

    # ---------- 조회 ----------

    def find(self, locator):
        """요소가 나타날 때까지 대기 후 반환."""
        return self.wait.until(EC.presence_of_element_located(locator))

    def find_all(self, locator):
        """조건에 맞는 요소 전체를 반환. 없으면 빈 리스트."""
        try:
            self.wait.until(EC.presence_of_element_located(locator))
        except TimeoutException:
            return []
        return self.driver.find_elements(*locator)

    def get_text(self, locator):
        try:
            return self.find(locator).text
        except TimeoutException:
            raise AssertionError(f"요소를 찾을 수 없습니다: {locator}")

    def get_texts(self, locator):
        """목록 요소의 텍스트를 순서대로 반환. 정렬 검증 등에 사용."""
        return [el.text for el in self.find_all(locator)]

    def count(self, locator):
        return len(self.find_all(locator))

    def is_displayed(self, locator, timeout=5):
        """노출될 때까지 대기. 끝내 안 보이면 False (예외 발생시키지 않음)."""
        try:
            WebDriverWait(self.driver, timeout, poll_frequency=0.3).until(
                EC.visibility_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False

    def is_absent(self, locator, timeout=5):
        """
        사라질 때까지 대기. 이미 없으면 즉시 True.

        `not is_displayed(...)` 로 부재를 확인하면 요소가 없을 때 타임아웃만큼
        기다렸다가 False 를 받게 되어, 케이스마다 불필요한 유휴 시간이 쌓인다.
        부재 확인은 이 메소드를 사용한다.
        """
        try:
            WebDriverWait(self.driver, timeout, poll_frequency=0.3).until(
                EC.invisibility_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False

    # ---------- 조작 ----------

    def click(self, locator):
        """
        클릭 불가 시 테스트 실패 처리.

        대기 조건이 돌려준 요소를 그대로 클릭하면, 그 사이 화면이 다시 그려질 때
        이미 분리된 요소를 누르게 되어 클릭이 조용히 무시된다.
        (SPA 에서 흔한 현상으로, 예외도 발생하지 않아 원인 파악이 어렵다.)

        그래서 클릭 가능 상태를 확인한 뒤 **다시 찾아서** 클릭한다.
        """
        for attempt in (1, 2, 3):
            try:
                self.wait.until(EC.element_to_be_clickable(locator))
                self.driver.find_element(*locator).click()
                return
            except StaleElementReferenceException:
                continue
            except TimeoutException:
                raise AssertionError(f"클릭할 수 없습니다: {locator}")
        raise AssertionError(f"요소 참조가 계속 끊깁니다: {locator}")

    def click_pass(self, locator):
        """요소가 없어도 다음 단계로 진행. (선택적으로 노출되는 요소용)"""
        try:
            WebDriverWait(self.driver, 3, poll_frequency=0.5).until(
                EC.element_to_be_clickable(locator)
            ).click()
        except TimeoutException:
            pass

    def send_keys(self, locator, text):
        el = self.wait.until(EC.visibility_of_element_located(locator))
        el.clear()
        el.send_keys(text)

    def clear(self, locator):
        self.find(locator).clear()

    def select_by_value(self, locator, value):
        """select 요소에서 value 기준으로 옵션 선택."""
        Select(self.find(locator)).select_by_value(value)

    def scroll_to(self, locator):
        el = self.find(locator)
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        return el

    # ---------- 대기 ----------

    def wait_url_contains(self, part):
        """URL 이 바뀔 때까지 대기. 페이지 전환 검증에 사용."""
        try:
            self.wait.until(EC.url_contains(part))
        except TimeoutException:
            raise AssertionError(
                f"URL 에 '{part}' 가 포함되지 않았습니다. 현재: {self.driver.current_url}"
            )

    def wait_text(self, locator, text):
        try:
            self.wait.until(EC.text_to_be_present_in_element(locator, text))
        except TimeoutException:
            raise AssertionError(f"'{text}' 가 표시되지 않았습니다: {locator}")
