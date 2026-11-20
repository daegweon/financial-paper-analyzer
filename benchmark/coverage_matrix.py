#!/usr/bin/env python3
"""Build topic/method/fact-category coverage matrices from benchmark manifest and scorecard."""
from __future__ import annotations
import argparse
import json
from collections import Counter
from pathlib import Path

def build_coverage_matrix(manifest, scorecard):
    scored = {str(r.get('paper_id')): r for r in scorecard.get('results', []) if isinstance(r, dict) and r.get('paper_id')}
    papers = []
    topic_counts, method_counts, category_counts = Counter(), Counter(), Counter()
    for paper in manifest.get('papers', []):
        pid = str(paper['id'])
        row = scored.get(pid, {})
        missing = set(row.get('gold_fact_missing') or [])
        matched = set(row.get('gold_fact_matches') or [])
        status = 'not_run' if row.get('status') == 'not_run' or not row else 'measured'
        facts = []
        for fact in paper.get('gold_facts', []):
            fid = str(fact.get('id'))
            category = str(fact.get('category', 'uncategorized'))
            outcome = 'missing' if fid in missing else ('matched_screen' if fid in matched else 'unmeasured')
            facts.append({'fact_id': fid, 'category': category, 'weight': fact.get('weight', 1), 'screen_status': outcome})
            category_counts[(category, outcome)] += 1
        topics = paper.get('topic', [])
        methods = paper.get('method_families', [])
        for item in topics: topic_counts[(str(item), status)] += 1
        for item in methods: method_counts[(str(item), status)] += 1
        papers.append({'paper_id': pid, 'title': paper.get('title'), 'status': status, 'topics': topics, 'method_families': methods, 'gold_facts': facts, 'gold_fact_coverage_screen': row.get('gold_fact_coverage_screen')})
    def aggregate(counter):
        keys = sorted({key for key, _ in counter})
        return [{'name': key, 'measured': counter[(key, 'measured')], 'not_run': counter[(key, 'not_run')]} for key in keys]
    return {
        'benchmark_version': manifest.get('benchmark_version'),
        'paper_count': len(papers),
        'analyzed_count': sum(p['status'] == 'measured' for p in papers),
        'not_run_count': sum(p['status'] == 'not_run' for p in papers),
        'topics': aggregate(topic_counts),
        'method_families': aggregate(method_counts),
        'fact_categories': [{'category': key, 'matched_screen': category_counts[(key, 'matched_screen')], 'missing': category_counts[(key, 'missing')], 'unmeasured': category_counts[(key, 'unmeasured')]} for key in sorted({k for k, _ in category_counts})],
        'papers': papers,
        'warning': 'Gold-fact alias matches are screening coverage only, not semantic correctness. Missing facts must be reviewed against the exact publisher PDF.',
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=Path('benchmark/manifest.json'))
    parser.add_argument('--scorecard', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=Path('benchmark/results/coverage-matrix.json'))
    args = parser.parse_args()
    data = build_coverage_matrix(json.loads(args.manifest.read_text(encoding='utf-8')), json.loads(args.scorecard.read_text(encoding='utf-8')))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: data[k] for k in ('paper_count','analyzed_count','not_run_count')}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()