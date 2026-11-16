from benchmark import full_analysis_replay as replay

def test_collects_nested_legends_and_deduplicates():
    result={"findings":[{"evidence":[{"page":1,"quote":"alpha"}],
                         "significance_legend_evidence":[{"page":2,"quote":"star"}]}],
            "evidence":[{"page":1,"quote":"alpha"}]}
    assert replay.all_page_quotes(result)==[{"page":1,"quote":"alpha"},{"page":2,"quote":"star"}]

def test_unsupported_replay_evidence_is_not_fabricated():
    historical={"findings":[{"claim":"coef 0.45","estimate":"0.45",
                             "evidence":[{"page":1,"quote":"coefficient 0.45"}]}]}
    metrics=replay.review_historical_against_pages(historical,[{"page":1,"text":"different text"}])
    assert metrics["stored_findings"]==1
    assert metrics["findings_preserving_direct_source_evidence"]==0
    assert metrics["citations_revalidated_on_parsed_page_text"]==0
