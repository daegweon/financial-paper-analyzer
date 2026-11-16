"""One-shot source-first visual draft checks, read-only on existing user data."""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path
from benchmark.draft_cell_audit import caption_inventory, expand_document, observe
from benchmark.table_shadow import StorageSource, package_versions

ROOT=Path(__file__).resolve().parent
PACKET_RUN='cell-review-ef695c09efdd4e42ae6c4dbc619c7b3c'
INVENTORY_IDS={'B01','B02','B09','B10'}


def packet_for(source,spec,owner):
    body,_=source.request(f'/storage/v1/object/{source.artifact_bucket}/{owner}/benchmarks/{PACKET_RUN}/{spec["id"]}.json')
    packet=json.loads(body)
    if packet.get('id')!=spec['id'] or packet.get('identity',{}).get('sha256')!=spec['sha256']:
        raise ValueError('Prior packet/source mismatch')
    return packet


def render_digest(page,spec):
    import fitz
    from PIL import Image
    pix=page.get_pixmap(matrix=fitz.Matrix(spec['render_scale'],spec['render_scale']),
                       clip=fitz.Rect(spec['render_crop']),colorspace=fitz.csGRAY,alpha=False)
    image=Image.frombytes('L',(pix.width,pix.height),pix.samples)
    image=image.point(lambda n:255 if n>=spec['render_threshold'] else 0,mode='1')
    output=io.BytesIO();image.save(output,format='PNG',optimize=True)
    return hashlib.sha256(output.getvalue()).hexdigest()


def inspect(source,spec,draft):
    import fitz
    pdf,identity,owner=source.get_pdf(spec)
    if identity['sha256']!=spec['sha256']:
        raise ValueError('Unlocked source')
    packet=packet_for(source,spec,owner)
    comparisons=[]
    with fitz.open(stream=pdf,filetype='pdf') as doc:
        if len(doc)!=spec['pages']:
            raise ValueError('Page-count mismatch')
        pages=[]
        for n,page in enumerate(doc,1):
            lines=[''.join(s['text'] for s in line['spans'])
                   for block in page.get_text('dict')['blocks'] if block.get('type')==0
                   for line in block.get('lines',[])]
            pages.append({'page':n,'lines':lines})
        inventory=caption_inventory(pages,packet['selection']['selected'])
        if draft:
            if draft['source_sha256']!=identity['sha256']:
                raise ValueError('Draft/source mismatch')
            page=doc[draft['page']-1]
            actual_render=render_digest(page,draft)
            if actual_render!=draft['render_sha256']:
                raise ValueError('Inspected render cannot be reproduced')
            words=[list(w[:5]) for w in page.get_text('words')]
            targets=expand_document(draft)
            runs=packet['candidate_runs']
            if {(r['variant'],r['repeat']) for r in runs}!={('all',1),('all',2),('selected',1),('selected',2)} or len(runs)!=4:
                raise ValueError('Expected four frozen comparison runs')
            for run in runs:
                if run.get('status')!='ok':raise ValueError('Failed prior candidate run')
                outcomes=[observe(t,run['tables'],identity['sha256'],words,actual_render,draft['page']) for t in targets]
                comparisons.append({'variant':run['variant'],'repeat':run['repeat'],'targets':len(outcomes),
                    'agreement':sum(o['candidate_agreement'] is True for o in outcomes),
                    'unassessed':sum(o['candidate_agreement'] is None for o in outcomes),'outcomes':outcomes})
    result={'id':spec['id'],'source_sha256':identity['sha256'],'inventory':inventory,
            'visual_draft_targets':len(draft['targets']) if draft else 0,
            'visual_pages':[draft['page']] if draft else [],'comparisons':comparisons,
            'independently_human_reviewed_targets':0,'certified_accuracy':None,
            'promotion_eligible':False,'existing_analysis_changes':0}
    # NEW append-only administrative JSON; never modify existing papers/analyses/jobs.
    if not source.save_artifact(owner,spec['id'],result):
        raise RuntimeError('Private audit artifact not saved')
    return result


def main():
    source=StorageSource()
    if source.bucket!='papers' or not source.upload:
        raise ValueError('Explicit private source/artifact mode required')
    source.run_id=source.run_id.replace('tables-','visual-draft-audit-')
    drafts=json.loads((ROOT/'visual_drafts_20261116.json').read_text())
    if drafts.get('review_origin')!='assistant' or drafts.get('independent_human_reviewers')!=0:
        raise ValueError('Draft provenance mismatch')
    by_id={d['id']:d for d in drafts['documents']}
    specs=json.loads((ROOT/'table_corpus.sha256.json').read_text())['papers']
    results=[];errors=[]
    print(json.dumps({'event':'visual_draft_audit_start','run_id':source.run_id,'versions':package_versions()}),flush=True)
    for spec in specs:
        if spec['id'] not in INVENTORY_IDS:continue
        try:
            result=inspect(source,spec,by_id.get(spec['id']))
            results.append(result)
            print(json.dumps({'event':'visual_draft_audit_result',**result},allow_nan=False),flush=True)
        except Exception as exc:
            errors.append({'id':spec['id'],'error_type':type(exc).__name__})
    print(json.dumps({'event':'visual_draft_audit_complete','run_id':source.run_id,'completed':len(results),'expected':4,
        'errors':errors,'visual_draft_targets':sum(r['visual_draft_targets'] for r in results),
        'candidate_comparisons':sum(c['targets'] for r in results for c in r['comparisons']),
        'agreements':sum(c['agreement'] for r in results for c in r['comparisons']),
        'unassessed':sum(c['unassessed'] for r in results for c in r['comparisons']),
        'independently_human_reviewed_targets':0,'certified_accuracy':None,'promotion_eligible':False,
        'provider_calls':0,'database_writes':0,'new_artifacts':len(results)},allow_nan=False),flush=True)
    return int(bool(errors) or len(results)!=4)

if __name__=='__main__':raise SystemExit(main())
