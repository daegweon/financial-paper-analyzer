import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from benchmark.run_quality_pipeline import run_pipeline

def test_pipeline_creates_all_review_artifacts_and_preserves_unmeasured(tmp_path):
    manifest = {'benchmark_version': 'test', 'papers': [{'id': 'B01', 'title': 'Paper', 'gold_facts': []}, {'id': 'B02', 'title': 'Not run', 'gold_facts': []}]}
    results = {'results': [{'paper_id': 'B01', 'analysis': {'findings': [{'claim': 'A claim', 'evidence': [{'page': 1, 'quote': 'A claim.'}]}]}}]}
    out = run_pipeline(manifest, results, tmp_path)
    assert out['scorecard']['completed_count'] == 1
    assert out['scorecard']['not_run_count'] == 1
    assert out['scorecard']['mean_human_score'] is None
    assert out['diagnostics']['paper_count'] == 1
    for name in ('scorecard.json', 'diagnostics.json', 'quality-dashboard.html', 'human-review-packet.md'):
        assert (tmp_path / name).is_file()
    packet = (tmp_path / 'human-review-packet.md').read_text(encoding='utf-8')
    assert '승인된 finding 수: 0' in packet

def test_pipeline_optional_baseline_comparison(tmp_path):
    manifest = {'benchmark_version': 'v2', 'papers': [{'id': 'B01', 'title': 'Paper', 'gold_facts': []}]}
    results = {'results': [{'paper_id': 'B01', 'analysis': {'summary': 'hello'}}]}
    baseline = {'benchmark_version': 'v1', 'results': [{'paper_id': 'B01', 'gold_fact_coverage_screen': 0.4}]}
    out = run_pipeline(manifest, results, tmp_path, baseline=baseline)
    assert out['comparison'] is not None
    assert (tmp_path / 'comparison.json').is_file()