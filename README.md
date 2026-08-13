# saucedemo-selenium-pytest

[![UI Tests](https://github.com/lsj-qa/saucedemo-selenium-pytest/actions/workflows/test.yml/badge.svg)](https://github.com/lsj-qa/saucedemo-selenium-pytest/actions/workflows/test.yml)

Selenium + pytest 기반 웹 UI 자동화 테스트입니다.
데모 커머스 사이트 [saucedemo.com](https://www.saucedemo.com/) 을 대상으로
**로그인 → 상품 조회 → 장바구니 → 주문 완료**까지의 흐름을 검증합니다.

---

## 구조

```
├── conftest.py          WebDriver 생성/종료, 공용 fixture
├── BaseAction.py        클릭·입력·조회·대기 등 공통 동작
├── ele_login.py         화면별 element 정의
├── ele_inventory.py
├── ele_cart.py
├── ele_checkout.py
├── test_Login.py        시나리오
├── test_Inventory.py
├── test_Cart.py
└── test_Checkout.py
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

Chrome 이 설치되어 있으면 드라이버는 Selenium 이 자동으로 준비합니다.

---

## 테스트 시나리오

### 로그인 (`test_Login.py`)

| 케이스 | 확인 내용 |
|---|---|
| `test_login_logout` | 로그인 후 상품 목록 진입, 로그아웃 후 복귀 |
| `test_login_locked_out_user` | 잠긴 계정 차단 및 안내 문구 |
| `test_login_wrong_password` | 비밀번호 불일치 시 진입 차단 |
| `test_login_empty_input` | 필수값 미입력 안내 |
| `test_logout_then_back_button` | 로그아웃 후 뒤로가기로 이전 화면 접근 불가 |

### 상품 목록 (`test_Inventory.py`)

| 케이스 | 확인 내용 |
|---|---|
| `test_product_list_displayed` | 목록 노출 |
| `test_sort_price_low_to_high` | 가격 오름차순 — **실제 값의 순서**로 검증 |
| `test_sort_price_high_to_low` | 가격 내림차순 |
| `test_sort_name_z_to_a` | 이름 역순 |
| `test_sort_does_not_change_item_count` | 정렬 변경이 상품 수에 영향을 주지 않음 |

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
