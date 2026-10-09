from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

PASTA = Path(__file__).parent
PORTA = 3456


class Resposta:
    def __init__(self, status_code: int, texto: str) -> None:
        self.status_code = status_code
        self.text = texto

    def json(self):
        return json.loads(self.text)


class Cliente:
    def __init__(self, base_url: str, timeout: float = 10) -> None:
        self.base_url = base_url
        self.timeout = timeout

    def post(self, path: str, json: dict | None = None) -> Resposta:
        import json as _json

        req = urllib.request.Request(
            self.base_url + path,
            data=_json.dumps(json or {}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return Resposta(r.status, r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:  # 4xx / 5xx também são respostas
            return Resposta(e.code, e.read().decode("utf-8"))


@pytest.fixture(scope="session")
def base_url():
    url_externa = os.environ.get("BASE_URL")
    if url_externa:
        yield url_externa.rstrip("/")
        return

    url = f"http://localhost:{PORTA}"
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "bentoml",
            "serve",
            "service:Recomendador",
            "--port",
            str(PORTA),
        ],
        cwd=PASTA,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        limite = time.time() + 90
        while time.time() < limite:
            if proc.poll() is not None:
                pytest.fail(
                    "O servidor BentoML encerrou antes de ficar pronto "
                    "(o modelo 'recomendador:latest' existe no bento store?)"
                )
            try:
                with urllib.request.urlopen(f"{url}/readyz", timeout=2) as r:
                    if r.status == 200:
                        break
            except (urllib.error.URLError, OSError):
                pass
            time.sleep(1)
        else:
            pytest.fail("Timeout esperando o servidor BentoML subir")
        yield url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.fixture
def client(base_url):
    return Cliente(base_url)


def test_home(client):
    r = client.post("/v1/recommendations/home", json={"user_id": "u_83921", "limit": 3})
    assert r.status_code == 200
    body = r.json()
    assert body["fallback_used"] is False
    assert len(body["items"]) > 0
    for item in body["items"]:
        assert {"product_id", "artisan_id", "score", "reason"} <= item.keys()


def test_seller(client):
    r = client.post(
        "/v1/recommendations/seller", json={"artisan_id": "a_207", "limit": 3}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["artisan_id"] == "a_207"
    assert body["resumo_vendas"]["total_vendas"] > 0
    assert len(body["tags_com_mais_sucesso"]) > 0
    faixa = body["preco_sugerido"]["faixa_sugerida"]
    assert faixa["min"] < faixa["max"]


def test_events(client):
    r = client.post(
        "/v1/events",
        json={
            "user_id": "u_83921",
            "event_type": "click",
            "product_id": "p_1042",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "accepted"
    assert body["event_id"].startswith("evt_")
