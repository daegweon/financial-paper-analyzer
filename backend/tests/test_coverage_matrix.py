import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from benchmark.coverage_matrix import build_coverage_matrix

def test_coverage_matrix_separates_missing_from_unmeasured_and_groups_methods():
    manifest = {'benchmark_version':'v1','papers':[
        {'id':'B01','title':'A','topic':['asset pricing'],'method_families':['OLS'],'gold_facts':[{'id':'sample','category':'data'},{'id':'method','category':'methodology'}]},
        {'id':'B02','title':'B','topic':['risk'],'method_families':['GARCH'],'gold_facts':[{'id':'finding','category':'findings'}]},
    ]}
    scorecard = {'results':[{'paper_id':'B01','gold_fact_matches':['sample'],'gold_fact_missing':['method'],'gold_fact_coverage_screen':0.5},{'paper_id':'B02','status':'not_run'}]}
    result = build_coverage_matrix(manifest, scorecard)
    assert result['analyzed_count'] == 1 and result['not_run_count'] == 1
    b01 = result['papers'][0]
    assert b01['gold_facts'][0]['screen_status'] == 'matched_screen'
    assert b01['gold_facts'][1]['screen_status'] == 'missing'
    assert result['papers'][1]['gold_facts'][0]['screen_status'] == 'unmeasured'
    assert result['method_families'][0]['name'] == 'GARCH'
    assert 'not semantic correctness' in result['warning']

def test_empty_scorecard_does_not_create_false_zero_match():
    result = build_coverage_matrix({'papers':[{'id':'B01','gold_facts':[{'id':'x'}]}]}, {'results':[]})
    assert result['papers'][0]['gold_facts'][0]['screen_status'] == 'unmeasured'
    assert result['not_run_count'] == 1