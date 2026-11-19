from benchmark.build_review_packet import build_packet


def test_review_packet_preserves_numeric_and_table_context_without_auto_approval():
    manifest = {"papers": [{"id": "B01", "title": "Sample paper"}]}
    results = {"results": [{
        "paper_id": "B01",
        "analysis": {"findings": [{
            "claim": "The coefficient is -0.12",
            "table_reference": "Table 4",
            "model_or_column": "Column (3)",
            "estimate": "-0.12",
            "statistical_significance": "5%",
            "direction": "negative",
            "verification_status": "review_required",
            "evidence": [{"page": 7, "quote": "The coefficient is -0.12 and significant at 5%."}],
        }]},
    }]}
    packet = build_packet(manifest, results)
    assert "B01-F01" in packet
    assert "Table 4" in packet
    assert "Column (3)" in packet
    assert "-0.12" in packet
    assert "PDF p.7" in packet
    assert "승인된 finding 수: 0" in packet


def test_review_packet_never_approves_missing_evidence():
    packet = build_packet(
        {"papers": [{"id": "B02", "title": "No evidence"}]},
        [{"paper_id": "B02", "analysis": {"findings": [{"claim": "unsupported"}]}}],
    )
    assert "직접 인용 근거 없음" in packet
    assert "미검토 / 승인 / 수정 필요 / 기각" in packet
    assert "승인된 finding 수: 0" in packet
