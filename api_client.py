"""
API 호출 공통 처리

테스트 코드가 HTTP 세부사항을 직접 다루지 않도록 한 단계 감쌌습니다.
UI 쪽 BaseAction 과 같은 역할로, 주소·헤더·인증·재시도 정책을 이 파일에만 둡니다.

대상: https://restful-booker.herokuapp.com (API 테스트 연습용 공개 서비스)
"""
import requests

BASE_URL = "https://restful-booker.herokuapp.com"

# 공개 연습 서비스에 게시된 계정입니다.
ADMIN_USER = "admin"
ADMIN_PASSWORD = "password123"

TIMEOUT = 30

# 서버가 깨어나는 중이거나 앞단이 일시적으로 끊길 때만 다시 시도한다.
# 4xx 나 500 은 응답이 돌아온 것이므로 다시 시도하지 않는다.
# (결과를 확인하지 않는 재시도는 실패를 감출 뿐이다 — docs/테스트_설계.md 안정성 정책)
RETRY_STATUS = (502, 503, 504)
RETRY_COUNT = 3


class BookingApi:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    # ---------- 공통 ----------

    def _request(self, method, path, **kwargs):
        """일시적인 연결 실패에만 다시 시도한다."""
        url = f"{BASE_URL}{path}"
        last_error = None

        for attempt in range(1, RETRY_COUNT + 1):
            try:
                response = self.session.request(method, url, timeout=TIMEOUT, **kwargs)
            except requests.RequestException as exc:
                last_error = exc
                continue

            if response.status_code in RETRY_STATUS and attempt < RETRY_COUNT:
                continue
            return response

        raise AssertionError(f"{method} {path} 요청이 실패했습니다: {last_error}")

    # ---------- 인증 ----------

    def issue_token(self, username=ADMIN_USER, password=ADMIN_PASSWORD):
        """인증 토큰 발급. 응답 전체를 돌려주어 실패 케이스도 검증할 수 있게 한다."""
        return self._request("POST", "/auth", json={
            "username": username,
            "password": password,
        })

    @staticmethod
    def _auth(token):
        """이 서비스는 토큰을 쿠키로 받는다."""
        return {"Cookie": f"token={token}"}

    # ---------- 예약 ----------

    def create(self, payload):
        return self._request("POST", "/booking", json=payload)

    def get(self, booking_id):
        return self._request("GET", f"/booking/{booking_id}")

    def get_ids(self):
        return self._request("GET", "/booking")

    def update(self, booking_id, payload, token=None):
        """token 을 넘기지 않으면 인증 없이 호출한다. 권한 검증에 사용."""
        headers = self._auth(token) if token else {}
        return self._request("PUT", f"/booking/{booking_id}", json=payload, headers=headers)

    def update_partial(self, booking_id, payload, token=None):
        headers = self._auth(token) if token else {}
        return self._request("PATCH", f"/booking/{booking_id}", json=payload, headers=headers)

    def delete(self, booking_id, token=None):
        headers = self._auth(token) if token else {}
        return self._request("DELETE", f"/booking/{booking_id}", headers=headers)
