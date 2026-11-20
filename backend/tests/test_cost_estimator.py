from datetime import date
from app.cost_estimator import estimate_cost, load_catalog, validate_catalog

def test_paid_cost_uses_effective_dated_price_and_includes_thought_tokens():
    result = estimate_cost(provider='gemini', model='gemini-3.6-flash', occurred_on='2026-12-15', billing_mode='paid_standard', prompt_tokens=1_000_000, candidate_tokens=1_000_000, thought_tokens=500_000)
    assert result['estimated_cost'] == '6.37500000'
    assert result['output_tokens_including_thoughts'] == 1_500_000
    assert result['price_effective_from'] == '2026-11-20'

def test_price_increase_is_applied_on_2027_boundary():
    result = estimate_cost(provider='gemini', model='gemini-3.6-flash', occurred_on='2027-01-01', billing_mode='paid_standard', prompt_tokens=1_000_000, candidate_tokens=1_000_000, thought_tokens=0)
    assert result['estimated_cost'] == '9.00000000'
    assert result['price_effective_from'] == '2027-01-01'

def test_unknown_free_tier_and_incomplete_usage_never_invent_cost():
    unknown = estimate_cost(provider='gemini', model='gemini-3.6-flash', occurred_on='2026-12-15', billing_mode=None, prompt_tokens=100, candidate_tokens=100, thought_tokens=0)
    free = estimate_cost(provider='gemini', model='gemini-3.6-flash', occurred_on='2026-12-15', billing_mode='free', prompt_tokens=100, candidate_tokens=100, thought_tokens=0)
    incomplete = estimate_cost(provider='gemini', model='gemini-3.6-flash', occurred_on='2026-12-15', billing_mode='paid_standard', prompt_tokens=100, candidate_tokens=None, thought_tokens=None)
    assert unknown['estimated_cost'] is None and unknown['price_status'] == 'billing_mode_unknown'
    assert free['estimated_cost'] == '0'
    assert incomplete['estimated_cost'] is None and incomplete['price_status'] == 'token_usage_incomplete'

def test_unknown_model_has_no_cost_and_catalog_rejects_overlapping_prices():
    result = estimate_cost(provider='gemini', model='unknown-model', occurred_on='2026-12-15', billing_mode='paid_standard', prompt_tokens=100, candidate_tokens=100, thought_tokens=0)
    assert result['estimated_cost'] is None and result['price_status'] == 'price_not_found'
    catalog = {'prices': [
        {'provider':'gemini','model':'x','tier':'paid_standard','effective_from':'2026-01-01','effective_until':'2026-08-01'},
        {'provider':'gemini','model':'x','tier':'paid_standard','effective_from':'2026-07-01','effective_until':None},
    ]}
    try:
        validate_catalog(catalog)
    except ValueError as exc:
        assert 'overlapping' in str(exc)
    else:
        raise AssertionError('overlapping price periods must be rejected')