import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from learning.build_methodology_cards import render_cards, validate_catalog

CATALOG = Path(__file__).resolve().parents[2] / 'learning' / 'methodology_catalog.json'

def test_methodology_catalog_is_complete_and_generates_learning_cards():
    data = validate_catalog(json.loads(CATALOG.read_text(encoding='utf-8')))
    assert len(data['methods']) >= 8
    cards = render_cards(data)
    assert '일반 교육용 콘텐츠' in cards
    assert '이해도 확인' in cards
    assert '주의점' in cards
    assert '이중차분법(DiD)' in cards
    assert '도구변수(IV·2SLS)' in cards

def test_catalog_rejects_duplicate_method_ids():
    data = {'methods': [
        {'id':'x','title':'x','level':'x','category':'x','concept':'x','formula':'x','read_table':['x'],'caveats':['x'],'quiz':{'question':'q','answer':'a'}},
        {'id':'x','title':'x','level':'x','category':'x','concept':'x','formula':'x','read_table':['x'],'caveats':['x'],'quiz':{'question':'q','answer':'a'}},
    ]}
    try:
        validate_catalog(data)
    except ValueError as exc:
        assert 'duplicate' in str(exc)
    else:
        raise AssertionError('duplicate ids must be rejected')