import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.cost_report import build_cost_report

def test_cost_report_groups_per_paper_and_model_and_preserves_unknown_costs():
    events = [
        {'paper_id':'p1','provider':'gemini','model':'gemini-3.5-flash-lite','created_at':'2026-11-20T10:00:00Z','billing_mode':'paid_standard','prompt_tokens':1000000,'candidate_tokens':100000,'thought_tokens':0},
        {'paper_id':'p1','provider':'gemini','model':'gemini-3.5-flash-lite','created_at':'2026-11-20T10:01:00Z','billing_mode':None,'prompt_tokens':1000000,'candidate_tokens':100000,'thought_tokens':0},
    ]
    report = build_cost_report(events)
    row = report['groups'][0]
    assert row['event_count'] == 2
    assert row['known_cost_events'] == 1
    assert row['unknown_cost_events'] == 1
    assert row['estimated_cost_usd'] == 0.00055
    assert row['complete_cost_coverage'] is False

def test_free_tier_is_zero_only_when_explicitly_confirmed():
    event = {'paper_id':'p2','provider':'gemini','model':'gemini-3.6-flash','created_at':'2026-11-20','billing_mode':'free','prompt_tokens':100,'candidate_tokens':100,'thought_tokens':0}
    row = build_cost_report([event])['groups'][0]
    assert row['estimated_cost_usd'] == 0.0
    assert row['known_cost_events'] == 1

def test_unknown_model_does_not_receive_a_guessed_price():
    event = {'paper_id':'p3','provider':'gemini','model':'unknown','created_at':'2026-11-20','billing_mode':'paid_standard','prompt_tokens':100,'candidate_tokens':100,'thought_tokens':0}
    row = build_cost_report([event])['groups'][0]
    assert row['estimated_cost_usd'] == 0.0
    assert row['unknown_cost_events'] == 1