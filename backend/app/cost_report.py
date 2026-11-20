from __future__ import annotations
import argparse
import json
from collections import defaultdict
from pathlib import Path
try:
    from app.cost_estimator import estimate_cost
except ModuleNotFoundError:
    from backend.app.cost_estimator import estimate_cost

def build_cost_report(events, catalog=None):
    groups = defaultdict(lambda: {'event_count': 0, 'known_cost_events': 0, 'unknown_cost_events': 0, 'estimated_cost_usd': 0.0, 'cost_status_counts': {}})
    for event in events:
        if not isinstance(event, dict):
            continue
        key = (str(event.get('paper_id') or 'unknown-paper'), str(event.get('model') or 'unknown-model'))
        result = estimate_cost(
            provider=str(event.get('provider') or ''), model=str(event.get('model') or ''),
            occurred_on=str(event.get('created_at', ''))[:10], billing_mode=event.get('billing_mode'),
            prompt_tokens=event.get('prompt_tokens'), candidate_tokens=event.get('candidate_tokens'),
            thought_tokens=event.get('thought_tokens'), catalog=catalog,
        )
        row = groups[key]
        row['event_count'] += 1
        status = result['price_status']
        row['cost_status_counts'][status] = row['cost_status_counts'].get(status, 0) + 1
        if result['estimated_cost'] is None:
            row['unknown_cost_events'] += 1
        else:
            row['known_cost_events'] += 1
            row['estimated_cost_usd'] += float(result['estimated_cost'])
    output = []
    for (paper_id, model), row in sorted(groups.items()):
        row['estimated_cost_usd'] = round(row['estimated_cost_usd'], 8)
        row['paper_id'] = paper_id
        row['model'] = model
        row['complete_cost_coverage'] = row['unknown_cost_events'] == 0
        output.append(row)
    return {'currency': 'USD', 'groups': output, 'warning': 'Costs are estimates only for explicitly verified billing modes and complete token metadata. Unknown/free-tier billing is not inferred. This report is not an invoice.'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--events', type=Path, required=True, help='JSON array exported from ai_usage_events')
    parser.add_argument('--out', type=Path, default=Path('benchmark/results/ai-cost-report.json'))
    args = parser.parse_args()
    events = json.loads(args.events.read_text(encoding='utf-8'))
    report = build_cost_report(events)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'groups': len(report['groups']), 'known_cost_events': sum(x['known_cost_events'] for x in report['groups']), 'unknown_cost_events': sum(x['unknown_cost_events'] for x in report['groups'])}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()