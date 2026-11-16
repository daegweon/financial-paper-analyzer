import asyncio
import json

import app.main as module


def _sample_pages():
    return [
        {
            "page": 1,
            "text": (
                "This paper studies whether monetary policy shocks affect bank lending. "
                "We use a panel of 50 banks from 2001 to 2020. The dependent variable is loan growth. "
                "We estimate a fixed-effects panel regression. The panel is balanced and annual, "
                "with 50 banks observed for 20 years."

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
            "design_evidence": [{"page": 1, "quote": "We estimate a fixed-effects panel regression."}],
            "sample": "50개 은행",
            "sample_evidence": [{"page": 1, "quote": "We use a panel of 50 banks from 2001 to 2020."}],
            "period": "2001~2020년",
            "period_evidence": [{"page": 1, "quote": "We use a panel of 50 banks from 2001 to 2020."}],
            "data_sources": ["은행 패널 자료"],
            "data_sources_evidence": [{"page": 1, "quote": "We use a panel of 50 banks from 2001 to 2020."}],
            "variables": [
                {"name": "loan growth", "role": "종속변수", "definition": "대출 증가율",
                 "evidence": [{"page": 1, "quote": "The dependent variable is loan growth."}]}
            ],
            "empirical_strategy": "패널 회귀분석",
            "empirical_strategy_evidence": [{"page": 1, "quote": "We estimate a fixed-effects panel regression."}],
            "identification_strategy": "확인 불가",
            "identification_strategy_evidence": [],
            "equations": [],
            "equations_evidence": [],
            "evidence": [{"page": 1, "quote": "We use a panel of 50 banks from 2001 to 2020."}],
            "panel_dimensions": {
                "study_design_type": "balanced_panel",
                "study_design_evidence": [{
                    "page": 1,
                    "quote": "The panel is balanced and annual, with 50 banks observed for 20 years.",
                }],
                "panel_balance": "balanced",
                "panel_balance_evidence": [{
                    "page": 1,
                    "quote": "The panel is balanced and annual, with 50 banks observed for 20 years.",
                }],
                "cross_sectional_units_count": 50,
                "time_periods_count": 20,
                "reported_total_observations_count": 0,
                "observation_frequency": "annual",
                "observation_unit": "bank-year",
                "sample_count_reports": [],
                "evidence": [{
                    "page": 1,
                    "quote": "The panel is balanced and annual, with 50 banks observed for 20 years.",
                }],
            },
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
    monkeypatch.setattr(module, "GEMINI_MODEL", "gemini-3.5-flash-lite")
    monkeypatch.setattr(module, "GEMINI_FALLBACK_MODEL", "gemini-3.6-flash")
    monkeypatch.setattr(module, "OPENAI_API_KEY", "")
    monkeypatch.setattr(module.httpx, "AsyncClient", FakeClient)

    result = asyncio.run(module.llm_result(2, pages))
    assert result["mode"] == "llm"
    assert result["provider"] == "gemini"
    assert result["model"] == "gemini-3.5-flash-lite"
    assert requests[0][0].endswith("/v1beta/models/gemini-3.5-flash-lite:generateContent")
    headers = requests[0][1]["headers"]
    assert headers["x-goog-api-key"] == "test-gemini-key-not-used"
    assert "key=" not in requests[0][0]
    config = requests[0][1]["json"]["generationConfig"]
    assert config["responseMimeType"] == "application/json"
    assert config["responseJsonSchema"] == module.ANALYSIS_SCHEMA
    assert config["thinkingConfig"]["thinkingLevel"] == "minimal"
    assert "candidateCount" not in config
    assert config["maxOutputTokens"] == 16384
    assert requests[0][1]["json"]["contents"][0]["parts"][0]["text"].startswith("다음은")


def test_provider_selection_does_not_silently_fallback(monkeypatch):
    monkeypatch.setattr(module, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(module, "GEMINI_API_KEY", "")
    monkeypatch.setattr(module, "OPENAI_API_KEY", "an-openai-key")
    assert module.active_ai_provider() is None
    assert module.active_ai_model("gemini") == "gemini-3.5-flash-lite"


def test_gemini_health_reports_free_tier_data_notice(monkeypatch):
    from fastapi.testclient import TestClient
    monkeypatch.setattr(module, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(module, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(module, "GEMINI_MODEL", "gemini-3.5-flash-lite")
    monkeypatch.setattr(module, "GEMINI_FALLBACK_MODEL", "gemini-3.6-flash")
    response = TestClient(module.app).get("/health")
    assert response.status_code == 200
    assert response.json()["analysis_mode"] == "ai"
    assert response.json()["ai_provider"] == "gemini"
    assert response.json()["model"] == "gemini-3.5-flash-lite"
    assert response.json()["fallback_model"] == "gemini-3.6-flash"
    assert response.json()["free_tier_data_notice"] is True



def test_gemini_falls_back_to_flash_when_primary_returns_503(monkeypatch):
    pages = _sample_pages()
    model_output = _sample_model_output()
    requests = []
    sleeps = []

    class FakeResponse:
        def __init__(self, status_code):
            self.status_code = status_code
            self.headers = {}
            self.text = "temporary overload" if status_code == 503 else ""
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
            requests.append((url, kwargs))
            return FakeResponse(503 if len(requests) == 1 else 200)

    async def fake_sleep(seconds):
        sleeps.append(seconds)

    monkeypatch.setattr(module, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(module, "GEMINI_API_KEY", "test-key-not-used")
    monkeypatch.setattr(module, "GEMINI_MODEL", "gemini-3.5-flash-lite")
    monkeypatch.setattr(module, "GEMINI_FALLBACK_MODEL", "gemini-3.6-flash")
    monkeypatch.setattr(module.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(module.asyncio, "sleep", fake_sleep)

    result = asyncio.run(module.llm_result(2, pages))
    assert result["provider"] == "gemini"
    assert result["model"] == "gemini-3.6-flash"
    assert len(requests) == 2
    assert requests[0][0].endswith("/gemini-3.5-flash-lite:generateContent")
    assert requests[1][0].endswith("/gemini-3.6-flash:generateContent")
    assert requests[0][1]["json"]["generationConfig"]["thinkingConfig"]["thinkingLevel"] == "minimal"
    assert requests[1][1]["json"]["generationConfig"]["thinkingConfig"]["thinkingLevel"] == "low"
    assert sleeps == [1.0]


def test_gemini_falls_back_when_primary_times_out(monkeypatch):
    pages = _sample_pages()
    model_output = _sample_model_output()
    requests = []

    class FakeResponse:
        status_code = 200
        headers = {}
        text = ""
        def raise_for_status(self): return None
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
            if len(requests) == 1:
                raise module.httpx.ReadTimeout("primary timed out")
            return FakeResponse()

    async def fake_sleep(seconds): return None

    monkeypatch.setattr(module, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(module, "GEMINI_API_KEY", "test-key-not-used")
    monkeypatch.setattr(module, "GEMINI_MODEL", "gemini-3.5-flash-lite")
    monkeypatch.setattr(module, "GEMINI_FALLBACK_MODEL", "gemini-3.6-flash")
    monkeypatch.setattr(module.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(module.asyncio, "sleep", fake_sleep)

    result = asyncio.run(module.llm_result(2, pages))
    assert result["provider"] == "gemini"
    assert result["model"] == "gemini-3.6-flash"
    assert len(requests) == 2



def test_gemini_retries_with_fallback_when_primary_hits_output_cap(monkeypatch):
    pages = _sample_pages()
    model_output = _sample_model_output()
    requests = []

    class FakeResponse:
        def __init__(self, finish_reason):
            self.status_code = 200
            self.headers = {}
            self.text = ""
            self.finish_reason = finish_reason
        def raise_for_status(self):
            return None
        def json(self):
            if self.finish_reason == "MAX_TOKENS":
                return {
                    "candidates": [{"finishReason": "MAX_TOKENS", "content": {"parts": []}}],
                    "usageMetadata": {
                        "promptTokenCount": 12000,
                        "candidatesTokenCount": 16384,
                        "thoughtsTokenCount": 0,
                        "totalTokenCount": 28384,
                    },
                }
            return {
                "candidates": [{
                    "finishReason": "STOP",
                    "content": {"parts": [{"text": json.dumps(model_output, ensure_ascii=False)}]},
                }],
                "usageMetadata": {
                    "promptTokenCount": 12000,
                    "candidatesTokenCount": 4500,
                    "thoughtsTokenCount": 100,
                    "totalTokenCount": 16600,
                },
            }

    class FakeClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        async def post(self, url, **kwargs):
            requests.append((url, kwargs))
            return FakeResponse("MAX_TOKENS" if len(requests) == 1 else "STOP")

    async def fake_sleep(seconds):
        return None

    monkeypatch.setattr(module, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(module, "GEMINI_API_KEY", "test-key-not-used")
    monkeypatch.setattr(module, "GEMINI_MODEL", "gemini-3.5-flash-lite")
    monkeypatch.setattr(module, "GEMINI_FALLBACK_MODEL", "gemini-3.6-flash")
    monkeypatch.setattr(module.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(module.asyncio, "sleep", fake_sleep)

    result = asyncio.run(module.llm_result(2, pages))
    assert result["provider"] == "gemini"
    assert result["model"] == "gemini-3.6-flash"
    assert len(requests) == 2
    assert requests[0][1]["json"]["generationConfig"]["maxOutputTokens"] == 16384
    assert requests[1][1]["json"]["generationConfig"]["maxOutputTokens"] == 24576



def test_validate_evidence_normalizes_pdf_ligatures_and_dash_variants():
    page_text = (
        "The coefﬁcient is statistically signiﬁcant at the 5% level – "
        "after the robustness adjustment."
    )
    accepted = module.validate_evidence(
        [{
            "page": 1,
            "quote": "The coefficient is statistically significant at the 5% level - after the robustness adjustment.",
        }],
        [{"page": 1, "text": page_text}],
    )
    assert len(accepted) == 1
    assert accepted[0]["quote"] in page_text
    assert "coefﬁcient" in accepted[0]["quote"]


def test_validate_evidence_normalizes_whitespace_but_returns_page_excerpt():
    page_text = "The estimated coefficient  is negative and statistically significant."
    accepted = module.validate_evidence(
        [{"page": 2, "quote": "The estimated coefficient is negative and statistically significant."}],
        [{"page": 2, "text": page_text}],
    )
    assert len(accepted) == 1
    assert accepted[0]["quote"] in page_text


def test_methodology_keeps_variables_when_section_level_quote_is_missing():
    pages = _sample_pages()
    raw = _sample_model_output()
    raw["methodology"]["evidence"] = []
    for key in ("design", "sample", "period", "data_sources", "empirical_strategy", "identification_strategy", "equations"):
        raw["methodology"][f"{key}_evidence"] = []
    result = module.normalize_llm_result(raw, 2, pages)
    assert result["methodology"]["design"] == "확인 불가"
    assert len(result["methodology"]["variables"]) == 1
    assert result["methodology"]["variables"][0]["name"] == "loan growth"
    assert any("변수별 원문 근거" in warning for warning in result["warnings"])


def test_analysis_prompt_requires_korean_findings_and_separates_hypotheses():
    prompt = module.build_analysis_prompt(_sample_pages())
    assert "findings 배열을 비워 두지 말고" in prompt
    assert "가설(hypotheses)과 실제 검증 결과(findings)를 혼동하지 않는다" in prompt
    assert "전체 답변하지 않는다" in prompt



def test_audit_finding_checks_numeric_values_and_direction_against_cited_page():
    pages = _sample_pages()
    supported = {
        "claim": "추정계수는 -0.12이며 5% 수준에서 통계적으로 유의하다.",
        "direction": "negative",
        "estimate": "-0.12",
        "statistical_significance": "5% level",
        "evidence": [{"page": 2, "quote": "The estimated coefficient is -0.12 and statistically significant at the 5 percent level."}],
    }
    audit = module.audit_finding(supported, pages)
    assert audit["status"] == "screen_passed"
    assert audit["numeric_supported"] is True
    assert audit["direction_consistent"] is True
    assert audit["significance_supported"] is True


def test_audit_finding_flags_unsupported_numeric_claim_and_sign_conflict():
    pages = _sample_pages()
    unsupported = {
        "claim": "추정계수는 0.25이며 1% 수준에서 유의하다.",
        "direction": "negative",
        "estimate": "0.25",
        "statistical_significance": "1% level",
        "evidence": [{"page": 2, "quote": "The estimated coefficient is -0.12 and statistically significant at the 5 percent level."}],
    }
    audit = module.audit_finding(unsupported, pages)
    assert audit["status"] == "review"
    assert audit["numeric_supported"] is False
    assert set(audit["unsupported_numeric_tokens"]) == {"0.25"}
    assert audit["direction_consistent"] is False
    assert audit["significance_supported"] is False


def test_audit_finding_requires_numeric_estimate_inside_direct_quote():
    pages = [{
        "page": 9,
        "text": (
            "Table 9 AR_Amihud -0.154*** (0.048). "
            "The discussion describes a negative and significant association."
        ),
    }]
    finding = {
        "claim": "예상치 못한 유동성 위험은 초과수익률과 음(-)의 관계를 보인다.",
        "direction": "negative",
        "estimate": "-0.154",
        "statistical_significance": "1% level",
        "evidence": [{
            "page": 9,
            "quote": "The discussion describes a negative and significant association.",
        }],
        "significance_legend_evidence": [{
            "page": 9,
            "quote": "*** p < 0.01",
        }],
    }
    audit = module.audit_finding(finding, pages)
    assert audit["status"] == "review"
    assert audit["numeric_supported"] is False
    assert audit["unsupported_numeric_tokens"] == ["-0.154"]


def test_audit_finding_ignores_tier_table_and_column_labels_but_checks_coefficient():
    pages = [{
        "page": 7,
        "text": (
            "Table 3 L.Tier1Rat*SFFR −0.000348 −0.000493 0.00140*** 0.00168*** "
            "(0.340) (0.183) (0.000) (0.000). "
            "Standard errors are clustered at the bank level p values in parentheses "
            "* p < 0.10, ** p < 0.05, *** p < 0.01."
        ),
    }]
    finding = {
        "claim": (
            "표 3의 열 (4)에서 티어 1 자본비율과 SFFR의 상호작용항 계수는 "
            "0.00168로 양(+)이며 1% 수준에서 유의하다."
        ),
        "direction": "positive",
        "estimate": "0.00168",
        "statistical_significance": "p < 0.01",
        "table_reference": "Table 3",
        "model_or_column": "(4)",
        "evidence": [{
            "page": 7,
            "quote": (
                "L.Tier1Rat*SFFR −0.000348 −0.000493 0.00140*** 0.00168*** "
                "(0.340) (0.183) (0.000) (0.000)"
            ),
        }],
        "significance_legend_evidence": [{
            "page": 7,
            "quote": (
                "Standard errors are clustered at the bank level p values in parentheses "
                "* p < 0.10, ** p < 0.05, *** p < 0.01"
            ),
        }],
    }
    audit = module.audit_finding(finding, pages)
    assert audit["status"] == "screen_passed"
    assert audit["numeric_supported"] is True
    assert audit["unsupported_numeric_tokens"] == []
    assert audit["significance_supported"] is True
    revalidated, rejected, _ = module._revalidate_prior_findings([finding], pages)
    assert rejected == []
    assert len(revalidated) == 1

    unsupported = {**finding, "estimate": "0.999"}
    failed_audit = module.audit_finding(unsupported, pages)
    assert failed_audit["status"] == "review"
    assert failed_audit["numeric_supported"] is False
    assert failed_audit["unsupported_numeric_tokens"] == ["0.999"]


def test_audit_finding_ignores_financial_model_identifiers_but_checks_reported_metrics():
    quote = (
        "The two-country durable consumption model reports R2 = 0.633 and MAE = 1.405%. "
        "Regime 1 is the bear-market state. The Fama-French three-factor model is used "
        "for comparison in the ASEAN-5 sample and the 5-21 hedging portfolio."
    )
    pages = [{"page": 10, "text": quote}]
    finding = {
        "claim": (
            "2국가 내구재 소비 모형의 R2는 0.633이고 MAE는 1.405%이다. "
            "Regime 1과 Fama-French 3요인 모형을 ASEAN-5 표본 및 "
            "5-21 hedging portfolio와 Figure 1에서 비교한다."
        ),
        "direction": "neutral",
        "estimate": "R2 = 0.633; MAE = 1.405%",
        "table_reference": "Table 3",
        "model_or_column": "Two-Country EZ-D",
        "evidence": [{"page": 10, "quote": quote}],
    }
    audit = module.audit_finding(finding, pages)
    assert audit["numeric_supported"] is True, audit["unsupported_numeric_tokens"]
    assert audit["unsupported_numeric_tokens"] == []

    unsupported = {**finding, "estimate": "R2 = 0.999; MAE = 1.405%"}
    failed = module.audit_finding(unsupported, pages)
    assert failed["numeric_supported"] is False
    assert failed["unsupported_numeric_tokens"] == ["0.999"]


def test_audit_finding_matches_written_count_words_only_in_count_context():
    quote = (
        "SCGP appears in 12 of the 20 portfolios, followed by KCE with nine appearances. "
        "The Sharpe ratio is five times higher in this specification."
    )
    pages = [{"page": 13, "text": quote}]
    finding = {
        "claim": "KCE는 9회 선택되었다.",
        "direction": "neutral",
        "estimate": "9 appearances",
        "table_reference": "Figure 1",
        "model_or_column": "Stock selection frequency",
        "evidence": [{"page": 13, "quote": quote}],
    }
    finding["claim"] = "KCE는 nine appearances로 9회 선택되었다."
    finding["estimate"] = "nine appearances"
    assert module._extract_written_count_tokens(quote) == ["9"]
    assert module._extract_written_count_tokens("nine of the 20 portfolios") == ["9"]
    assert module._extract_written_count_tokens("two to five stocks") == ["2", "5"]
    audit = module.audit_finding(finding, pages)
    assert audit["numeric_supported"] is True, audit["unsupported_numeric_tokens"]
    assert audit["unsupported_numeric_tokens"] == []
    assert module._extract_written_count_tokens("nine appearances") == ["9"]
    assert module._extract_written_count_tokens("five times higher") == []


def test_audit_finding_ignores_portfolio_size_labels_but_checks_sharpe_coefficients():
    pages = [{
        "page": 10,
        "text": (
            "2 (ADVANC, SCC) 0.03 0.33. "
            "Portfolio Sharpe ratio for the two-stock portfolio is 0.33. "
            "Table 1 reports SharpeRV 0.33 versus SharpeVar 0.02."
        ),
    }]
    finding = {
        "claim": "2종목 최적 포트폴리오에서 실현 변동성 모형의 샤프 지수는 0.33으로 분산 모형의 0.02보다 높다.",
        "direction": "positive",
        "estimate": "SharpeRV 0.33 vs SharpeVar 0.02",
        "table_reference": "Table 1",
        "model_or_column": "2-stock portfolio",
        "evidence": [{
            "page": 10,
            "quote": "2 (ADVANC, SCC) 0.03 0.33. Table 1 reports SharpeRV 0.33 versus SharpeVar 0.02.",
        }],
    }
    audit = module.audit_finding(finding, pages)
    assert audit["numeric_supported"] is True
    assert audit["unsupported_numeric_tokens"] == []

    unsupported = {**finding, "estimate": "SharpeRV 0.99 vs SharpeVar 0.02"}
    failed = module.audit_finding(unsupported, pages)
    assert failed["numeric_supported"] is False
    assert "0.99" in failed["unsupported_numeric_tokens"]


def test_numeric_audit_ignores_four_and_five_stock_labels():
    pages = [{
        "page": 12,
        "text": (
            "Realized volatility portfolios improve from 0.11 at 1% to 0.17 at 5%, "
            "while variance-based portfolios show only marginal gains, peaking at 0.04."
        ),
    }]
    for size in (4, 5):
        finding = {
            "claim": f"{size}개 종목 포트폴리오에서 SharpeRV는 0.11에서 0.17로 상승한다.",
            "direction": "positive",
            "estimate": "SharpeRV from 0.11 to 0.17",
            "table_reference": "Table 5",
            "model_or_column": f"{size}-stock portfolios",
            "evidence": [{
                "page": 12,
                "quote": (
                    "Realized volatility portfolios improve from 0.11 at 1% to 0.17 at 5%, "
                    "while variance-based portfolios show only marginal gains, peaking at 0.04."
                ),
            }],
        }
        audit = module.audit_finding(finding, pages)
        assert audit["numeric_supported"] is True
        assert audit["unsupported_numeric_tokens"] == []

    unsupported = {
        **finding,
        "estimate": "SharpeRV from 0.11 to 0.99",
    }
    audit = module.audit_finding(unsupported, pages)
    assert audit["numeric_supported"] is False
    assert "0.99" in audit["unsupported_numeric_tokens"]


def test_table_and_figure_reference_overlap_deduplicates_compound_citations():
    quote = "SCGP appears in 12 of the 20 portfolios, followed by KCE with nine appearances."
    left = {
        "claim": "SCGP와 KCE의 종목 선택 빈도를 분석했다.",
        "direction": "neutral",
        "estimate": "SCGP 12, KCE 9",
        "table_reference": "Figure 1 and Table 9",
        "model_or_column": "Stock selection frequency",
        "evidence": [{"page": 13, "quote": quote}],
    }
    right = {
        "claim": "SCGP와 KCE의 선택 빈도를 비교했다.",
        "direction": "neutral",
        "estimate": "SCGP 12, KCE 9",
        "table_reference": "Figure 1",
        "model_or_column": "Stock selection frequency",
        "evidence": [{"page": 13, "quote": quote}],
    }
    assert module._finding_table_reference_keys("Figures 4-6 and Table 3") == {
        "figure:4", "figure:5", "figure:6", "table:3"
    }
    assert module._are_duplicate_findings(left, right) is True

    cross_page_left = {
        **left,
        "claim": "SCGP와 KCE의 종목 선택 빈도를 분석했다.",
        "evidence": [{"page": 13, "quote": quote}],
    }
    cross_page_right = {
        **right,
        "claim": "SCGP와 KCE의 종목 선택 빈도를 분석했다.",
        "evidence": [{"page": 14, "quote": quote}],
    }
    assert module._are_duplicate_findings(cross_page_left, cross_page_right) is True


def test_dedup_merges_figure_findings_with_unknown_metadata_but_protects_other_variables():
    quote = (
        "As shown in Figure 1a, SCGP emerges as the most frequently selected stock, "
        "appearing in 12 of the 20 portfolios, followed by KCE with nine appearances."
    )
    left = {
        "claim": "SCGP는 실현 변동성 모형에서 가장 자주 선택된 종목이다.",
        "direction": "positive",
        "estimate": "12",
        "table_reference": "Figure 1",
        "model_or_column": "Stock selection frequency based on Volm(W)",
        "evidence": [{"page": 13, "quote": quote}],
    }
    alias = {
        "claim": "SCGP와 KCE의 종목 선택 빈도가 높게 나타났다.",
        "direction": "확인 불가",
        "estimate": "SCGP 12, KCE 9",
        "table_reference": "Figure 1 and Table 9",
        "model_or_column": "확인 불가",
        "evidence": [{"page": 13, "quote": quote}],
    }
    assert module._are_duplicate_findings(left, alias) is True

    contradictory = {**alias, "direction": "negative"}
    assert module._are_duplicate_findings(left, contradictory) is False

    other_variable = {
        **alias,
        "claim": "CDS 스프레드가 주식 비유동성을 높인다.",
        "direction": "positive",
        "estimate": "12",
        "model_or_column": "Liquidity regression",
    }
    assert module._finding_variable_tokens(left) == {"SCGP"}
    assert module._finding_variable_tokens(other_variable) == {"CDS"}
    assert module._are_duplicate_findings(left, other_variable) is False


def test_audit_finding_supports_unicode_operator_star_legend():
    pages = [{
        "page": 7,
        "text": (
            "Table 3 CDS 0.024∗∗∗ (0.008). "
            "Note: ∗∗∗, ∗∗, and ∗ indicate significance at 1%, 5%, and 10%."
        ),
    }]
    finding = {
        "claim": "CDS 스프레드는 R-spread와 양(+)의 관계를 보인다.",
        "direction": "positive",
        "estimate": "0.024",
        "statistical_significance": "1% level",
        "table_reference": "Table 3",
        "model_or_column": "Column (1)",
        "evidence": [{
            "page": 7,
            "quote": "Table 3 CDS 0.024∗∗∗ (0.008)",
        }],
        "significance_legend_evidence": [{
            "page": 7,
            "quote": "∗∗∗, ∗∗, and ∗ indicate significance at 1%, 5%, and 10%.",
        }],
    }
    audit = module.audit_finding(finding, pages)
    assert audit["status"] == "screen_passed"
    assert audit["numeric_supported"] is True
    assert audit["significance_supported"] is True


def test_merge_prior_findings_revalidates_quotes_and_prefers_supported_duplicate():
    pages = [
        {
            "page": 9,
            "text": (
                "The results in Table 9 show that unexpected liquidity risk is "
                "negatively related to excess stock returns."
            ),
        },
        {
            "page": 10,
            "text": (
                "Table 9 AR_Amihud −0.154∗∗∗ (0.048). "
                "Note: ∗∗∗, ∗∗, and ∗ indicate significance at 1%, 5%, and 10%."
            ),
        },
    ]
    claim = "AR_Amihud 계수는 음(-)이며 1% 수준에서 유의하다."
    current_review = {
        "claim": claim,
        "direction": "negative",
        "estimate": "-0.154",
        "statistical_significance": "1% level",
        "table_reference": "Table 9",
        "model_or_column": "Column (1) AR_Amihud",
        "evidence": [{
            "page": 9,
            "quote": (
                "The results in Table 9 show that unexpected liquidity risk is "
                "negatively related to excess stock returns."
            ),
        }],
    }
    prior_supported = {
        **current_review,
        "model_or_column": "Columns (1), (2), and (3)",
        "evidence": [{
            "page": 10,
            "quote": "Table 9 AR_Amihud −0.154∗∗∗ (0.048)",
        }],
        "significance_legend_evidence": [{
            "page": 10,
            "quote": "∗∗∗, ∗∗, and ∗ indicate significance at 1%, 5%, and 10%.",
        }],
    }
    invalid_prior = {
        **prior_supported,
        "estimate": "-0.999",
    }

    current = module._normalize_findings([current_review], pages)
    merged, revalidated, rejected, _ = module._merge_prior_findings(
        current, [prior_supported, invalid_prior], pages
    )
    assert len(revalidated) == 1
    assert len(rejected) == 1
    assert rejected[0]["estimate"] == "-0.999"
    assert len(merged) == 1
    assert merged[0]["verification"]["status"] == "screen_passed"
    assert merged[0]["verification"]["numeric_supported"] is True
    assert merged[0]["verification"]["significance_supported"] is True
    assert {item["page"] for item in merged[0]["evidence"]} == {9, 10}


def test_dedup_merges_same_evidence_across_korean_and_english_directions():
    quote = "L.NIBDepRat*SFFR 0.000702*** 0.000749*** 0.000321** 0.000615***"
    current = {
        "claim": "무이자 예금 비중이 높은 은행은 통화정책 긴축 시 위험 감수를 덜 줄인다.",
        "direction": "양(+)의 방향",
        "estimate": "0.000615",
        "table_reference": "Table 3",
        "model_or_column": "Column (4)",
        "evidence": [{"page": 7, "quote": quote}],
    }
    prior = {
        "claim": (
            "대손충당금 비율(LLPRat)을 종속변수로 한 회귀분석에서 "
            "L.NIBDepRat*SFFR 계수는 0.000615로 양(+)이다."
        ),
        "direction": "positive",
        "estimate": "0.000615",
        "table_reference": "Table 3",
        "model_or_column": "(4)",
        "evidence": [{"page": 7, "quote": quote}],
    }
    assert module._are_duplicate_findings(current, prior) is True, (module._finding_direction_sign(current["direction"]), module._finding_direction_sign(prior["direction"]), module._finding_numeric_set(current), module._finding_numeric_set(prior), module._finding_table_reference_keys(current["table_reference"]), module._finding_table_reference_keys(prior["table_reference"]))

    contradictory = {**prior, "direction": "negative"}
    assert module._are_duplicate_findings(current, contradictory) is False


def test_dedup_merges_b10_figure_one_duplicate_across_quote_prefix_and_direction_labels():
    left = {
        "claim": "종목 선택 빈도 분석 결과, SCGP와 KCE가 실현 변동성 및 분산 모형 모두에서 가장 빈번하게 선택되어 위험 최소화 전략의 핵심 구성 종목임을 확인하였다.",
        "direction": "일치",
        "estimate": "SCGP selected 12 times and KCE 9 times out of 20 portfolios under Volm",
        "table_reference": "Figure 1 and Table 9",
        "model_or_column": "Stock selection frequency",
        "evidence": [{
            "page": 13,
            "quote": "As shown in Figure 1a, SCGP emerges as the most frequently selected stock, appearing in 12 of the 20 portfolios, followed by KCE with nine appearances.",
        }],
    }
    right = {
        "claim": "종목 선택 빈도 분석 결과, SCGP와 KCE가 두 위험 계량화 지표 모두에서 가장 빈번하게 최적 포트폴리오에 포함되어 위험 최소화 전략에서 핵심적인 역할을 한다.",
        "direction": "positive",
        "estimate": "SCGP selected in 12 and KCE in 9 portfolios (Volm)",
        "table_reference": "Figure 1",
        "model_or_column": "Stock selection frequency",
        "evidence": [{
            "page": 13,
            "quote": "SCGP emerges as the most frequently selected stock, appearing in 12 of the 20 portfolios, followed by KCE with nine appearances.",
        }],
    }
    assert module._are_duplicate_findings(left, right) is True


def test_dedup_does_not_merge_same_figure_but_different_portfolio_outcomes():
    left = {
        "claim": "SCGP is selected 12 times among the 20 portfolios.",
        "direction": "positive",
        "estimate": "12 of 20 portfolios",
        "table_reference": "Figure 1",
        "model_or_column": "Stock selection frequency",
        "evidence": [{"page": 13, "quote": "SCGP appears in 12 of the 20 portfolios."}],
    }
    right = {
        "claim": "KCE is selected 9 times among the 20 portfolios.",
        "direction": "positive",
        "estimate": "9 of 20 portfolios",
        "table_reference": "Figure 1",
        "model_or_column": "Stock selection frequency",
        "evidence": [{"page": 13, "quote": "KCE appears in 9 of the 20 portfolios."}],
    }
    assert module._are_duplicate_findings(left, right) is False


def test_cross_page_dedup_does_not_merge_different_variables_with_same_estimate():
    left = {
        "claim": "AR_Amihud 유동성 위험 계수는 음(-)이다.",
        "direction": "negative",
        "estimate": "-0.154",
        "table_reference": "Table 9",
        "model_or_column": "Column (1)",
        "evidence": [{"page": 9, "quote": "AR_Amihud coefficient -0.154"}],
    }
    right = {
        "claim": "CDS 스프레드 계수는 음(-)이다.",
        "direction": "negative",
        "estimate": "-0.154",
        "table_reference": "Table 9",
        "model_or_column": "Column (1)",
        "evidence": [{"page": 10, "quote": "CDS spread coefficient -0.154"}],
    }
    assert module._are_duplicate_findings(left, right) is False


def test_findings_rescue_prompt_uses_prior_candidates_as_untrusted_hints():
    pages = [{"page": 7, "text": "Table 3 CDS 0.024∗∗∗ (0.008)."}]
    prompt = module.build_findings_rescue_prompt(
        pages,
        [{
            "claim": "CDS 스프레드는 R-spread와 양(+)의 관계를 보인다.",
            "estimate": "0.024",
            "table_reference": "Table 3",
            "model_or_column": "Column (1)",
            "evidence": [{"page": 7, "quote": "Table 3 CDS 0.024∗∗∗ (0.008)"}],
        }],
    )
    assert "Table 3" in prompt
    assert "탐색 힌트일 뿐 정답이 아니다" in prompt
    assert "0.024" in prompt


def test_summary_falls_back_to_only_page_verified_methodology_and_findings():
    raw = _sample_model_output()
    raw["evidence"] = []
    result = module.normalize_llm_result(raw, 2, _sample_pages())
    assert "연구 설계는 은행 패널 분석" in result["summary"]
    assert "추정계수는 -0.12" in result["summary"]
    assert result["evidence"]
    assert all(item["quote"] in _sample_pages()[item["page"] - 1]["text"] for item in result["evidence"])


def test_primary_prompt_requires_exact_regression_row_and_separate_legend():
    pages = [{
        "page": 8,
        "text": (
            "Table 4. Liquidity regression. "
            "AR_Amihud -0.154*** (0.048). "
            "Note: *** p < 0.01."
        ),
    }]
    prompt = module.build_analysis_prompt(pages)
    assert "실제 계수 셀을 포함한" in prompt
    assert "model_or_column의 셀을 정확히 식별" in prompt
    assert "표 행 인용에 연결" in prompt
    assert "significance_legend_evidence" in prompt


def test_repair_prompt_requires_row_quote_not_prose_or_legend_substitution():
    pages = [{
        "page": 8,
        "text": (
            "The coefficient is negative and significant. "
            "Table 4 AR_Amihud -0.154*** (0.048). "
            "Note: *** p < 0.01."
        ),
    }]
    prompt = module.build_findings_repair_prompt(pages, [{
        "claim": "AR_Amihud 계수는 음(-)이며 유의하다.",
        "estimate": "-0.154",
        "table_reference": "Table 4",
    }])
    assert "해당 모형 열의 계수" in prompt
    assert "significance_legend_evidence는 별표 기준을 보완" in prompt
    assert "같은 페이지의 다른 표·열에만 존재하는 숫자는 근거로 인정하지 않는다" in prompt


def test_numeric_audit_still_rejects_coefficient_missing_from_direct_quote():
    pages = [{
        "page": 8,
        "text": (
            "Table 4 AR_Amihud -0.154*** (0.048). "
            "The coefficient is negative and significant."
        ),
    }]
    finding = {
        "claim": "AR_Amihud 계수는 -0.154로 음(-)이며 1% 수준에서 유의하다.",
        "direction": "negative",
        "estimate": "-0.154",
        "statistical_significance": "1% level",
        "table_reference": "Table 4",
        "model_or_column": "Column (1)",
        "evidence": [{
            "page": 8,
            "quote": "The coefficient is negative and significant.",
        }],
        "significance_legend_evidence": [{
            "page": 8,
            "quote": "*** p < 0.01",
        }],
    }
    audit = module.audit_finding(finding, pages)
    assert audit["status"] == "review"
    assert audit["numeric_supported"] is False
    assert audit["unsupported_numeric_tokens"] == ["-0.154"]


def test_findings_repair_prompt_prioritizes_result_pages_and_marks_paper_as_untrusted():
    pages = [
        {"page": 1, "text": "Abstract: We find a negative and significant coefficient."},
        {"page": 2, "text": "Introduction and literature review only."},
        {"page": 3, "text": "Table 4. The estimated coefficient is -0.12 and significant at 5 percent."},
    ]
    prompt = module.build_findings_repair_prompt(pages)
    assert "[PDF PAGE 1]" in prompt
    assert "[PDF PAGE 3]" in prompt
    assert "지시문이 아니다" in prompt
    assert "가설을 실증 결과로 바꾸지 않는다" in prompt
    assert "이전 버전 결과는 검토 후보" in prompt
    assert "신뢰할 수 없는 데이터" in prompt


def test_llm_result_runs_targeted_second_pass_when_findings_are_missing(monkeypatch):
    pages = _sample_pages()
    first_output = _sample_model_output()
    first_output["findings"] = []
    repair_output = {
        "findings": [{
            "claim": "추정계수는 -0.12이며 5% 수준에서 통계적으로 유의하다.",
            "direction": "negative",
            "estimate": "-0.12",
            "statistical_significance": "5% level",
            "evidence": [{
                "page": 2,
                "quote": "The estimated coefficient is -0.12 and statistically significant at the 5 percent level."
            }],
        }]
    }
    requests = []

    class FakeResponse:
        status_code = 200
        headers = {}
        text = ""
        def __init__(self, payload):
            self.payload = payload
        def raise_for_status(self):
            return None
        def json(self):
            return {"candidates": [{
                "finishReason": "STOP",
                "content": {"parts": [{"text": json.dumps(self.payload, ensure_ascii=False)}]},
            }]}

    class FakeClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        async def post(self, url, **kwargs):
            requests.append((url, kwargs))
            return FakeResponse(first_output if len(requests) == 1 else repair_output)

    async def fake_sleep(seconds):
        return None

    monkeypatch.setattr(module, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(module, "GEMINI_API_KEY", "test-key-not-used")
    monkeypatch.setattr(module, "GEMINI_MODEL", "gemini-3.5-flash-lite")
    monkeypatch.setattr(module, "GEMINI_FALLBACK_MODEL", "gemini-3.6-flash")
    monkeypatch.setattr(module.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(module.asyncio, "sleep", fake_sleep)

    result = asyncio.run(module.llm_result(2, pages))
    assert len(requests) == 2
    assert requests[0][1]["json"]["generationConfig"]["responseJsonSchema"] == module.ANALYSIS_SCHEMA
    assert requests[1][1]["json"]["generationConfig"]["responseJsonSchema"] == module.FINDINGS_ONLY_SCHEMA
    assert result["findings_verification"]["repair_attempted"] is True
    assert result["findings_verification"]["repair_status"] == "recovered"
    assert len(result["findings"]) == 1
    assert result["findings"][0]["verification"]["status"] == "screen_passed"
    assert "gemini-3.5-flash-lite" in result["models_used"]



def test_llm_result_repairs_multiple_rejected_prior_findings_but_not_one(monkeypatch):
    pages = _sample_pages()
    first_output = _sample_model_output()
    first_output["findings"] = [first_output["findings"][0]]
    repair_output = {"findings": [first_output["findings"][0]]}
    rejected_prior = [
        {
            "claim": "prior-only-candidate-one의 추정계수는 9.99이다.",
            "direction": "positive",
            "estimate": "9.99",
            "table_reference": "Table 8",
            "model_or_column": "Column (1)",
            "evidence": [{
                "page": 2,
                "quote": "The estimated coefficient is -0.12 and statistically significant at the 5 percent level.",
            }],
        },
        {
            "claim": "prior-only-candidate-two의 추정계수는 8.88이다.",
            "direction": "positive",
            "estimate": "8.88",
            "table_reference": "Table 9",
            "model_or_column": "Column (2)",
            "evidence": [{
                "page": 2,
                "quote": "The estimated coefficient is -0.12 and statistically significant at the 5 percent level.",
            }],
        },
    ]
    requests = []

    class FakeResponse:
        status_code = 200
        headers = {}
        text = ""
        def __init__(self, payload):
            self.payload = payload
        def raise_for_status(self):
            return None
        def json(self):
            return {"candidates": [{
                "finishReason": "STOP",
                "content": {"parts": [{"text": json.dumps(self.payload, ensure_ascii=False)}]},
            }]}

    class FakeClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        async def post(self, url, **kwargs):
            requests.append(kwargs["json"])
            return FakeResponse(first_output if len(requests) == 1 else repair_output)

    async def fake_sleep(seconds):
        return None

    monkeypatch.setattr(module, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(module, "GEMINI_API_KEY", "test-key-not-used")
    monkeypatch.setattr(module, "GEMINI_MODEL", "gemini-3.5-flash-lite")
    monkeypatch.setattr(module, "GEMINI_FALLBACK_MODEL", "gemini-3.6-flash")
    monkeypatch.setattr(module.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(module.asyncio, "sleep", fake_sleep)

    result = asyncio.run(module.llm_result(2, pages, prior_findings=rejected_prior))
    assert len(requests) == 2
    repair_payload = json.dumps(requests[1], ensure_ascii=False)
    assert "prior-only-candidate-one" in repair_payload
    assert "prior-only-candidate-two" in repair_payload
    assert result["findings_verification"]["prior_findings_loaded_count"] == 2
    assert result["findings_verification"]["prior_findings_rejected_count"] == 2
    assert result["findings_verification"]["repair_attempted"] is True


def test_llm_result_does_not_add_repair_call_for_single_rejected_prior_finding(monkeypatch):
    pages = _sample_pages()
    first_output = _sample_model_output()
    first_output["findings"] = [first_output["findings"][0]]
    requests = []

    class FakeResponse:
        status_code = 200
        headers = {}
        text = ""
        def raise_for_status(self):
            return None
        def json(self):
            return {"candidates": [{
                "finishReason": "STOP",
                "content": {"parts": [{"text": json.dumps(first_output, ensure_ascii=False)}]},
            }]}

    class FakeClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        async def post(self, url, **kwargs):
            requests.append(kwargs["json"])
            return FakeResponse()

    async def fake_sleep(seconds):
        return None

    monkeypatch.setattr(module, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(module, "GEMINI_API_KEY", "test-key-not-used")
    monkeypatch.setattr(module, "GEMINI_MODEL", "gemini-3.5-flash-lite")
    monkeypatch.setattr(module, "GEMINI_FALLBACK_MODEL", "gemini-3.6-flash")
    monkeypatch.setattr(module.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(module.asyncio, "sleep", fake_sleep)

    one_rejected = [{
        "claim": "prior-only-single-candidate의 추정계수는 9.99이다.",
        "direction": "positive",
        "estimate": "9.99",
        "table_reference": "Table 8",
        "model_or_column": "Column (1)",
        "evidence": [{
            "page": 2,
            "quote": "The estimated coefficient is -0.12 and statistically significant at the 5 percent level.",
        }],
    }]
    result = asyncio.run(module.llm_result(2, pages, prior_findings=one_rejected))
    assert len(requests) == 1
    assert result["findings_verification"]["prior_findings_rejected_count"] == 1
    assert result["findings_verification"]["repair_attempted"] is False


def test_llm_result_skips_redundant_repair_when_four_findings_are_already_supported(monkeypatch):
    pages = _sample_pages()
    first_output = _sample_model_output()
    base = first_output["findings"][0]
    first_output["findings"] = []
    for label, table_number in [
        ("Alpha", 1), ("Beta", 2), ("Gamma", 3), ("Delta", 4)
    ]:
        finding = dict(base)
        finding["claim"] = f"{label} supported result: " + base["claim"]
        finding["table_reference"] = f"Table {table_number}"
        finding["model_or_column"] = f"Column ({table_number})"
        first_output["findings"].append(finding)
    rejected_prior = [
        {
            "claim": "prior-only-candidate-one의 추정계수는 9.99이다.",
            "direction": "positive",
            "estimate": "9.99",
            "table_reference": "Table 8",
            "model_or_column": "Column (1)",
            "evidence": [{
                "page": 2,
                "quote": "The estimated coefficient is -0.12 and statistically significant at the 5 percent level.",
            }],
        },
        {
            "claim": "prior-only-candidate-two의 추정계수는 8.88이다.",
            "direction": "positive",
            "estimate": "8.88",
            "table_reference": "Table 9",
            "model_or_column": "Column (2)",
            "evidence": [{
                "page": 2,
                "quote": "The estimated coefficient is -0.12 and statistically significant at the 5 percent level.",
            }],
        },
    ]
    requests = []

    class FakeResponse:
        status_code = 200
        headers = {}
        text = ""
        def raise_for_status(self):
            return None
        def json(self):
            return {"candidates": [{
                "finishReason": "STOP",
                "content": {"parts": [{"text": json.dumps(first_output, ensure_ascii=False)}]},
            }]}

    class FakeClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        async def post(self, url, **kwargs):
            requests.append(kwargs["json"])
            return FakeResponse()

    async def fake_sleep(seconds):
        return None

    monkeypatch.setattr(module, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(module, "GEMINI_API_KEY", "test-key-not-used")
    monkeypatch.setattr(module, "GEMINI_MODEL", "gemini-3.5-flash-lite")
    monkeypatch.setattr(module, "GEMINI_FALLBACK_MODEL", "gemini-3.6-flash")
    monkeypatch.setattr(module.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(module.asyncio, "sleep", fake_sleep)

    result = asyncio.run(module.llm_result(2, pages, prior_findings=rejected_prior))
    assert len(result["findings"]) == 4
    assert all(item["verification"]["status"] == "screen_passed" for item in result["findings"])
    assert len(requests) == 1
    assert result["findings_verification"]["prior_findings_rejected_count"] == 2
    assert result["findings_verification"]["repair_attempted"] is False


def test_audit_finding_does_not_confuse_significant_with_not_significant():
    pages = [{
        "page": 4,
        "text": "The coefficient is not statistically significant at the 10 percent level.",
    }]
    finding = {
        "claim": "계수는 통계적으로 유의하다.",
        "direction": "positive",
        "estimate": "0.03",
        "statistical_significance": "statistically significant at 10% level",
        "evidence": [{"page": 4, "quote": "The coefficient is not statistically significant at the 10 percent level."}],
    }
    audit = module.audit_finding(finding, pages)
    assert audit["status"] == "review"
    assert audit["significance_supported"] is False



def test_numeric_tokenizer_normalizes_unicode_minus_and_does_not_treat_date_ranges_as_negative():
    assert module._extract_numeric_tokens("ESG −0.0017 ***; period 2001–2020") == [
        "-0.0017", "2001", "2020"
    ]
    assert module._numeric_key("−0.0017") == "-0.0017"


def test_audit_finding_accepts_unicode_minus_in_cited_pdf_table():
    pages = [{
        "page": 8,
        "text": "The ESG coefficient is −0.0017 *** and the momentum coefficient is −0.0019 ***.",
    }]
    finding = {
        "claim": "ESG 점수는 주식 수익률과 음(-)의 관계를 보인다.",
        "direction": "negative",
        "estimate": "-0.0017",
        "statistical_significance": "확인 불가",
        "evidence": [{
            "page": 8,
            "quote": "The ESG coefficient is −0.0017 *** and the momentum coefficient is −0.0019 ***.",
        }],
    }
    audit = module.audit_finding(finding, pages)
    assert audit["status"] == "screen_passed"
    assert audit["numeric_supported"] is True
    assert audit["unsupported_numeric_tokens"] == []


def test_panel_dimensions_calculates_total_only_for_evidence_backed_balanced_panel():
    pages = [{
        "page": 4,
        "text": "The balanced panel consists of 12 portfolios observed over 4,950 daily periods, giving 59,400 portfolio-day observations.",
    }]
    quote = "The balanced panel consists of 12 portfolios observed over 4,950 daily periods, giving 59,400 portfolio-day observations."
    evidence = [{"page": 4, "quote": quote}]
    base = {
        "study_design_type": "balanced_panel",
        "study_design_evidence": evidence,
        "panel_balance": "balanced",
        "panel_balance_evidence": evidence,
        "cross_sectional_units_count": 12,
        "time_periods_count": 4950,
        "observation_frequency": "daily",
        "observation_unit": "portfolio-day",
        "sample_count_reports": [],
        "evidence": evidence,
    }
    consistent = module.audit_panel_dimensions({
        **base, "reported_total_observations_count": 59400,
    }, pages)
    assert consistent["calculated_total_observations_count"] == 59400
    assert consistent["consistency_status"] == "consistent"

    mismatch = module.audit_panel_dimensions({
        **base, "reported_total_observations_count": 4950,
    }, pages)
    assert mismatch["calculated_total_observations_count"] == 59400
    assert mismatch["consistency_status"] == "mismatch"


def test_unbalanced_panel_does_not_apply_n_times_t_multiplication():
    quote = "The unbalanced panel contains 3,856 stocks over 81 quarters with 84,345 observations."
    pages = [{"page": 1, "text": quote}]
    evidence = [{"page": 1, "quote": quote}]
    result = module.audit_panel_dimensions({
        "study_design_type": "unbalanced_panel",
        "study_design_evidence": evidence,
        "panel_balance": "unbalanced",
        "panel_balance_evidence": evidence,
        "cross_sectional_units_count": 3856,
        "time_periods_count": 81,
        "reported_total_observations_count": 84345,
        "observation_frequency": "quarterly",
        "observation_unit": "stock-quarter",
        "sample_count_reports": [{
            "metric": "total_observations", "label": "overall", "count": 84345,
            "section": "table", "evidence": evidence,
        }],
        "evidence": evidence,
    }, pages)
    assert result["consistency_status"] == "not_applicable_unbalanced"
    assert result["calculated_total_observations_count"] is None
    assert result["reported_total_observations_count"] == 84345


def test_non_panel_portfolio_optimization_does_not_calculate_pseudo_panel_total():
    quote = "The portfolio optimization uses up to 40 stocks and 1,250 daily trading observations."
    pages = [{"page": 8, "text": quote}]
    evidence = [{"page": 8, "quote": quote}]
    result = module.audit_panel_dimensions({
        "study_design_type": "portfolio_optimization",
        "study_design_evidence": evidence,
        "panel_balance": "not_applicable",
        "panel_balance_evidence": evidence,
        "cross_sectional_units_count": 40,
        "time_periods_count": 1250,
        "reported_total_observations_count": 0,
        "observation_frequency": "daily",
        "observation_unit": "stock-day",
        "sample_count_reports": [],
        "evidence": evidence,
    }, pages)
    assert result["consistency_status"] == "not_applicable_design"
    assert result["calculated_total_observations_count"] is None


def test_sample_count_conflicts_are_preserved_instead_of_collapsed():
    abstract_quote = "The pre-crisis, post-crisis, and overall periods comprise 365, 650, and 1,085 observations."
    method_quote = "The pre-crisis, post-crisis, and overall periods comprise 366, 606, and 1,086 observations."
    table_quote = "Table 1 reports 365 pre-crisis, 605 post-crisis, and 1,085 overall observations."
    pages = [
        {"page": 1, "text": abstract_quote},
        {"page": 5, "text": method_quote},
        {"page": 10, "text": table_quote},
    ]
    result = module.audit_panel_dimensions({
        "study_design_type": "unbalanced_panel",
        "study_design_evidence": [{"page": 5, "quote": method_quote}],
        "panel_balance": "unbalanced",
        "panel_balance_evidence": [{"page": 5, "quote": method_quote}],
        "cross_sectional_units_count": 0,
        "time_periods_count": 0,
        "reported_total_observations_count": 0,
        "observation_frequency": "monthly",
        "observation_unit": "country-month",
        "sample_count_reports": [
            {"metric": "subsample_observations", "label": "pre-crisis", "count": 365, "section": "abstract", "evidence": [{"page": 1, "quote": abstract_quote}]},
            {"metric": "subsample_observations", "label": "pre-crisis", "count": 366, "section": "methodology", "evidence": [{"page": 5, "quote": method_quote}]},
            {"metric": "subsample_observations", "label": "post-crisis", "count": 650, "section": "abstract", "evidence": [{"page": 1, "quote": abstract_quote}]},
            {"metric": "subsample_observations", "label": "post-crisis", "count": 606, "section": "methodology", "evidence": [{"page": 5, "quote": method_quote}]},
            {"metric": "total_observations", "label": "overall", "count": 1085, "section": "abstract", "evidence": [{"page": 1, "quote": abstract_quote}]},
            {"metric": "total_observations", "label": "overall", "count": 1086, "section": "methodology", "evidence": [{"page": 5, "quote": method_quote}]},
            {"metric": "total_observations", "label": "overall", "count": 1085, "section": "table 1", "evidence": [{"page": 10, "quote": table_quote}]},
        ],
        "evidence": [{"page": 1, "quote": abstract_quote}],
    }, pages)
    assert result["consistency_status"] == "source_conflict"
    assert len(result["source_conflicts"]) == 3
    assert result["calculated_total_observations_count"] is None
    assert {item["count"] for item in result["sample_count_reports"]} >= {365, 366, 1085, 1086}


def test_deduplicate_findings_removes_near_duplicate_claims_but_keeps_distinct_results():
    pages = [{
        "page": 9,
        "text": (
            "The amortized liquidity coefficient is positive and significant in all models. "
            "The average liquidity premium is 0.019 percentage points monthly."
        ),
    }]
    quote = "The amortized liquidity coefficient is positive and significant in all models."
    first = {
        "claim": "상각 유동성 계수는 모든 모형에서 양(+)이고 통계적으로 유의하다.",
        "direction": "positive",
        "estimate": "2.394 to 2.667",
        "statistical_significance": "p < 0.01",
        "evidence": [{"page": 9, "quote": quote}],
    }
    duplicate = {
        "claim": "모든 모형에서 상각된 유동성 측정치의 계수는 양수이며 통계적으로 유의미하다.",
        "direction": "positive",
        "estimate": "2.394–2.667",
        "statistical_significance": "p < 0.01",
        "evidence": [{"page": 9, "quote": quote}],
    }
    distinct = {
        "claim": "평균 총 유동성 프리미엄은 월 0.019%p이다.",
        "direction": "positive",
        "estimate": "0.019",
        "statistical_significance": "확인 불가",
        "evidence": [{
            "page": 9,
            "quote": "The average liquidity premium is 0.019 percentage points monthly.",
        }],
    }
    result, removed = module._deduplicate_findings([first, duplicate, distinct], pages)
    assert removed == 1
    assert len(result) == 2


def test_methodology_schema_requires_field_level_evidence_and_panel_dimensions():
    props = module.METHODOLOGY_SCHEMA["properties"]
    assert "design_evidence" in props
    assert "sample_evidence" in props
    assert "period_evidence" in props
    assert "panel_dimensions" in props
    panel_props = module.PANEL_DIMENSIONS_SCHEMA["properties"]
    assert panel_props["cross_sectional_units_count"]["type"] == "integer"
    assert panel_props["time_periods_count"]["type"] == "integer"
    assert "study_design_type" in panel_props
    assert "sample_count_reports" in panel_props
    assert set(module.METHODOLOGY_ONLY_SCHEMA["required"]) == {"methodology"}


def test_methodology_repair_prompt_requests_panel_units_and_field_citations():
    pages = [
        {"page": 1, "text": "Abstract: We study asset pricing."},
        {"page": 2, "text": "Data and sample: 12 portfolios are observed over 4,950 daily periods."},
        {"page": 3, "text": "Methodology: We estimate a panel model using the Mean Group estimator."},
    ]
    prompt = module.build_methodology_repair_prompt(pages)
    assert "cross_sectional_units_count" in prompt
    assert "reported_total_observations_count" in prompt
    assert "sample_count_reports" in prompt
    assert "sample_evidence" in prompt
    assert "[PDF PAGE 2]" in prompt
    assert "[PDF PAGE 3]" in prompt


def test_llm_result_runs_methodology_only_repair_when_section_evidence_is_missing(monkeypatch):
    pages = _sample_pages()
    first_output = _sample_model_output()
    first_output["methodology"]["evidence"] = []
    first_output["methodology"]["variables"] = []
    for key in ("design", "sample", "period", "data_sources", "empirical_strategy", "identification_strategy", "equations"):
        first_output["methodology"][f"{key}_evidence"] = []
    first_output["methodology"]["panel_dimensions"] = {
        "study_design_type": "unknown",
        "study_design_evidence": [],
        "panel_balance": "unknown",
        "panel_balance_evidence": [],
        "cross_sectional_units_count": 0,
        "time_periods_count": 0,
        "reported_total_observations_count": 0,
        "observation_frequency": "확인 불가",
        "observation_unit": "확인 불가",
        "sample_count_reports": [],
        "evidence": [],
    }
    repair_output = {
        "methodology": {
            "design": "은행 패널 회귀분석",
            "design_evidence": [{
                "page": 1,
                "quote": "We use a panel of 50 banks from 2001 to 2020.",
            }],
            "sample": "50개 은행",
            "sample_evidence": [{
                "page": 1,
                "quote": "We use a panel of 50 banks from 2001 to 2020.",
            }],
            "period": "2001년부터 2020년",
            "period_evidence": [{
                "page": 1,
                "quote": "We use a panel of 50 banks from 2001 to 2020.",
            }],
            "data_sources": ["은행 패널 자료"],
            "data_sources_evidence": [{
                "page": 1,
                "quote": "We use a panel of 50 banks from 2001 to 2020.",
            }],
            "variables": [{
                "name": "loan growth",
                "role": "종속변수",
                "definition": "대출 증가율",
                "evidence": [{
                    "page": 1,
                    "quote": "The dependent variable is loan growth.",
                }],
            }],
            "empirical_strategy": "패널 회귀분석",
            "empirical_strategy_evidence": [{
                "page": 2,
                "quote": "The estimated coefficient is -0.12 and statistically significant at the 5 percent level.",
            }],
            "identification_strategy": "확인 불가",
            "identification_strategy_evidence": [],
            "equations": [],
            "evidence": [{
                "page": 1,
                "quote": "We use a panel of 50 banks from 2001 to 2020.",
            }],
            "panel_dimensions": {
                "study_design_type": "balanced_panel",
                "study_design_evidence": [{
                    "page": 1,
                    "quote": "The panel is balanced and annual, with 50 banks observed for 20 years.",
                }],
                "panel_balance": "balanced",
                "panel_balance_evidence": [{
                    "page": 1,
                    "quote": "The panel is balanced and annual, with 50 banks observed for 20 years.",
                }],
                "cross_sectional_units_count": 50,
                "time_periods_count": 20,
                "reported_total_observations_count": 0,
                "observation_frequency": "annual",
                "observation_unit": "bank-year",
                "sample_count_reports": [],
                "evidence": [{
                    "page": 1,
                    "quote": "The panel is balanced and annual, with 50 banks observed for 20 years.",
                }],
            },
        }
    }
    requests = []

    class FakeResponse:
        status_code = 200
        headers = {}
        text = ""
        def __init__(self, payload):
            self.payload = payload
        def raise_for_status(self):
            return None
        def json(self):
            return {"candidates": [{
                "finishReason": "STOP",
                "content": {"parts": [{"text": json.dumps(self.payload, ensure_ascii=False)}]},
            }]}

    class FakeClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        async def post(self, url, **kwargs):
            requests.append((url, kwargs))
            return FakeResponse(first_output if len(requests) == 1 else repair_output)

    async def fake_sleep(seconds):
        return None

    monkeypatch.setattr(module, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(module, "GEMINI_API_KEY", "test-key-not-used")
    monkeypatch.setattr(module, "GEMINI_MODEL", "gemini-3.5-flash-lite")
    monkeypatch.setattr(module, "GEMINI_FALLBACK_MODEL", "gemini-3.6-flash")
    monkeypatch.setattr(module.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(module.asyncio, "sleep", fake_sleep)

    result = asyncio.run(module.llm_result(2, pages))
    assert len(requests) == 2
    assert requests[1][1]["json"]["generationConfig"]["responseJsonSchema"] == module.METHODOLOGY_ONLY_SCHEMA
    assert result["methodology_verification"]["repair_attempted"] is True
    assert result["methodology_verification"]["repair_status"] == "recovered"
    assert result["methodology"]["design"] == "은행 패널 회귀분석"
    assert result["methodology"]["sample"] == "50개 은행"
    assert "gemini-3.5-flash-lite" in result["models_used"]



def test_overall_methodology_quote_does_not_substitute_for_sample_field_evidence():
    raw = _sample_model_output()
    raw["methodology"]["sample_evidence"] = []
    result = module.normalize_llm_result(raw, 2, _sample_pages())
    assert result["methodology"]["design"] == "은행 패널 분석"
    assert result["methodology"]["sample"] == "확인 불가"
    assert result["methodology"]["sample_evidence"] == []
    assert module._methodology_needs_repair(result["methodology"])



def test_significance_star_without_legend_is_not_misclassified_as_false():
    quote = "ESG −0.0017 ***"
    pages = [{"page": 7, "text": quote}]
    finding = {
        "claim": "ESG 점수 계수는 음(-)이다.",
        "direction": "negative",
        "estimate": "-0.0017",
        "statistical_significance": "1% 수준에서 유의함",
        "evidence": [{"page": 7, "quote": quote}],
        "significance_legend_evidence": [],
    }
    audit = module.audit_finding(finding, pages)
    assert audit["numeric_supported"] is True
    assert audit["significance_supported"] is None
    assert audit["status"] == "screen_passed"


def test_significance_star_uses_separate_table_legend_evidence():
    table_quote = "ESG −0.0017 ***"
    legend_quote = "***, **, and * denote significance at the 1%, 5%, and 10% levels, respectively."
    pages = [
        {"page": 7, "text": table_quote},
        {"page": 8, "text": legend_quote},
    ]
    finding = {
        "claim": "ESG 점수 계수는 음(-)이다.",
        "direction": "negative",
        "estimate": "-0.0017",
        "statistical_significance": "1% 수준에서 유의함",
        "evidence": [{"page": 7, "quote": table_quote}],
        "significance_legend_evidence": [{"page": 8, "quote": legend_quote}],
    }
    audit = module.audit_finding(finding, pages)
    assert audit["significance_supported"] is True
    assert audit["significance_legend_checked"] is True


def test_significance_claim_stricter_than_source_level_is_flagged():
    quote = "The coefficient is statistically significant at the 5 percent level."
    pages = [{"page": 3, "text": quote}]
    finding = {
        "claim": "계수는 1% 수준에서 유의하다.",
        "direction": "positive",
        "estimate": "0.12",
        "statistical_significance": "1% level",
        "evidence": [{"page": 3, "quote": quote}],
    }
    audit = module.audit_finding(finding, pages)
    assert audit["significance_supported"] is False
    assert audit["status"] == "review"


def test_explicit_p_value_is_compared_to_source_p_value():
    quote = "The coefficient is negative with p = 0.0054."
    pages = [{"page": 3, "text": quote}]
    finding = {
        "claim": "계수는 음(-)의 효과를 보인다.",
        "direction": "negative",
        "estimate": "-0.12",
        "statistical_significance": "p = 0.0054",
        "evidence": [{"page": 3, "quote": quote}],
    }
    audit = module.audit_finding(finding, pages)
    assert audit["significance_supported"] is True


def test_summary_consistency_flags_results_without_structured_findings():
    result = module.audit_summary_consistency(
        "분석 결과 변수 X는 수익률에 음(-)의 영향을 미치며 계수는 -0.12이다.",
        [],
        {"design": "패널 회귀분석", "sample": "50개 은행", "period": "2001~2020년", "panel_dimensions": {}},
    )
    assert result["status"] == "review"
    assert "summary_mentions_empirical_results_but_findings_empty" in result["reasons"]
    assert "-0.12" in result["unmatched_numeric_tokens"]


def test_summary_consistency_accepts_numbers_present_in_findings_and_methodology():
    result = module.audit_summary_consistency(
        "분석 결과 계수는 -0.12이다. 표본은 50개 은행이며 기간은 2001~2020년이다.",
        [{"claim": "계수는 -0.12이다.", "estimate": "-0.12", "statistical_significance": "확인 불가"}],
        {"design": "패널 회귀분석", "sample": "50개 은행", "period": "2001~2020년", "panel_dimensions": {}},
    )
    assert result["status"] == "screen_passed"
    assert result["unmatched_numeric_tokens"] == []



def test_findings_coverage_marks_result_bearing_paper_incomplete_when_empty():
    pages = [
        {"page": 1, "text": "Abstract and research question."},
        {"page": 8, "text": "Table 4. Regression results. Estimated coefficient is statistically significant."},
    ]
    coverage = module.assess_findings_coverage(pages, [])
    assert coverage["status"] == "incomplete"
    assert coverage["empirical_result_signals_detected"] is True


def test_findings_coverage_does_not_invent_missing_results_for_non_empirical_paper():
    pages = [{"page": 1, "text": "This paper proposes a theoretical framework."}]
    coverage = module.assess_findings_coverage(pages, [])
    assert coverage["status"] == "not_assessable"
    assert coverage["empirical_result_signals_detected"] is False


def test_findings_rescue_prompt_prioritizes_tables_and_does_not_infer_results():
    pages = [
        {"page": 1, "text": "Abstract and introduction."},
        {"page": 2, "text": "Table 2. Regression results. Coefficient and standard errors."},
    ]
    prompt = module.build_findings_rescue_prompt(pages)
    assert "표 중심 추출 전문가" in prompt
    assert "[PDF PAGE 2]" in prompt
    assert "빈 배열을 채우기 위해 추정" in prompt


def test_llm_result_runs_table_first_rescue_only_after_empty_findings(monkeypatch):
    pages = _sample_pages()
    first_output = _sample_model_output()
    first_output["findings"] = []
    empty_repair = {"findings": []}
    rescue_output = {
        "findings": [{
            "claim": "추정계수는 -0.12이며 5% 수준에서 유의하다.",
            "direction": "negative",
            "estimate": "-0.12",
            "statistical_significance": "5% level",
            "evidence": [{
                "page": 2,
                "quote": "The estimated coefficient is -0.12 and statistically significant at the 5 percent level."
            }],
        }]
    }
    requests = []

    class FakeResponse:
        status_code = 200
        headers = {}
        text = ""
        def __init__(self, payload):
            self.payload = payload
        def raise_for_status(self):
            return None
        def json(self):
            return {"candidates": [{
                "finishReason": "STOP",
                "content": {"parts": [{"text": json.dumps(self.payload, ensure_ascii=False)}]},
            }]}

    class FakeClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        async def post(self, url, **kwargs):
            requests.append({**kwargs, "url": url})
            payload = first_output if len(requests) == 1 else empty_repair if len(requests) == 2 else rescue_output
            return FakeResponse(payload)

    async def fake_sleep(seconds):
        return None

    monkeypatch.setattr(module, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(module, "GEMINI_API_KEY", "test-key-not-used")
    monkeypatch.setattr(module, "GEMINI_MODEL", "gemini-3.5-flash-lite")
    monkeypatch.setattr(module, "GEMINI_FALLBACK_MODEL", "gemini-3.6-flash")
    monkeypatch.setattr(module.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(module.asyncio, "sleep", fake_sleep)

    result = asyncio.run(module.llm_result(2, pages))
    assert len(requests) == 3
    assert requests[2]["json"]["generationConfig"]["responseJsonSchema"] == module.FINDINGS_ONLY_SCHEMA
    assert "gemini-3.6-flash" in requests[2]["url"]
    assert result["findings_verification"]["rescue_attempted"] is True
    assert result["findings_verification"]["rescue_status"] == "recovered"
    assert result["findings_coverage"]["status"] == "supported"
    assert len(result["findings"]) == 1


def test_llm_result_runs_table_first_rescue_when_findings_only_need_review(monkeypatch):
    pages = _sample_pages() + [
        {
            "page": 11,
            "text": (
                "The results in Table 9 show that unexpected liquidity risk is "
                "negatively related to excess stock returns."
            ),
        },
        {
            "page": 12,
            "text": (
                "Table 9. Unexpected stock illiquidity. "
                "AR_Amihud −0.154*** (0.048). "
                "Note: *** p < 0.01, ** p < 0.05, * p < 0.10."
            ),
        },
    ]
    review_finding = {
        "claim": "AR_Amihud 계수는 음(-)이며 1% 수준에서 유의하다.",
        "direction": "negative",
        "estimate": "-0.154",
        "statistical_significance": "1% level",
        "table_reference": "Table 9",
        "model_or_column": "AR_Amihud",
        "evidence": [{
            "page": 11,
            "quote": (
                "The results in Table 9 show that unexpected liquidity risk is "
                "negatively related to excess stock returns."
            ),
        }],
    }
    initial_output = _sample_model_output()
    initial_output["findings"] = [review_finding]
    repair_output = {"findings": [review_finding]}
    rescue_output = {
        "findings": [{
            **review_finding,
            "evidence": [{
                "page": 12,
                "quote": "AR_Amihud −0.154*** (0.048)",
            }],
            "significance_legend_evidence": [{
                "page": 12,
                "quote": "*** p < 0.01, ** p < 0.05, * p < 0.10",
            }],
        }]
    }
    requests = []

    class FakeResponse:
        status_code = 200
        headers = {}
        text = ""

        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return {"candidates": [{
                "finishReason": "STOP",
                "content": {"parts": [{
                    "text": json.dumps(self.payload, ensure_ascii=False)
                }]},
            }]}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, **kwargs):
            requests.append({**kwargs, "url": url})
            payload = (
                initial_output if len(requests) == 1
                else repair_output if len(requests) == 2
                else rescue_output
            )
            return FakeResponse(payload)

    async def fake_sleep(seconds):
        return None

    monkeypatch.setattr(module, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(module, "GEMINI_API_KEY", "test-key-not-used")
    monkeypatch.setattr(module, "GEMINI_MODEL", "gemini-3.5-flash-lite")
    monkeypatch.setattr(module, "GEMINI_FALLBACK_MODEL", "gemini-3.6-flash")
    monkeypatch.setattr(module.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(module.asyncio, "sleep", fake_sleep)

    result = asyncio.run(module.llm_result(12, pages))
    assert len(requests) == 3
    assert "gemini-3.6-flash" in requests[2]["url"]
    assert result["findings_verification"]["repair_attempted"] is True
    assert result["findings_verification"]["rescue_attempted"] is True
    assert result["findings_verification"]["rescue_reason"] == "review_only_findings"
    assert result["findings_verification"]["rescue_status"] == "recovered"
    assert result["findings_coverage"]["status"] == "supported"
    assert len(result["findings"]) == 1
    assert result["findings"][0]["verification"]["status"] == "screen_passed"
    assert result["findings"][0]["verification"]["numeric_supported"] is True
    assert result["findings"][0]["verification"]["significance_supported"] is True
    assert {item["page"] for item in result["findings"][0]["evidence"]} == {11, 12}


def test_llm_result_skips_third_pass_when_supported_findings_remain(monkeypatch):
    pages = _sample_pages() + [
        {
            "page": 11,
            "text": (
                "The results in Table 9 show that unexpected liquidity risk is "
                "negatively related to excess stock returns."
            ),
        },
        {
            "page": 12,
            "text": (
                "Table 9. Unexpected stock illiquidity. "
                "AR_Amihud −0.154*** (0.048). "
                "Note: *** p < 0.01, ** p < 0.05, * p < 0.10."
            ),
        },
    ]
    review_finding = {
        "claim": "AR_Amihud 계수는 음(-)이며 1% 수준에서 유의하다.",
        "direction": "negative",
        "estimate": "-0.154",
        "statistical_significance": "1% level",
        "table_reference": "Table 9",
        "model_or_column": "AR_Amihud Column (1)",
        "evidence": [{
            "page": 11,
            "quote": (
                "The results in Table 9 show that unexpected liquidity risk is "
                "negatively related to excess stock returns."
            ),
        }],
    }
    initial_output = _sample_model_output()
    supported_finding = initial_output["findings"][0]
    initial_output["findings"] = [supported_finding, review_finding]
    repair_output = {"findings": [review_finding]}
    rescue_output = {
        "findings": [{
            **review_finding,
            "evidence": [{
                "page": 12,
                "quote": "AR_Amihud −0.154*** (0.048)",
            }],
            "significance_legend_evidence": [{
                "page": 12,
                "quote": "*** p < 0.01, ** p < 0.05, * p < 0.10",
            }],
        }]
    }
    requests = []

    class FakeResponse:
        status_code = 200
        headers = {}
        text = ""

        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return {"candidates": [{
                "finishReason": "STOP",
                "content": {"parts": [{
                    "text": json.dumps(self.payload, ensure_ascii=False)
                }]},
            }]}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, **kwargs):
            requests.append({**kwargs, "url": url})
            payload = (
                initial_output if len(requests) == 1
                else repair_output if len(requests) == 2
                else rescue_output
            )
            return FakeResponse(payload)

    async def fake_sleep(seconds):
        return None

    monkeypatch.setattr(module, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(module, "GEMINI_API_KEY", "test-key-not-used")
    monkeypatch.setattr(module, "GEMINI_MODEL", "gemini-3.5-flash-lite")
    monkeypatch.setattr(module, "GEMINI_FALLBACK_MODEL", "gemini-3.6-flash")
    monkeypatch.setattr(module.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(module.asyncio, "sleep", fake_sleep)

    result = asyncio.run(module.llm_result(12, pages))
    # The focused repair pass has already run. Do not pay for a third full
    # table-first model call while at least one supported finding remains.
    assert len(requests) == 2
    assert result["findings_verification"]["rescue_attempted"] is False
    assert result["findings_verification"]["rescue_status"] == "not_needed"
    assert result["findings_coverage"]["supported_findings_count"] == 1
    assert result["findings_coverage"]["review_findings_count"] == 1
    assert sorted(item["verification"]["status"] for item in result["findings"]) == [
        "review", "screen_passed"
    ]


def test_llm_result_marks_findings_incomplete_if_table_first_rescue_still_empty(monkeypatch):
    pages = _sample_pages()
    first_output = _sample_model_output()
    first_output["findings"] = []
    requests = []

    class FakeResponse:
        status_code = 200
        headers = {}
        text = ""
        def __init__(self, payload):
            self.payload = payload
        def raise_for_status(self):
            return None
        def json(self):
            return {"candidates": [{
                "finishReason": "STOP",
                "content": {"parts": [{"text": json.dumps(self.payload, ensure_ascii=False)}]},
            }]}

    class FakeClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        async def post(self, url, **kwargs):
            requests.append(kwargs)
            return FakeResponse(first_output if len(requests) == 1 else {"findings": []})

    async def fake_sleep(seconds):
        return None

    monkeypatch.setattr(module, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(module, "GEMINI_API_KEY", "test-key-not-used")
    monkeypatch.setattr(module, "GEMINI_MODEL", "gemini-3.5-flash-lite")
    monkeypatch.setattr(module, "GEMINI_FALLBACK_MODEL", "gemini-3.6-flash")
    monkeypatch.setattr(module.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(module.asyncio, "sleep", fake_sleep)

    result = asyncio.run(module.llm_result(2, pages))
    assert len(requests) == 3
    assert result["findings_verification"]["rescue_status"] == "no_supported_findings"
    assert result["findings_coverage"]["status"] == "incomplete"
    assert any("실증 결과 추출은 불완전" in warning for warning in result["warnings"])



def test_significance_legend_uses_validated_excerpt_not_unrelated_page_stars():
    table_quote = "NIBDepRat*SFFR 0.000615*** (0.000)"
    legend_quote = "p values in parentheses * p < 0.10, ** p < 0.05, *** p < 0.01"
    pages = [
        {"page": 7, "text": table_quote},
        {
            "page": 8,
            "text": (
                "Table 1 unrelated results * p < 0.10 ** p < 0.05 "
                "Table 2 other model *** p < 0.05. Notes: " + legend_quote
            ),
        },
    ]
    finding = {
        "claim": "무이자예금 교호항은 양(+)이며 1% 수준에서 유의하다.",
        "direction": "positive",
        "estimate": "0.000615",
        "statistical_significance": "p < 0.01",
        "evidence": [{"page": 7, "quote": table_quote}],
        "significance_legend_evidence": [{"page": 8, "quote": legend_quote}],
    }
    audit = module.audit_finding(finding, pages)
    assert audit["significance_supported"] is True
    assert audit["status"] == "screen_passed"


def test_written_portfolio_fraction_audits_both_counts_without_relaxing_estimates():
    quote = "Four out of six portfolios improve, with an estimated coefficient of -0.12."
    pages = [{"page": 6, "text": quote}]
    assert module._extract_written_count_tokens(quote) == ["4", "6"]
    assert module._extract_written_count_tokens("four of the six portfolios") == ["4", "6"]
    assert module._extract_written_count_tokens("four out of six times higher") == []

    finding = {
        "claim": "Four out of six portfolios improve; the coefficient is -0.12.",
        "estimate": "-0.12",
        "direction": "negative",
        "evidence": [{"page": 6, "quote": quote}],
    }
    supported = module.audit_finding(finding, pages)
    assert supported["numeric_supported"] is True
    assert supported["status"] == "screen_passed"

    wrong_count = module.audit_finding({**finding, "claim": "Five out of six portfolios improve."}, pages)
    assert wrong_count["numeric_supported"] is False
    assert "5" in wrong_count["unsupported_numeric_tokens"]
    assert wrong_count["status"] == "review"

    wrong_coefficient = module.audit_finding({**finding, "estimate": "-0.99"}, pages)
    assert wrong_coefficient["numeric_supported"] is False
    assert "-0.99" in wrong_coefficient["unsupported_numeric_tokens"]
    assert wrong_coefficient["status"] == "review"
