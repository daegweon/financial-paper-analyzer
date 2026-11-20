import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.cost_report import build_cost_report

def test_admin_report_groups_usage_without_individual_budgets():
    events = [
        {'user_id':'u1','paper_id':'p1','provider':'gemini','model':'gemini-3.5-flash-lite','created_at':'2026-11-20T10:00:00Z','billing_mode':'paid_standard','prompt_tokens':1000000,'candidate_tokens':100000,'thought_tokens':0},
        {'user_id':'u1','paper_id':'p1','provider':'gemini','model':'gemini-3.5-flash-lite','created_at':'2026-11-20T10:01:00Z','billing_mode':None,'prompt_tokens':1000000,'candidate_tokens':100000,'thought_tokens':0},
    ]
    report = build_cost_report(events, admin_monthly_budget_usd='0.50')
    row = report['groups'][0]
    assert row['event_count'] == 2
    assert row['known_cost_events'] == 1
    assert row['unknown_cost_events'] == 1
    assert row['estimated_cost_usd'] == '0.55000000'
    assert row['cost_coverage_complete'] is False
    monthly = report['admin_monthly_budget'][0]
    assert monthly['budget_status'] == 'exceeded_with_unknown_costs'
    assert monthly['admin_monthly_budget_usd'] == '0.50000000'
    assert len(report['admin_user_usage']) == 1
    assert len(report['admin_paper_usage']) == 1
    assert 'individual budgets' in report['warning']

def test_free_tier_is_zero_only_when_explicitly_confirmed():
    event = {'user_id':'u2','paper_id':'p2','provider':'gemini','model':'gemini-3.6-flash','created_at':'2026-11-20','billing_mode':'free','prompt_tokens':100,'candidate_tokens':100,'thought_tokens':0}
    row = build_cost_report([event])['groups'][0]
    assert row['estimated_cost_usd'] == '0.00000000'
    assert row['known_cost_events'] == 1

def test_unknown_model_does_not_receive_a_guessed_price():
    event = {'user_id':'u3','paper_id':'p3','provider':'gemini','model':'unknown','created_at':'2026-11-20','billing_mode':'paid_standard','prompt_tokens':100,'candidate_tokens':100,'thought_tokens':0}
    row = build_cost_report([event])['groups'][0]
    assert row['estimated_cost_usd'] == '0.00000000'
    assert row['unknown_cost_events'] == 1

def test_admin_budget_is_global_monthly_and_unknown_costs_never_show_within_budget():
    events = [
        {'user_id':'u1','paper_id':'p1','provider':'gemini','model':'gemini-3.5-flash-lite','created_at':'2026-11-20','billing_mode':'paid_standard','prompt_tokens':1000000,'candidate_tokens':100000,'thought_tokens':0},
        {'user_id':'u2','paper_id':'p2','provider':'gemini','model':'gemini-3.5-flash-lite','created_at':'2026-11-21','billing_mode':None,'prompt_tokens':1000,'candidate_tokens':100,'thought_tokens':0},
        {'user_id':'u1','paper_id':'p3','provider':'gemini','model':'gemini-3.5-flash-lite','created_at':'2026-12-01','billing_mode':'paid_standard','prompt_tokens':100000,'candidate_tokens':10000,'thought_tokens':0},
    ]
    report = build_cost_report(events, admin_monthly_budget_usd='0.50')
    nov = next(x for x in report['admin_monthly_budget'] if x['month']=='2026-11')
    assert nov['budget_status'] == 'exceeded_with_unknown_costs'
    assert nov['estimated_cost_usd'] == '0.55000000'
    dec = next(x for x in report['admin_monthly_budget'] if x['month']=='2026-12')
    assert dec['budget_status'] == 'within_budget'
    assert len(report['admin_user_usage']) == 3

def test_invalid_event_timestamp_is_unknown_not_a_crash():
    event = {'user_id':'u1','paper_id':'p1','provider':'gemini','model':'gemini-3.5-flash-lite','created_at':'not-a-date','billing_mode':'paid_standard','prompt_tokens':100,'candidate_tokens':100,'thought_tokens':0}
    row = build_cost_report([event])['groups'][0]
    assert row['unknown_cost_events'] == 1
    assert row['cost_status_counts']['invalid_timestamp'] == 1

def test_cost_groups_preserve_provider_dimension_for_same_model_name():
    events = [
        {"user_id":"u1","paper_id":"p1","provider":"gemini","model":"shared-model","created_at":"2026-11-20","billing_mode":"free","prompt_tokens":1,"candidate_tokens":1,"thought_tokens":0},
        {"user_id":"u1","paper_id":"p1","provider":"openai","model":"shared-model","created_at":"2026-11-20","billing_mode":"free","prompt_tokens":1,"candidate_tokens":1,"thought_tokens":0},
    ]
    groups = build_cost_report(events)["groups"]
    assert len(groups) == 2
    assert {row["provider"] for row in groups} == {"gemini", "openai"}
