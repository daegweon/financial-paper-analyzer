"""Synthetic rejection controls. Source fixtures are not real-paper gold."""
from copy import deepcopy
import math
import pytest
from benchmark.draft_cell_audit import (
    digest, norm, observe, resolve, validate, caption_inventory, expand_document,
)

S='a'*64
R='b'*64


def fixture():
    # A transposed table: variable in column header, statistic in row header.
    matrix=[['','factor'],['Parameter','-0.120'],['Std. Dev.','0.010'],['t-stat','-12.000']]
    cells=[]; words=[]
    for row,values in enumerate(matrix):
        for col,text in enumerate(values):
            box=[col*40+1,row*20+1,col*40+39,row*20+19]
            cells.append({'row':row,'column':col,'text':text,'bbox':box})
            if text: words.append([box[0]+5,box[1]+5,box[2]-5,box[3]-5,text])
    def anchor(r,c):
        cell=cells[r*2+c]
        return {'bbox':cell['bbox'],'text_sha256':digest(cell['text'])}
    target={'id':'synthetic','source_sha256':S,'render_sha256':R,'page':1,
        'variable':'factor','model':'MG','statistic':'parameter','layout':'variables_in_columns',
        'coordinate_system':'pdf_points_top_left','review_origin':'assistant',
        'review_status':'visual_draft','source_render_checked':True,
        'anchors':{'row':anchor(1,0),'column':anchor(0,1),'value':anchor(1,1)},
        'companions':[{'kind':'reported_std_dev','row_offset':1,'label':anchor(2,0),'value':anchor(2,1)},
                      {'kind':'t_statistic','row_offset':2,'label':anchor(3,0),'value':anchor(3,1)}]}
    table={'page':1,'coordinate_system':'pdf_points_top_left','cells':cells}
    return target,[table],words


def run(t,tables,words,**kw):
    return observe(t,tables,kw.get('sha',S),words,kw.get('render',R),kw.get('page',1))


def test_correct_transposed_table_is_draft_only():
    t,tables,w=fixture();out=run(t,tables,w)
    assert out['candidate_agreement'] is True
    assert out['source_anchors_resolved']==7
    assert out['human_reviewed'] is False
    assert out['certified_accuracy'] is None
    assert out['promotion_eligible'] is False


@pytest.mark.parametrize('text',['0.120','-0.120*','-0.12','0.010','-0.121','-0.120 (0.010)'])
def test_numeric_mutations_rejected(text):
    t,tables,w=fixture();tables[0]['cells'][3]['text']=text
    assert run(t,tables,w)['status']=='mismatch'


@pytest.mark.parametrize('index,field,value',[(3,'row',7),(3,'column',7),(2,'row',0),(1,'column',0),(5,'column',0),(5,'row',3),(4,'column',1)])
def test_relationship_mutations_rejected(index,field,value):
    t,tables,w=fixture();tables[0]['cells'][index][field]=value
    assert run(t,tables,w)['status']=='mismatch'


def test_std_dev_cannot_be_relabelled_as_standard_error():
    t,_,_=fixture();t['companions'][0]['kind']='standard_error'
    with pytest.raises(ValueError,match='label/kind'):validate(t)


@pytest.mark.parametrize('key,value',[('review_origin','human'),('review_status','independently_reviewed'),('source_render_checked',False)])
def test_no_fabricated_review_promotion(key,value):
    t,tables,w=fixture();t[key]=value
    assert run(t,tables,w)['candidate_agreement'] is None


@pytest.mark.parametrize('kw',[{'sha':'c'*64},{'render':'c'*64},{'page':2}])
def test_source_binding(kw):
    t,tables,w=fixture()
    assert run(t,tables,w,**kw)['status']=='source_or_render_mismatch'


def test_source_checked_before_matching_candidate():
    t,tables,w=fixture();w[2][4]='wrong source'
    out=run(t,tables,w)
    assert out['status']=='source_anchor_mismatch'
    assert out['candidate_agreement'] is None


def test_all_page_conflicts_cannot_be_score_selected():
    t,tables,w=fixture();other=deepcopy(tables[0]);other['cells'][3]['text']='0.120';other['accuracy']=100
    assert run(t,tables+[other],w)['status']=='conflict'


def test_identical_overlapping_candidates_remain_agreement():
    t,tables,w=fixture()
    assert run(t,tables+deepcopy(tables),w)['status']=='agreement'


def test_ambiguous_overlapping_cells_rejected():
    t,tables,w=fixture();tables[0]['cells'].append(deepcopy(tables[0]['cells'][3]))
    assert run(t,tables,w)['candidate_agreement'] is False


def test_missing_and_wrong_page_tables():
    t,tables,w=fixture()
    assert run(t,[],w)['status']=='missing'
    tables[0]['page']=2
    assert run(t,tables,w)['status']=='missing'


@pytest.mark.parametrize('bad',[float('nan'),float('inf'),True,-1])
def test_invalid_geometry_fails_closed(bad):
    t,tables,w=fixture();tables[0]['cells'][3]['bbox'][0]=bad
    with pytest.raises(ValueError):run(t,tables,w)


def test_subscripts_use_visual_left_to_right():
    a={'bbox':[1,1,35,20],'text_sha256':digest('Rm-rf')}
    w=[[3,3,12,13,'Rm'],[13,2,23,12,'−r'],[24,7,28,14,'f']]
    assert resolve(a,w) is not None


def test_two_lines_cannot_be_stitched():
    a={'bbox':[1,1,35,40],'text_sha256':digest('AB')}
    assert resolve(a,[[3,3,12,13,'A'],[13,22,23,32,'B']]) is None


def test_normalization_retains_statistical_information():
    assert norm(' −0.120 *** ')==norm('-0.120***')
    assert digest('0.120')!=digest('0.12')!=digest('0.120*')


def test_caption_inventory_not_recall():
    pages=[{'page':1,'lines':['Table 1 shows something.']},
           {'page':2,'lines':['Table 1. Results.','Table A1. Cont.']},
           {'page':3,'lines':['Table 2: More results.']}]
    out=caption_inventory(pages,[2])
    assert out['caption_instances']==3
    assert out['unselected_caption_pages']==[3]
    assert out['table_recall'] is None
    assert out['captionless_or_image_tables_audited'] is False


def test_invalid_inventory_rejected():
    with pytest.raises(ValueError):caption_inventory([{'page':1,'lines':[]}],[2])


def test_digest_and_anchor_refs_expand_without_human_gate():
    t,_,_=fixture()
    doc={k:v for k,v in t.items() if k not in ('id','variable','anchors','companions')}
    doc['anchors']=t['anchors'];doc['targets']=[{'id':'s','variable':'factor','anchors':{k:k for k in t['anchors']},'companions':[]}]
    assert expand_document(doc)[0]['review_origin']=='assistant'


def test_same_number_wrong_column_is_not_accepted():
    t,tables,w=fixture();t['companions']=[]
    # A correct numeric string elsewhere does not repair this wrong variable cell.
    tables[0]['cells'][3]['text']='0.010'
    tables[0]['cells'].append({'row':1,'column':2,'text':'-0.120','bbox':[81,21,119,39]})
    assert run(t,tables,w)['status']=='mismatch'
