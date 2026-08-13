"""
공통 동작 정의 — 클릭, 입력, 텍스트 조회, 대기 등

테스트 코드가 Selenium API 를 직접 호출하지 않도록 한 단계 감쌌습니다.
대기 방식이나 예외 처리를 바꿔야 할 때 이 파일만 수정하면 됩니다.
"""
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


class BaseAction:
    # CI 서버는 로컬보다 3배가량 느려, 로컬 기준으로 맞추면 대기가 부족하다.
    def __init__(self, driver, timeout=15):
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

    def click(self, locator, until=None, until_gone=None):
        """
        클릭한 뒤 **실제로 반영되었는지까지 확인**한다.

        화면이 다시 그려지는 시점과 클릭이 겹치면, 이미 분리된 요소를 누르게 되어
        클릭이 조용히 무시된다. 예외가 발생하지 않으므로 그 자리에서는 통과한 것처럼
        보이고, 한참 뒤 엉뚱한 단계에서 실패한다. (SPA 에서 흔한 현상)

        그래서 클릭 가능 상태를 확인한 뒤 다시 찾아서 클릭하고,
        기대한 변화가 나타나지 않으면 최대 3회까지 다시 클릭한다.

        until      클릭이 반영되었다고 볼 조건
                     - locator 튜플 : 그 요소가 나타나면 반영된 것
                     - 문자열       : URL 에 그 문자열이 포함되면 반영된 것
        until_gone 그 요소가 사라지면 반영된 것으로 본다

        마지막 시도는 JavaScript 로 클릭한다. 좌표를 계산해 그 위치에 이벤트를
        보내는 방식이 아니라 요소에 직접 보내므로, 화면이 밀려 좌표가 어긋나는
        상황에서도 영향을 받지 않는다.
        """
        for attempt in (1, 2, 3):
            try:
                self.wait.until(EC.element_to_be_clickable(locator))
                element = self.driver.find_element(*locator)
                if attempt < 3:
                    element.click()
                else:
                    self.driver.execute_script("arguments[0].click();", element)
            except (StaleElementReferenceException, ElementClickInterceptedException):
                continue
            except TimeoutException:
                # 클릭이 이미 반영되어 요소 자체가 바뀐 경우까지 실패로 보지 않는다.
                if self._is_applied(until, until_gone, timeout=1):
                    return
                raise AssertionError(f"클릭할 수 없습니다: {locator}")

            if self._is_applied(until, until_gone):
                return

        raise AssertionError(
            f"클릭이 반영되지 않았습니다: {locator} "
            f"(확인 조건: until={until}, until_gone={until_gone})"
        )

    def _is_applied(self, until, until_gone, timeout=5):
        """클릭 결과가 화면에 반영되었는지 확인. 확인 조건이 없으면 그대로 통과."""
        if until is None and until_gone is None:
            return True

        wait = WebDriverWait(self.driver, timeout, poll_frequency=0.3)
        try:
            if until is not None:
                if isinstance(until, str):
                    wait.until(EC.url_contains(until))
                    # URL 이 바뀐 시점에는 화면이 아직 그려지는 중일 수 있다.
                    # 이때 입력하면 이어서 화면이 그려질 때 입력값이 지워진다.
                    wait.until(
                        lambda d: d.execute_script("return document.readyState") == "complete"
                    )
                else:
                    wait.until(EC.visibility_of_element_located(until))
            if until_gone is not None:
                wait.until(EC.invisibility_of_element_located(until_gone))
            return True
        except TimeoutException:
            return False
        except StaleElementReferenceException:
            return False

    def click_pass(self, locator):
        """요소가 없어도 다음 단계로 진행. (선택적으로 노출되는 요소용)"""
        try:
            WebDriverWait(self.driver, 3, poll_frequency=0.5).until(
                EC.element_to_be_clickable(locator)
            ).click()
        except TimeoutException:
            pass

    def send_keys(self, locator, text):
        """
        입력한 뒤 **값이 실제로 남아 있는지까지 확인**한다.

        화면이 다 그려지기 전에 입력하면, 이어서 화면이 그려질 때 입력값이
        초기값으로 되돌아간다. 이때도 예외는 발생하지 않아 입력에 성공한 것처럼
        보이고, '필수값 누락' 같은 엉뚱한 결과로 뒤늦게 드러난다.
        """
        for attempt in (1, 2, 3):
            try:
                element = self.wait.until(EC.element_to_be_clickable(locator))
                element.clear()
                element.send_keys(text)
            except StaleElementReferenceException:
                continue
            except TimeoutException:
                raise AssertionError(f"입력할 수 없습니다: {locator}")

            if self.get_value(locator) == text:
                return

        raise AssertionError(f"입력값이 유지되지 않습니다: {locator} = '{text}'")

    def get_value(self, locator):
        """입력 요소에 실제로 담겨 있는 값. 화면에 보이는 텍스트가 아니다."""
        try:
            return self.find(locator).get_attribute("value")
        except (TimeoutException, StaleElementReferenceException):
            return None

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
