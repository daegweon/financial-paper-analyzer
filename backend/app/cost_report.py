from __future__ import annotations
import argparse
import json
from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
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
        return 'exceeded_with_unknown_costs' if unknown_count else 'exceeded'
    return 'incomplete_unknown_costs' if unknown_count else 'within_budget'

def build_cost_report(events, catalog=None, admin_monthly_budget_usd=None):
    groups = defaultdict(lambda: {'event_count': 0, 'known_cost_events': 0, 'unknown_cost_events': 0, 'estimated_cost_usd': Decimal('0'), 'cost_status_counts': {}})
    users = defaultdict(lambda: {'event_count': 0, 'known_cost_events': 0, 'unknown_cost_events': 0, 'estimated_cost_usd': Decimal('0')})
    papers = defaultdict(lambda: {'event_count': 0, 'known_cost_events': 0, 'unknown_cost_events': 0, 'estimated_cost_usd': Decimal('0')})
    months = defaultdict(lambda: {'event_count': 0, 'known_cost_events': 0, 'unknown_cost_events': 0, 'estimated_cost_usd': Decimal('0')})
    for event in events:
        if not isinstance(event, dict):
            continue
        paper_id = str(event.get('paper_id') or 'unknown-paper')
        user_id = str(event.get('user_id') or 'unknown-user')
        model = str(event.get('model') or 'unknown-model')
        created_at = str(event.get('created_at') or '')
        try:
            month = date.fromisoformat(created_at[:10]).strftime('%Y-%m')
        except ValueError:
            month = 'unknown-period'
        result = estimate_cost(provider=str(event.get('provider') or ''), model=model, occurred_on=created_at[:10], billing_mode=event.get('billing_mode'), prompt_tokens=event.get('prompt_tokens'), candidate_tokens=event.get('candidate_tokens'), thought_tokens=event.get('thought_tokens'), catalog=catalog) if month != 'unknown-period' else {'estimated_cost': None, 'price_status': 'invalid_timestamp'}
        cost = Decimal(result['estimated_cost']) if result['estimated_cost'] is not None else None
        for mapping, key in ((groups, (paper_id, model, month)), (users, (user_id, month)), (papers, (paper_id, month)), (months, (month,))):
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
            item['cost_coverage_complete'] = item['unknown_cost_events'] == 0
            item.update(dict(zip(key_names, key)))
            output.append(item)
        return output
    budget = Decimal(str(admin_monthly_budget_usd)) if admin_monthly_budget_usd is not None else None
    if budget is not None and budget < 0:
        raise ValueError('admin monthly budget cannot be negative')
    monthly_admin = []
    for item in serialize(months, ('month',)):
        known = Decimal(item['estimated_cost_usd'])
        item['admin_monthly_budget_usd'] = _money(budget) if budget is not None else None
        item['budget_status'] = _budget_status(known, item['unknown_cost_events'], budget)
        monthly_admin.append(item)
    return {
        'currency': 'USD',
        'groups': serialize(groups, ('paper_id', 'model', 'month')),
        'admin_user_usage': serialize(users, ('user_id', 'month')),
        'admin_paper_usage': serialize(papers, ('paper_id', 'month')),
        'admin_monthly_budget': monthly_admin,
        'warning': 'Administrator-only operational estimates. User/paper rows are usage breakdowns, not individual budgets. Unknown costs are excluded from known totals and prevent a within-budget status. This is not an invoice or an automatic spending cap.',
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--events', type=Path, required=True)
    parser.add_argument('--admin-monthly-budget-usd', type=Decimal)
    parser.add_argument('--out', type=Path, default=Path('benchmark/results/ai-cost-report.json'))
    args = parser.parse_args()
    events = json.loads(args.events.read_text(encoding='utf-8'))
    report = build_cost_report(events, admin_monthly_budget_usd=args.admin_monthly_budget_usd)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'model_paper_groups': len(report['groups']), 'admin_months': len(report['admin_monthly_budget'])}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()