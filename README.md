# saucedemo-selenium-pytest

[![UI Tests](https://github.com/lsj-qa/saucedemo-selenium-pytest/actions/workflows/test.yml/badge.svg)](https://github.com/lsj-qa/saucedemo-selenium-pytest/actions/workflows/test.yml)

Selenium + pytest 기반 웹 UI 자동화 테스트입니다.
데모 커머스 사이트 [saucedemo.com](https://www.saucedemo.com/) 을 대상으로
**로그인 → 상품 조회 → 장바구니 → 주문 완료**까지의 흐름을 24개 케이스로 검증합니다.

> **케이스를 왜 이렇게 골랐는지**는 [테스트 설계 문서](docs/테스트_설계.md) 에 정리했습니다.
> 리스크 기반 우선순위, 의도적으로 제외한 항목, 안정성 정책이 들어 있습니다.

---

## 구조

```
├── conftest.py          WebDriver 생성/종료, 공용 fixture, 실패 시 화면 저장
├── BaseAction.py        클릭·입력·조회·대기 등 공통 동작
├── ele_login.py         화면별 element 정의
├── ele_inventory.py
├── ele_cart.py
├── ele_checkout.py
├── test_Login.py        시나리오
├── test_Inventory.py
├── test_Cart.py
├── test_Checkout.py
└── docs/
    └── 테스트_설계.md    선정 근거 · 우선순위 · 제외 항목 · 안정성 정책
```

**element 정의를 테스트 로직과 분리(Page Object)** 했습니다.
화면이 개편되면 `ele_*.py` 만 수정하면 되고, 시나리오 파일은 건드리지 않습니다.

공통 동작은 `BaseAction` 으로 모았습니다. 대기 방식이나 예외 처리 정책을 바꿔야 할 때
테스트 파일 전체가 아니라 이 파일 하나만 고치면 됩니다.

---

## 실행

```bash
pip install -r requirements.txt

pytest                                  # 전체 실행
pytest test_Cart.py                     # 파일 단위
pytest test_Cart.py::test_add_to_cart   # 메소드 단위
pytest --headless                       # 브라우저 창 없이 (CI 용)
pytest --html=TestResult.html           # HTML 리포트 생성
```

**실행 범위를 나눠서** 돌릴 수 있습니다.

```bash
pytest -m smoke                         # 핵심 흐름 4건 (약 20초)
pytest -m regression                    # 전체 검증
pytest -n auto                          # 브라우저를 여러 개 띄워 나눠 실행
```

핵심 흐름이 깨진 빌드는 전체를 돌릴 이유가 없으므로, CI 는 **smoke 를 먼저 통과시킨 뒤**
전체를 실행합니다. 변경이 없는 날에도 하루 한 번 정기 실행합니다 —
코드가 그대로여도 대상 사이트가 바뀌면 깨지기 때문입니다.

Chrome 이 설치되어 있으면 드라이버는 Selenium 이 자동으로 준비합니다.

---

## 테스트 시나리오

### 로그인 (`test_Login.py`)

| 케이스 | 확인 내용 |
|---|---|
| `test_login_logout` | 로그인 후 상품 목록 진입, 로그아웃 후 복귀 |
| `test_login_rejected` **(6종)** | 차단 조건별로 **다른 사유**가 안내되는지 |
| `test_logout_then_back_button` | 로그아웃 후 뒤로가기로 이전 화면 접근 불가 |

차단 케이스는 조건마다 함수를 두지 않고 **데이터로 관리**합니다.

```python
REJECTED_LOGINS = [
    pytest.param(LOCKED_OUT_USER, PASSWORD, "locked out", id="잠긴계정"),
    pytest.param(STANDARD_USER, "wrong_password", "do not match", id="비밀번호불일치"),
    pytest.param("", PASSWORD, "Username is required", id="아이디미입력"),
    ...
]
```

조건이 늘어도 확인 절차는 하나만 유지됩니다. 새 조건은 이 표에 한 줄을 더하면 됩니다.

"들어가지지 않았다"만 확인하면 **사유가 뒤바뀌어도 통과**하므로, 안내 문구까지 대조합니다.

### 상품 목록 (`test_Inventory.py`)

| 케이스 | 확인 내용 |
|---|---|
| `test_product_list_displayed` | 목록 노출 |
| `test_sort` **(4종)** | 가격·이름 정렬 — **실제 값의 순서**로 검증 |
| `test_sort_does_not_change_item_count` | 정렬 변경이 상품 수에 영향을 주지 않음 |

정렬은 "정렬 옵션이 선택되었는지"를 확인하면 **정렬이 전혀 동작하지 않아도 통과**합니다.
그래서 실제 가격·이름 값을 꺼내 순서를 비교합니다.

### 장바구니 (`test_Cart.py`)

| 케이스 | 확인 내용 |
|---|---|
| `test_add_to_cart` | 담기 후 수량 배지·목록 반영 |
| `test_add_multiple_items` | 복수 상품 누적 |
| `test_remove_from_cart` | 제거 후 배지 소멸 |
| `test_cart_kept_after_navigation` | 화면 전환 후 담은 내용 유지 |
| `test_add_remove_repeat` | 담기·제거 반복 시 수량 정합성 |

### 주문 (`test_Checkout.py`)

| 케이스 | 확인 내용 |
|---|---|
| `test_checkout_complete` | 정보입력 → 확인 → 완료 전체 플로우 |
| `test_checkout_required_fields` | 필수값 누락 시 진행 차단 |
| `test_checkout_summary_matches_cart` | 확인 화면과 장바구니 내용 일치 |
| `test_checkout_cancel_keeps_cart` | 주문 취소 후 장바구니 유지 |
| `test_order_complete_clears_cart` | 주문 완료 후 장바구니 초기화 |

---

## 안정성 — 간헐적 실패를 잡은 과정

작성 직후 `test_add_remove_repeat` 가 **실행할 때마다 결과가 달라지는** 상태였습니다.
같은 코드로 어떤 때는 통과하고 어떤 때는 2회차에서 실패했습니다.

원인을 좁히기 위해 조건을 하나씩 바꿔가며 비교했습니다.

| 조건 | 결과 |
|---|---|
| 대기 없이 연속 실행 | 정상 |
| `time.sleep(3)` 후 실행 | 2회차 실패 |
| `not is_displayed(..., timeout=3)` 로 부재 확인 후 실행 | 2회차 실패 |
| 즉시 조회로 부재 확인 후 실행 | 정상 |

**부재를 타임아웃으로 확인하던 것이 원인**이었습니다.
`not is_displayed(...)` 로 "없음"을 확인하면 요소가 없을 때 지정한 시간만큼 기다렸다가
False 를 돌려주므로, 케이스마다 불필요한 유휴 시간이 쌓이고 그 뒤 클릭이 불안정해졌습니다.

부재 확인 전용 메소드 `is_absent()` 를 추가해 해결했습니다.
`invisibility_of_element_located` 는 요소가 이미 없으면 즉시 참을 반환하므로 유휴 시간이 생기지 않습니다.

```python
def is_absent(self, locator, timeout=5):
    try:
        WebDriverWait(self.driver, timeout, 0.3).until(
            EC.invisibility_of_element_located(locator)
        )
        return True
    except TimeoutException:
        return False
```

함께 적용한 것

- `click()` 은 클릭 가능 상태를 확인한 뒤 **요소를 다시 찾아서** 클릭합니다.
  대기 조건이 돌려준 요소를 그대로 누르면, 그 사이 화면이 다시 그려질 때
  이미 분리된 요소를 클릭하게 되어 아무 일도 일어나지 않습니다. 예외도 발생하지 않아 원인 파악이 어렵습니다.
- 반복 케이스는 결과를 바로 검증하지 않고 **버튼이 전환되었는지 먼저 확인**한 뒤 수량을 검증합니다.

수정 후 전체 20개 케이스를 3회 연속 실행하여 동일하게 통과하는 것을 확인했습니다.

### CI 에서 다시 드러난 같은 원인

로컬(Windows)에서 3회 연속 통과한 뒤 CI(리눅스)에 올리자 **20건 중 11건이 실패**했습니다.
실패 지점은 서로 달랐지만 내용은 하나로 모였습니다.

| 실패 케이스 | 실제로 일어난 일 |
|---|---|
| `test_add_to_cart` | 배지 수량까지는 정상 → 장바구니 아이콘 클릭이 무시됨 |
| `test_add_multiple_items` | 배지가 `2` 가 아닌 `1` → 두 번째 담기 클릭이 무시됨 |
| `test_add_remove_repeat` | 담기는 성공 → 제거 클릭이 무시됨 |
| `test_login_logout` | 로그아웃 링크가 끝내 노출되지 않음 → 햄버거 메뉴 클릭이 무시됨 |
| 주문 5건 | 공통 함수 안의 장바구니 아이콘 클릭이 무시됨 |

앞서 로컬에서 잡았던 것과 **같은 원인**이었습니다. 다만 로컬에서는 특정 케이스에서만
간헐적으로 드러났고, 사양이 낮은 CI 서버에서는 재현율이 올라가 여러 케이스에서 함께 드러났습니다.

로컬에서만 검증했다면 "환경 탓"으로 넘겼을 문제로, **실행 환경을 바꿔 재현율을 높인 것이
원인 확인에 도움이 된 사례**입니다.

근본적으로 고치기 위해, 클릭한 뒤 **결과가 반영되었는지까지 확인**하고
반영되지 않았으면 다시 클릭하도록 `click()` 을 바꿨습니다.

```python
base.click(Header.cart_link, until="cart.html")
base.click(InventoryPage.add_to_cart(item), until=InventoryPage.remove(item))
base.click(CartPage.remove(item), until_gone=Header.cart_badge)
```

- `until` — 이 요소가 나타나거나(locator) URL 이 이렇게 바뀌면(문자열) 반영된 것
- `until_gone` — 이 요소가 사라지면 반영된 것

호출부에 **"이 클릭이 성공했다면 무엇이 보여야 하는가"** 를 함께 적게 되므로,
실패했을 때 어느 단계에서 끊겼는지가 메시지에 그대로 남습니다.

마지막 재시도는 JavaScript 로 클릭합니다. 좌표를 계산해 그 위치에 이벤트를 보내는 방식이
아니라 요소에 직접 보내므로, 화면이 밀려 좌표가 어긋나는 상황에서도 영향을 받지 않습니다.

### 남은 4건 — 클릭이 아니라 입력이 문제였던 경우

위 수정으로 11건이 4건으로 줄었고, 남은 4건은 모두 주문 정보 입력 화면이었습니다.
이 중 한 건의 메시지가 원인을 가리켰습니다.

```
base.send_keys(CheckoutStepOne.first_name, FIRST_NAME)   ← 이름을 입력했는데
AssertionError: 예상과 다른 메시지: Error: First Name is required   ← 비어 있다고 나옴
```

**입력값이 지워지고 있었습니다.** 나머지 3건도 같은 원인으로, 세 칸이 모두 비어 있으니
필수값 검사에 걸려 다음 화면으로 넘어가지 못한 것이었습니다. 클릭은 정상이었습니다.

주문 정보 화면은 새 페이지로 이동합니다. URL 이 바뀐 직후에는 문서만 도착해 있고
화면을 그리는 스크립트는 아직 실행되기 전인데, 그 사이에 입력하면
**이어서 화면이 그려질 때 입력값이 초기값으로 되돌아갑니다.**

두 가지를 함께 고쳤습니다.

- 화면 이동 확인 시 URL 뿐 아니라 **그리기가 끝났는지**(`document.readyState`)까지 확인
- `send_keys()` 는 입력 후 **값이 실제로 남아 있는지 확인**하고, 지워졌으면 다시 입력

한 칸을 채우는 사이에 다른 칸이 지워지는 경우도 있어, 세 칸을 모두 채운 뒤
값이 그대로인지 한 번 더 확인하도록 했습니다.

`click()` 과 `send_keys()` 모두 **"했다"가 아니라 "반영되었다"를 기준으로** 바꾼 것이
공통점입니다.

### 실패한 순간의 화면을 남기도록

여기까지 오는 동안 원인이 두 번 바뀌었습니다. 로컬에서 재현되지 않는 실패를
로그만 보고 좁히는 데 한계가 있어, **실패 시점의 화면과 HTML 을 파일로 남기도록** 했습니다.

```python
@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    """테스트가 실패하면 그 시점의 화면과 HTML 을 파일로 남긴다."""
    report = yield
    if report.when == "call" and report.failed:
        drv = item.funcargs.get("driver")
        ...
```

CI 에서는 실패했을 때만 `failure-screenshots` 라는 이름으로 내려받을 수 있게 했습니다.
다른 사람이 이 저장소를 받아 실행하다 실패해도, 로그와 함께 화면을 그대로 확인할 수 있습니다.

---

## 케이스 설계 관점

정상 동작 확인에 그치지 않고, **정상 흐름에서 벗어나는 경로**를 함께 두었습니다.

- **되돌리는 동작** — 주문 취소, 장바구니 제거처럼 상태를 되돌릴 때 데이터가 유실되지 않는지
- **반복 조작** — 담기·제거를 여러 번 반복했을 때 수량이 어긋나지 않는지
- **화면 전환 후 상태** — 목록 ↔ 장바구니를 오갈 때 담은 내용이 유지되는지
- **이탈 후 재진입** — 로그아웃 후 뒤로가기로 이전 화면에 접근되지 않는지
- **화면 표시가 아닌 값** — 정렬은 UI 상태가 아니라 실제 가격·이름 순서를 비교

---

## 참고

테스트 계정은 saucedemo.com 첫 화면에 공개된 데모 계정입니다.
