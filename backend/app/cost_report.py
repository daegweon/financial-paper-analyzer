from __future__ import annotations
import argparse
import json
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from datetime import date
try:
    from app.cost_estimator import estimate_cost
except ModuleNotFoundError:
    from backend.app.cost_estimator import estimate_cost

def _money(value: Decimal) -> str:
    return format(value.quantize(Decimal('0.00000001'), rounding=ROUND_HALF_UP), 'f')

def _budget_status(known_cost: Decimal, unknown_count: int, limit: Decimal | None) -> str:
    if limit is None:
        return 'not_configured'
    if known_cost > limit:
        return 'exceeded' if unknown_count == 0 else 'exceeded_with_unknown_costs'
    if unknown_count:
        return 'incomplete_unknown_costs'
    return 'within_budget'

def build_cost_report(events, catalog=None, budgets=None):
    budgets = budgets or {}
    groups = defaultdict(lambda: {'event_count': 0, 'known_cost_events': 0, 'unknown_cost_events': 0, 'estimated_cost_usd': Decimal('0'), 'cost_status_counts': {}})
    user_month = defaultdict(lambda: {'event_count': 0, 'known_cost_events': 0, 'unknown_cost_events': 0, 'estimated_cost_usd': Decimal('0')})
    paper_month = defaultdict(lambda: {'event_count': 0, 'known_cost_events': 0, 'unknown_cost_events': 0, 'estimated_cost_usd': Decimal('0')})
    for event in events:
        if not isinstance(event, dict):
            continue
        paper_id = str(event.get('paper_id') or 'unknown-paper')
        model = str(event.get('model') or 'unknown-model')
        created_at = str(event.get('created_at') or '')
        try:
            month = date.fromisoformat(created_at[:10]).strftime('%Y-%m')
        except ValueError:
            month = 'unknown-period'
        result = estimate_cost(
            provider=str(event.get('provider') or ''), model=model,
            occurred_on=created_at[:10], billing_mode=event.get('billing_mode'),
            prompt_tokens=event.get('prompt_tokens'), candidate_tokens=event.get('candidate_tokens'),
            thought_tokens=event.get('thought_tokens'), catalog=catalog,
        ) if month != 'unknown-period' else {'estimated_cost': None, 'price_status': 'invalid_timestamp'}
        cost = Decimal(result['estimated_cost']) if result['estimated_cost'] is not None else None
        user_id = str(event.get('user_id') or 'unknown-user')
        keys = ((paper_id, model, month), (user_id, month), (paper_id, month))
        for mapping, key in ((groups, keys[0]), (user_month, keys[1]), (paper_month, keys[2])):
            row = mapping[key]
            row['event_count'] += 1
            if cost is None:
                row['unknown_cost_events'] += 1
            else:
                row['known_cost_events'] += 1
                row['estimated_cost_usd'] += cost
            if mapping is groups:
                status = result['price_status']
                row['cost_status_counts'][status] = row['cost_status_counts'].get(status, 0) + 1
    def serialize(mapping, key_names):
        output = []
        for key, row in sorted(mapping.items()):
            item = dict(row)
            item['estimated_cost_usd'] = _money(item['estimated_cost_usd'])
            item['complete_cost_coverage'] = item['unknown_cost_events'] == 0
            item.update(dict(zip(key_names, key)))
            output.append(item)
        return output
    user_limit = Decimal(str(budgets['monthly_user_usd'])) if budgets.get('monthly_user_usd') is not None else None
    paper_limit = Decimal(str(budgets['monthly_paper_usd'])) if budgets.get('monthly_paper_usd') is not None else None
    user_budgets = []
    for item in serialize(user_month, ('user_id', 'month')):
        known = Decimal(item['estimated_cost_usd'])
        item['budget_limit_usd'] = _money(user_limit) if user_limit is not None else None
        item['budget_status'] = _budget_status(known, item['unknown_cost_events'], user_limit)
        user_budgets.append(item)
    paper_budgets = []
    for item in serialize(paper_month, ('paper_id', 'month')):
        known = Decimal(item['estimated_cost_usd'])
        item['budget_limit_usd'] = _money(paper_limit) if paper_limit is not None else None
        item['budget_status'] = _budget_status(known, item['unknown_cost_events'], paper_limit)
        paper_budgets.append(item)
    return {
        'currency': 'USD',
        'groups': serialize(groups, ('paper_id', 'model', 'month')),
        'monthly_user_budgets': user_budgets,
        'monthly_paper_budgets': paper_budgets,
        'warning': 'Estimates only for explicitly verified billing modes and complete token metadata. Unknown costs make budget status incomplete; this report is not an invoice or an automatic spending cap.',
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--events', type=Path, required=True, help='JSON array exported from ai_usage_events')
    parser.add_argument('--monthly-user-budget-usd', type=Decimal)
    parser.add_argument('--monthly-paper-budget-usd', type=Decimal)
    parser.add_argument('--out', type=Path, default=Path('benchmark/results/ai-cost-report.json'))
    args = parser.parse_args()
    events = json.loads(args.events.read_text(encoding='utf-8'))
    report = build_cost_report(events, budgets={'monthly_user_usd': args.monthly_user_budget_usd, 'monthly_paper_usd': args.monthly_paper_budget_usd})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\\n', encoding='utf-8')
    print(json.dumps({'groups': len(report['groups']), 'user_budget_rows': len(report['monthly_user_budgets']), 'paper_budget_rows': len(report['monthly_paper_budgets'])}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()