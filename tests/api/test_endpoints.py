"""Contract tests for the two write endpoints.

Every request here is invalid on purpose: the server must reject it before it writes
anything, so the suite can run against production without leaving data behind.
"""

import httpx
import pytest

pytestmark = pytest.mark.api


@pytest.mark.parametrize("endpoint", ["/api/feedback", "/api/analytics"])
def test_rejects_get(http: httpx.Client, endpoint: str) -> None:
    assert http.get(endpoint).status_code == 405


@pytest.mark.parametrize("endpoint", ["/api/feedback", "/api/analytics"])
def test_rejects_malformed_json(http: httpx.Client, endpoint: str) -> None:
    response = http.post(
        endpoint, content=b"{not json", headers={"content-type": "application/json"}
    )
    assert response.status_code == 400
    assert response.json() == {"erro": "corpo inválido"}


@pytest.mark.parametrize(
    "body",
    [
        pytest.param({"slug": "no-such-guide", "util": True}, id="unknown-slug"),
        pytest.param({"slug": "../../etc/passwd", "util": True}, id="path-traversal-slug"),
        pytest.param({"slug": "sem-filtro", "util": "yes"}, id="util-not-boolean"),
        pytest.param({"slug": "sem-filtro"}, id="util-missing"),
        pytest.param([], id="array-body"),
    ],
)
def test_feedback_rejects_invalid_body(http: httpx.Client, body: object) -> None:
    response = http.post("/api/feedback", json=body)
    assert response.status_code == 400
    assert response.json() == {"erro": "pedido inválido"}


@pytest.mark.parametrize(
    "body",
    [
        pytest.param({"path": "sobre"}, id="path-without-slash"),
        pytest.param({"path": ""}, id="empty-path"),
        pytest.param({"path": "/" + "a" * 200}, id="path-over-200-chars"),
        pytest.param({"path": 42}, id="path-not-string"),
        pytest.param({"path": "/sobre", "ev": "no-such-event"}, id="unknown-event"),
        pytest.param({"path": "/sobre", "ev": "vista", "vid": "x" * 65}, id="vid-too-long"),
        pytest.param({"path": "/sobre", "ev": "vista", "vid": "<script>"}, id="vid-bad-chars"),
    ],
)
def test_analytics_rejects_invalid_body(http: httpx.Client, body: object) -> None:
    response = http.post("/api/analytics", json=body)
    assert response.status_code == 400
    assert response.json() == {"erro": "pedido inválido"}
