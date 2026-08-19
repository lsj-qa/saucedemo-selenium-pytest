"""
API 시나리오 — 예약 생성 / 조회 / 수정 / 삭제

UI 와 같은 관점으로 케이스를 뽑았습니다.
정상 동작 확인에 그치지 않고 **권한, 되돌리는 동작, 데이터 정합성**을 함께 봅니다.

대상: https://restful-booker.herokuapp.com
"""
import uuid

import pytest

# 예약 하나가 가져야 하는 필드. 응답 구조가 바뀌면 여기서 걸린다.
REQUIRED_FIELDS = ("firstname", "lastname", "totalprice", "depositpaid", "bookingdates")


@pytest.fixture()
def booking_payload():
    """
    케이스마다 다른 값을 쓴다.

    같은 값을 공유하면 다른 케이스가 만든 데이터와 섞여, 실패했을 때
    무엇이 원인인지 구분되지 않는다.
    """
    unique = uuid.uuid4().hex[:8]
    return {
        "firstname": f"Sujin_{unique}",
        "lastname": "Lee",
        "totalprice": 150,
        "depositpaid": True,
        "bookingdates": {"checkin": "2026-09-01", "checkout": "2026-09-05"},
        "additionalneeds": "Breakfast",
    }


# ---------- 인증 ----------

@pytest.mark.api
@pytest.mark.smoke
def test_issue_token(api):
    """올바른 계정으로 인증하면 토큰이 발급되어야 한다"""
    response = api.issue_token()

    assert response.status_code == 200, f"예상과 다른 응답: {response.status_code}"
    assert response.json().get("token"), f"토큰이 발급되지 않았습니다: {response.text}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.parametrize("username, password", [
    pytest.param("admin", "wrong_password", id="비밀번호불일치"),
    pytest.param("wrong_user", "password123", id="없는계정"),
    pytest.param("", "", id="미입력"),
])
def test_issue_token_rejected(api, username, password):
    """잘못된 계정으로는 토큰이 발급되면 안 된다"""
    response = api.issue_token(username, password)

    body = response.json()
    assert "token" not in body, f"잘못된 계정에 토큰이 발급되었습니다: {body}"
    assert body.get("reason"), f"거부 사유가 없습니다: {body}"


# ---------- 생성 · 조회 ----------

@pytest.mark.api
@pytest.mark.smoke
def test_create_and_read(api, booking):
    """
    생성한 예약을 조회하면 보낸 값과 같아야 한다.

    생성 응답만 확인하면 '응답은 정상인데 저장은 안 되는' 결함을 놓친다.
    그래서 다시 조회해 저장된 값을 확인한다.
    """
    booking_id, payload = booking

    response = api.get(booking_id)
    assert response.status_code == 200, f"조회 실패: {response.status_code}"

    saved = response.json()
    for field in REQUIRED_FIELDS:
        assert field in saved, f"응답에 '{field}' 가 없습니다: {saved}"

    assert saved["firstname"] == payload["firstname"]
    assert saved["totalprice"] == payload["totalprice"]
    assert saved["bookingdates"]["checkin"] == payload["bookingdates"]["checkin"]


@pytest.mark.api
@pytest.mark.regression
def test_read_unknown_id_returns_not_found(api):
    """존재하지 않는 예약을 조회하면 없음으로 응답해야 한다"""
    response = api.get(99999999)

    assert response.status_code == 404, f"예상과 다른 응답: {response.status_code}"


@pytest.mark.api
@pytest.mark.regression
def test_create_rejects_incomplete_payload(api):
    """
    필수값이 빠지면 생성이 거부되어야 한다.

    참고 — 이 서비스는 400 이 아니라 500 을 돌려준다.
    잘못된 요청은 클라이언트 오류(4xx)로 구분되어야 하므로 실무라면 결함으로 등록할 부분이다.
    여기서는 '거부되었는지' 를 기준으로 검증하고, 상태 코드는 위 내용으로 남긴다.
    """
    response = api.create({"firstname": "Sujin"})

    assert response.status_code >= 400, \
        f"필수값이 빠졌는데 생성되었습니다: {response.status_code} {response.text}"


# ---------- 권한 ----------

@pytest.mark.api
@pytest.mark.regression
def test_update_requires_auth(api, booking):
    """
    인증 없이 수정하면 거부되고, **저장된 값도 그대로여야 한다**.

    거부 응답만 확인하면 '응답은 막았는데 데이터는 바뀐' 경우를 놓친다.
    권한 검증은 응답과 상태를 함께 봐야 한다.
    """
    booking_id, payload = booking

    response = api.update(booking_id, {**payload, "firstname": "침입자"})
    assert response.status_code in (401, 403), f"인증 없이 수정이 허용되었습니다: {response.status_code}"

    saved = api.get(booking_id).json()
    assert saved["firstname"] == payload["firstname"], "인증이 거부되었는데 값이 변경되었습니다"


@pytest.mark.api
@pytest.mark.regression
def test_delete_requires_auth(api, booking):
    """인증 없이 삭제하면 거부되고, 예약은 남아 있어야 한다"""
    booking_id, _ = booking

    response = api.delete(booking_id)
    assert response.status_code in (401, 403), f"인증 없이 삭제가 허용되었습니다: {response.status_code}"

    assert api.get(booking_id).status_code == 200, "인증이 거부되었는데 삭제되었습니다"


# ---------- 수정 · 삭제 ----------

@pytest.mark.api
@pytest.mark.regression
def test_partial_update_keeps_other_fields(api, token, booking):
    """
    일부만 수정하면 나머지 값은 유지되어야 한다.

    부분 수정에서 보내지 않은 필드가 초기화되는 결함을 잡기 위한 케이스.
    """
    booking_id, payload = booking

    response = api.update_partial(booking_id, {"firstname": "Changed"}, token)
    assert response.status_code == 200, f"부분 수정 실패: {response.status_code}"

    saved = api.get(booking_id).json()
    assert saved["firstname"] == "Changed", "수정한 값이 반영되지 않았습니다"
    assert saved["lastname"] == payload["lastname"], "보내지 않은 값이 변경되었습니다"
    assert saved["totalprice"] == payload["totalprice"], "보내지 않은 값이 변경되었습니다"


@pytest.mark.api
@pytest.mark.regression
def test_delete_then_read_returns_not_found(api, token, booking_payload):
    """
    삭제한 예약은 조회되지 않아야 한다.

    삭제 응답만 보면 '지웠다고 했는데 남아 있는' 경우를 놓치므로 다시 조회한다.
    이 서비스는 삭제 성공에 201 을 돌려주어, 상태 코드가 아니라 조회 결과로 판정한다.
    """
    created = api.create(booking_payload)
    booking_id = created.json()["bookingid"]

    api.delete(booking_id, token)

    assert api.get(booking_id).status_code == 404, "삭제했는데 조회됩니다"
