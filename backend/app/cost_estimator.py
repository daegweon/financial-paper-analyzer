from __future__ import annotations
import json
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

DEFAULT_CATALOG = Path(__file__).with_name('model_price_catalog.json')

def load_catalog(path: Path = DEFAULT_CATALOG) -> dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))

def validate_catalog(catalog: dict[str, Any]) -> None:
    rows = catalog.get('prices')
    if not isinstance(rows, list):
        raise ValueError('prices must be a list')
    seen = set()
    for row in rows:
        start = date.fromisoformat(row['effective_from'])
        end = date.fromisoformat(row['effective_until']) if row.get('effective_until') else None
        if end is not None and end <= start:
            raise ValueError('effective_until must be after effective_from')
        key = (row['provider'], row['model'], row['tier'])
        interval = (key, start, end)
        if interval in seen:
            raise ValueError('duplicate price interval')
        seen.add(interval)
    for i, left in enumerate(rows):
        for right in rows[i + 1:]:
            if (left['provider'], left['model'], left['tier']) != (right['provider'], right['model'], right['tier']):
                continue
            ls = date.fromisoformat(left['effective_from'])
            le = date.fromisoformat(left['effective_until']) if left.get('effective_until') else date.max
            rs = date.fromisoformat(right['effective_from'])
            re = date.fromisoformat(right['effective_until']) if right.get('effective_until') else date.max
            if max(ls, rs) < min(le, re):
                raise ValueError('overlapping effective price intervals')

def estimate_cost(*, provider: str, model: str, occurred_on: str, billing_mode: str | None, prompt_tokens: int | None, candidate_tokens: int | None, thought_tokens: int | None, catalog: dict[str, Any] | None = None) -> dict[str, Any]:
    if billing_mode == 'free':
        return {'currency': 'USD', 'estimated_cost': '0', 'price_status': 'free_tier_confirmed', 'price_source': None}
    if billing_mode != 'paid_standard':
        return {'currency': 'USD', 'estimated_cost': None, 'price_status': 'billing_mode_unknown', 'price_source': None}
    if any(value is None or not isinstance(value, int) or value < 0 for value in (prompt_tokens, candidate_tokens, thought_tokens)):
        return {'currency': 'USD', 'estimated_cost': None, 'price_status': 'token_usage_incomplete', 'price_source': None}
    when = date.fromisoformat(occurred_on)
    prices = catalog or load_catalog()
    validate_catalog(prices)
    match = next((row for row in prices['prices'] if row['provider'] == provider and row['model'] == model and row['tier'] == 'paid_standard' and date.fromisoformat(row['effective_from']) <= when and (row.get('effective_until') is None or when < date.fromisoformat(row['effective_until']))), None)
    if match is None:
        return {'currency': 'USD', 'estimated_cost': None, 'price_status': 'price_not_found', 'price_source': None}
    output_tokens = candidate_tokens + thought_tokens
    input_cost = Decimal(prompt_tokens) * Decimal(str(match['input_usd_per_million'])) / Decimal(1_000_000)
    output_cost = Decimal(output_tokens) * Decimal(str(match['output_usd_per_million'])) / Decimal(1_000_000)
    total = (input_cost + output_cost).quantize(Decimal('0.00000001'), rounding=ROUND_HALF_UP)
    return {'currency': 'USD', 'estimated_cost': format(total, 'f'), 'price_status': 'estimated_paid_standard', 'price_source': match['source_url'], 'price_effective_from': match['effective_from'], 'input_tokens': prompt_tokens, 'output_tokens_including_thoughts': output_tokens}
