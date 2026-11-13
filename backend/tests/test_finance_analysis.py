import asyncio
import json

import app.main as module


def _sample_pages():
    return [
        {
            "page": 1,
            "text": (
                "This paper studies whether monetary policy shocks affect bank lending. "
                "We use a panel of 50 banks from 2001 to 2020. The dependent variable is loan growth."
            ),
        },
        {
            "page": 2,
            "text": (
                "The estimated coefficient is -0.12 and statistically significant at the 5 percent level. "
                "The result remains robust when we exclude crisis years."
            ),
        },
    ]


def _sample_model_output():
    return {
        "bibliographic": {
            "title": "Monetary Policy and Bank Lending",
            "authors": ["A. Researcher"],
            "year": "2024",
            "venue": "Journal of Finance",
            "doi": "확인 불가",
            "evidence": [{"page": 1, "quote": "This paper studies whether monetary policy shocks affect bank lending."}],
        },
        "summary": "통화정책 충격과 은행 대출 증가율의 관계를 분석한다.",
        "research_question": "통화정책 충격은 은행 대출에 어떤 영향을 미치는가?",
        "research_question_evidence": [
            {"page": 1, "quote": "This paper studies whether monetary policy shocks affect bank lending."}
        ],
        "hypotheses": [
            {"text": "긴축적 충격은 대출 증가율을 낮춘다.", "evidence": [
                {"page": 2, "quote": "The estimated coefficient is -0.12 and statistically significant at the 5 percent level."}
            ]}
        ],
        "contributions": [
            {"text": "은행 수준 패널 자료를 사용한다.", "evidence": [
                {"page": 1, "quote": "We use a panel of 50 banks from 2001 to 2020."}
            ]}
        ],
        "methodology": {
            "design": "은행 패널 분석",
            "sample": "50개 은행",
            "period": "2001~2020년",
            "data_sources": ["은행 패널 자료"],
            "variables": [
                {"name": "loan growth", "role": "종속변수", "definition": "대출 증가율",
                 "evidence": [{"page": 1, "quote": "The dependent variable is loan growth."}]}
            ],
            "empirical_strategy": "패널 회귀분석",
            "identification_strategy": "확인 불가",
            "equations": [],
            "evidence": [{"page": 1, "quote": "We use a panel of 50 banks from 2001 to 2020."}],
        },
        "findings": [
            {
                "claim": "추정계수는 -0.12이며 5% 수준에서 통계적으로 유의하다.",
                "direction": "negative",
                "estimate": "-0.12",
                "statistical_significance": "5% level",
                "evidence": [{"page": 2, "quote": "The estimated coefficient is -0.12 and statistically significant at the 5 percent level."}],
            },
            {
                "claim": "원문에 없는 가짜 결과",
                "direction": "positive",
                "estimate": "9.99",
                "statistical_significance": "1%",
                "evidence": [{"page": 2, "quote": "This fabricated quotation is not in the source paper."}],
            },
        ],
        "robustness_checks": [
            {"test": "위기 연도 제외", "result": "결과가 유지됨", "evidence": [
                {"page": 2, "quote": "The result remains robust when we exclude crisis years."}
            ]},
            {"test": "가짜 강건성 검사", "result": "통과", "evidence": []},
        ],
        "limitations": [
            {"description": "표본은 50개 은행으로 한정된다.", "evidence": [
                {"page": 1, "quote": "We use a panel of 50 banks from 2001 to 2020."}
            ]}
        ],
        "implications": [
            {"text": "통화정책 충격과 은행 대출 경로를 함께 검토할 필요가 있다.", "evidence": [
                {"page": 2, "quote": "The estimated coefficient is -0.12 and statistically significant at the 5 percent level."}
            ]}
        ],
        "keywords": ["monetary policy", "bank lending", "not-in-paper"],
        "evidence": [{"page": 1, "quote": "This paper studies whether monetary policy shocks affect bank lending."}],
    }


def test_normalize_llm_result_keeps_only_verifiable_claims():
    pages = _sample_pages()
    result = module.normalize_llm_result(_sample_model_output(), 2, pages)
    assert result["mode"] == "llm"
    assert result["analysis_version"] == module.ANALYSIS_VERSION
    assert "통화정책" in result["summary"]
    assert len(result["findings"]) == 1
    assert result["findings"][0]["estimate"] == "-0.12"
    assert len(result["robustness_checks"]) == 1
    assert "not-in-paper" not in result["keywords"]
    assert result["evidence"]
    for item in result["evidence"]:
        page_text = next(page["text"] for page in pages if page["page"] == item["page"])
        assert item["quote"] in page_text


def test_analysis_json_schema_disallows_unknown_properties():
    assert module.ANALYSIS_SCHEMA["additionalProperties"] is False
    assert set(module.ANALYSIS_SCHEMA["required"]) == set(module.ANALYSIS_SCHEMA["properties"])
    assert module.ANALYSIS_SCHEMA["properties"]["findings"]["items"]["additionalProperties"] is False


def test_llm_result_uses_structured_outputs(monkeypatch):
    pages = _sample_pages()
    model_output = _sample_model_output()
    requests = []

    class FakeResponse:
        def raise_for_status(self):
            return None
        def json(self):
            return {"choices": [{
                "finish_reason": "stop",
                "message": {"content": json.dumps(model_output, ensure_ascii=False), "refusal": None},
            }]}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.timeout = kwargs.get("timeout")
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            return None
        async def post(self, url, **kwargs):
            requests.append((url, kwargs))
            return FakeResponse()

    monkeypatch.setattr(module, "AI_PROVIDER", "openai")
    monkeypatch.setattr(module, "OPENAI_API_KEY", "test-key-not-used")
    monkeypatch.setattr(module, "OPENAI_MODEL", "gpt-5.6-terra")
    monkeypatch.setattr(module.httpx, "AsyncClient", FakeClient)
    result = asyncio.run(module.llm_result(2, pages))
    assert result["mode"] == "llm"
    assert requests[0][0] == "https://api.openai.com/v1/chat/completions"
    request_body = requests[0][1]["json"]
    assert request_body["response_format"]["type"] == "json_schema"
    assert request_body["response_format"]["json_schema"]["strict"] is True
    assert request_body["model"] == "gpt-5.6-terra"



def test_gemini_provider_uses_structured_json_and_server_side_key(monkeypatch):
    pages = _sample_pages()
    model_output = _sample_model_output()
    requests = []

    class FakeResponse:
        status_code = 200
        def raise_for_status(self):
            return None
        def json(self):
            return {"candidates": [{
                "finishReason": "STOP",
                "content": {"parts": [{"text": json.dumps(model_output, ensure_ascii=False)}]},
            }]}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.timeout = kwargs.get("timeout")
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            return None
        async def post(self, url, **kwargs):
            requests.append((url, kwargs))
            return FakeResponse()

    monkeypatch.setattr(module, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(module, "GEMINI_API_KEY", "test-gemini-key-not-used")
    monkeypatch.setattr(module, "GEMINI_MODEL", "gemini-3.8-flash")
    monkeypatch.setattr(module, "OPENAI_API_KEY", "")
    monkeypatch.setattr(module.httpx, "AsyncClient", FakeClient)

    result = asyncio.run(module.llm_result(2, pages))
    assert result["mode"] == "llm"
    assert result["provider"] == "gemini"
    assert result["model"] == "gemini-3.8-flash"
    assert requests[0][0].endswith("/v1beta/models/gemini-3.8-flash:generateContent")
    headers = requests[0][1]["headers"]
    assert headers["x-goog-api-key"] == "test-gemini-key-not-used"
    assert "key=" not in requests[0][0]
    config = requests[0][1]["json"]["generationConfig"]
    assert config["responseMimeType"] == "application/json"
    assert config["responseJsonSchema"] == module.ANALYSIS_SCHEMA
    assert config["thinkingConfig"]["thinkingLevel"] == "low"
    assert config["candidateCount"] == 1
    assert requests[0][1]["json"]["contents"][0]["parts"][0]["text"].startswith("다음은")


def test_provider_selection_does_not_silently_fallback(monkeypatch):
    monkeypatch.setattr(module, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(module, "GEMINI_API_KEY", "")
    monkeypatch.setattr(module, "OPENAI_API_KEY", "an-openai-key")
    assert module.active_ai_provider() is None
    assert module.active_ai_model("gemini") == "gemini-3.8-flash"


def test_gemini_health_reports_free_tier_data_notice(monkeypatch):
    from fastapi.testclient import TestClient
    monkeypatch.setattr(module, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(module, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(module, "GEMINI_MODEL", "gemini-3.8-flash")
    response = TestClient(module.app).get("/health")
    assert response.status_code == 200
    assert response.json()["analysis_mode"] == "ai"
    assert response.json()["ai_provider"] == "gemini"
    assert response.json()["model"] == "gemini-3.8-flash"
    assert response.json()["free_tier_data_notice"] is True



def test_gemini_retries_transient_503(monkeypatch):
    pages = _sample_pages()
    model_output = _sample_model_output()
    requests = []
    sleeps = []

    class FakeResponse:
        def __init__(self, status_code):
            self.status_code = status_code
            self.headers = {}
        def raise_for_status(self):
            if self.status_code >= 400:
                raise AssertionError("unexpected HTTP error")
        def json(self):
            return {"candidates": [{
                "finishReason": "STOP",
                "content": {"parts": [{"text": json.dumps(model_output, ensure_ascii=False)}]},
            }]}

    class FakeClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        async def post(self, url, **kwargs):
            requests.append(url)
            return FakeResponse(503 if len(requests) == 1 else 200)

    async def fake_sleep(seconds):
        sleeps.append(seconds)

    monkeypatch.setattr(module, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(module, "GEMINI_API_KEY", "test-key-not-used")
    monkeypatch.setattr(module, "GEMINI_MODEL", "gemini-3.8-flash")
    monkeypatch.setattr(module.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(module.asyncio, "sleep", fake_sleep)

    result = asyncio.run(module.llm_result(2, pages))
    assert result["provider"] == "gemini"
    assert len(requests) == 2
    assert sleeps == [1.5]
