from copy import deepcopy
import base64
import hashlib
import pytest

from benchmark.cell_review import (evaluate, normalized, render_html, review_ready,
                                   score_target, select_caption_pages, validate_target, valid_box)

SHA = 'a'*64


def target():
    return {'id':'unit-target', 'source_sha256':SHA, 'page':2,
            'variable':'Liquidity', 'model':'Model 1', 'statistic':'coefficient',
            'coordinate_system':'pdf_points_top_left',
            'review_status':'independently_reviewed', 'review_origin':'human',
            'source_render_checked':True, 'reviewers':['test-reviewer-a','test-reviewer-b'],
            'anchors':{'row':{'bbox':[1,11,9,19], 'text':'Liquidity'},
                       'column':{'bbox':[11,1,19,9], 'text':'Model 1'},
                       'value':{'bbox':[11,11,19,19], 'text':'−0.154***'}},
            'companions':[{'bbox':[11,21,19,29], 'text':'(0.020)',
                           'kind':'standard_error', 'row_offset':1}]}


def tables():
    return [{'page':2, 'coordinate_system':'pdf_points_top_left', 'cells':[
        {'row':0,'column':1,'bbox':[10,0,20,10],'text':'Model 1'},
        {'row':1,'column':0,'bbox':[0,10,10,20],'text':'Liquidity'},
        {'row':1,'column':1,'bbox':[10,10,20,20],'text':'-0.154***'},
        {'row':2,'column':1,'bbox':[10,20,20,30],'text':'(0.020)'}]}]


def test_exact_tuple_and_companion():
    assert score_target(target(),tables(),SHA)['status']=='exact'
    assert evaluate([target()],tables(),SHA)['exact_cell_accuracy']==1.0
    assert evaluate([target()],tables(),SHA)['promotion_eligible'] is False


@pytest.mark.parametrize('value',['0.154***','-0.154**','-0.154','-0.15***','0.154','-0.154*** 0.2'])
def test_wrong_sign_stars_precision_or_merged_values_fail(value):
    data=tables(); data[0]['cells'][2]['text']=value
    assert score_target(target(),data,SHA)['exact'] is False


@pytest.mark.parametrize('position,text',[(0,'Model 2'),(1,'Size'),(3,'(0.021)')])
def test_wrong_header_row_or_standard_error_fails(position,text):
    data=tables(); data[0]['cells'][position]['text']=text
    assert score_target(target(),data,SHA)['exact'] is False


@pytest.mark.parametrize('index,field,value',[(0,'column',2),(1,'row',2),(3,'column',2),(3,'row',3)])
def test_correct_numbers_but_wrong_axis_fails(index,field,value):
    data=tables(); data[0]['cells'][index][field]=value
    assert score_target(target(),data,SHA)['exact'] is False


def test_duplicate_identical_tables_not_false_conflict():
    assert score_target(target(),tables()+tables(),SHA)['status']=='exact'


def test_conflicting_candidates_never_select_by_accuracy():
    data=tables()+tables(); data[1]['accuracy']=100; data[1]['cells'][2]['text']='0.154***'
    assert score_target(target(),data,SHA)['status']=='conflict'


def test_correct_number_on_wrong_page_is_missing():
    data=tables(); data[0]['page']=3
    assert score_target(target(),data,SHA)['status']=='missing'


def test_source_mismatch_not_scored():
    out=evaluate([target()],tables(),'b'*64)
    assert out['outcomes'][0]['status']=='source_mismatch'
    assert out['exact_cell_accuracy'] is None


@pytest.mark.parametrize('update',[{'review_status':'draft'}, {'review_origin':'model'},
    {'source_render_checked':False}, {'reviewers':['one']}, {'reviewers':['same','same']},
    {'reviewers':['same',' same ']}, {'reviewers':['','second']}])
def test_unreviewed_gold_cannot_score(update):
    t=target(); t.update(update)
    assert not review_ready(t)
    assert evaluate([t],tables(),SHA)['exact_cell_accuracy'] is None


def test_empty_gold_abstains_and_never_reports_zero_error():
    out=evaluate([],tables(),SHA)
    assert out['exact_cell_accuracy'] is None and not out['fully_reviewed']


def test_partial_gold_is_not_full_accuracy():
    t=target(); t['id']='pending'; t['review_status']='draft'
    out=evaluate([target(),t],tables(),SHA)
    assert out['assessed']==1 and out['exact_cell_accuracy'] is None


def test_duplicate_target_ids_rejected():
    with pytest.raises(ValueError): evaluate([target(),target()],tables(),SHA)


def test_value_only_annotation_cannot_pass_as_row_and_column():
    t=target(); t['anchors']['row']=deepcopy(t['anchors']['value'])
    t['anchors']['column']=deepcopy(t['anchors']['value'])
    assert score_target(t,tables(),SHA)['exact'] is False


@pytest.mark.parametrize('box',[[0,0,0,1],[0,0,1,float('nan')],[True,0,1,1],[1,1,0,0],[]])
def test_invalid_geometry(box):
    assert not valid_box(box)
    t=target(); t['anchors']['value']['bbox']=box
    with pytest.raises(ValueError): validate_target(t)


def test_ambiguous_overlapping_cells_fail():
    data=tables(); data[0]['cells'].append(deepcopy(data[0]['cells'][2]))
    assert score_target(target(),data,SHA)['exact'] is False


def test_caption_selector_rejects_prose_and_preserves_cap_status():
    pages=[{'page':1,'text':'Table 2 shows results.\nSee Table 3.'},
           {'page':2,'text':'Table 2. Regression results'},
           {'page':3,'text':'Table 3: Continued.'}]
    r=select_caption_pages(pages,cap=1)
    assert r['selected']==[2] and r['omitted_by_cap']==[3] and not r['complete']
    assert not r['table_recall_known']


def test_no_captions_means_no_pages_not_all_pages():
    assert select_caption_pages([{'page':1,'text':'Abstract\nFigure 1. Returns'}])['selected']==[]


@pytest.mark.parametrize('cap',[0,17,True,-1])
def test_bad_cap_rejected(cap):
    with pytest.raises(ValueError): select_caption_pages([],cap=cap)


def test_duplicate_page_rejected():
    with pytest.raises(ValueError): select_caption_pages([{'page':1,'text':''}]*2)


def test_only_typographic_normalization():
    assert normalized('−0.154 ***')==normalized('-0.154***')
    assert normalized('(0.020)')!=normalized('0.020')
    assert normalized('0.00')!=normalized('p<0.01')


def test_render_rejects_tampered_image():
    packet={'identity':{'sha256':SHA}, 'source_pages':[{'png_base64':base64.b64encode(b'bad').decode(),
            'png_sha256':hashlib.sha256(b'bad').hexdigest(),'source_sha256':SHA}]}
    with pytest.raises(ValueError): render_html(packet)


def test_candidates_are_html_escaped_and_hidden():
    packet={'identity':{'sha256':SHA},'source_pages':[], 'candidate_runs':['<script>alert(1)</script>']}
    out=render_html(packet)
    assert '<script>' not in out and '&lt;script&gt;' in out and '<details>' in out


def test_negative_pages_require_independent_source_review():
    negative={k:v for k,v in target().items() if k in ('id','source_sha256','page','review_status','review_origin','reviewers','source_render_checked')}
    negative['kind']='no_table_page'
    out=evaluate([target()],tables(),SHA,negative_pages=[negative])
    assert out['negative_page_hit_rate']==1.0
    assert out['promotion_eligible'] is False
    negative['review_status']='machine_draft'
    assert evaluate([target()],tables(),SHA,negative_pages=[negative])['negative_page_hit_rate'] is None


def test_negative_empty_pages_report_only_audited_page_diagnostic():
    negative={k:v for k,v in target().items() if k in ('id','source_sha256','page','review_status','review_origin','reviewers','source_render_checked')}
    negative.update(kind='no_table_page',page=5)
    assert evaluate([],tables(),SHA,negative_pages=[negative])['negative_page_hit_rate']==0.0
    assert evaluate([],tables(),SHA)['negative_page_hit_rate'] is None


def test_unknown_candidate_coordinates_fail_closed():
    data=tables(); data[0]['coordinate_system']='bottom_left'
    with pytest.raises(ValueError): score_target(target(),data,SHA)
