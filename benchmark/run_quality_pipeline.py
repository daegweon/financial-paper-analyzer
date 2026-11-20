#!/usr/bin/env python3
"""Run the complete offline PaperSignal benchmark quality workflow."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmark.evaluate import evaluate_one
from benchmark.diagnose import diagnose
from benchmark.build_review_packet import build_packet
from benchmark.quality_dashboard import render_dashboard
from benchmark.compare_scorecards import compare_scorecards
from benchmark.failure_report import summarize_failures

def _load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))

def run_pipeline(manifest, results, out_dir: Path, pages_dir: Path | None = None, reviews=None, baseline=None, logs: Path | None = None):
    rows = results.get('results', results) if isinstance(results, dict) else results
    by_id = {}
    for row in rows if isinstance(rows, list) else []:
        if isinstance(row, dict):
            paper_id = row.get('paper_id') or row.get('benchmark_id')
            analysis = row.get('analysis') or row.get('result')
            if paper_id and isinstance(analysis, dict):
                by_id[str(paper_id)] = analysis
    pages = {}
    if pages_dir:
        for file in pages_dir.glob('*.json'):
            pages[file.stem] = _load(file)
    reviews_map = reviews.get('reviews', reviews) if isinstance(reviews, dict) else {}
    score_rows = []
    for paper in manifest.get('papers', []):
        paper_id = str(paper['id'])
        analysis = by_id.get(paper_id)
        if analysis is None:
            score_rows.append({'paper_id': paper_id, 'title': paper.get('title'), 'status': 'not_run'})
            continue
        page_text = pages.get(paper_id)
        score_rows.append(evaluate_one(paper, analysis, review=reviews_map.get(paper_id), pages=page_text))
    completed = [row for row in score_rows if row.get('status') != 'not_run']
    gold = [row['gold_fact_coverage_screen'] for row in completed if row.get('gold_fact_coverage_screen') is not None]
    human = [row['human_score'] for row in completed if row.get('human_score') is not None]
    scorecard = {
        'benchmark_version': manifest.get('benchmark_version'),
        'paper_count': len(manifest.get('papers', [])),
        'completed_count': len(completed),
        'not_run_count': len(score_rows) - len(completed),
        'mean_gold_fact_coverage_screen': sum(gold) / len(gold) if gold else None,
        'mean_human_score': sum(human) / len(human) if human else None,
        'warning': 'Alias coverage is not semantic accuracy. Human review against publisher PDFs is required.',
        'results': score_rows,
    }
    diagnostics = diagnose(results, pages if pages_dir else None)
    packet = build_packet(manifest, results)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'scorecard.json').write_text(json.dumps(scorecard, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out_dir / 'diagnostics.json').write_text(json.dumps(diagnostics, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out_dir / 'quality-dashboard.html').write_text(render_dashboard(scorecard), encoding='utf-8')
    (out_dir / 'human-review-packet.md').write_text(packet, encoding='utf-8')
    failure_report = None
    if logs is not None:
        with logs.open(encoding='utf-8') as handle:
            failure_report = summarize_failures(handle)
        (out_dir / 'failure-report.json').write_text(json.dumps(failure_report, ensure_ascii=False, indent=2) + '\\n', encoding='utf-8')
    comparison = None
    if baseline is not None:
        comparison = compare_scorecards(baseline, scorecard)
        (out_dir / 'comparison.json').write_text(json.dumps(comparison, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'scorecard': scorecard, 'diagnostics': diagnostics, 'comparison': comparison, 'failure_report': failure_report, 'output_dir': str(out_dir)}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, default=ROOT / 'benchmark/manifest.json')
    parser.add_argument('--pages-dir', type=Path)
    parser.add_argument('--reviews', type=Path)
    parser.add_argument('--baseline-scorecard', type=Path)
    parser.add_argument('--logs', type=Path, help='Optional exported Railway API text log for failure analytics')
    parser.add_argument('--out-dir', type=Path, default=ROOT / 'benchmark/results/quality-run')
    args = parser.parse_args()
    output = run_pipeline(_load(args.manifest), _load(args.results), args.out_dir, args.pages_dir, _load(args.reviews) if args.reviews else None, _load(args.baseline_scorecard) if args.baseline_scorecard else None, args.logs)
    print(json.dumps({'completed_count': output['scorecard']['completed_count'], 'not_run_count': output['scorecard']['not_run_count'], 'diagnostic_issue_count': output['diagnostics']['issue_count'], 'failed_job_count': output['failure_report']['failed_job_count'] if output['failure_report'] else None, 'output_dir': output['output_dir']}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()