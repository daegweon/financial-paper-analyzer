"""Read-only exact-source visual export. No plaintext PDF/image in logs.
X25519/HKDF/AES-GCM recipient key stays in inspecting session. No public endpoint,
Storage write, queue operation, provider call or production import.
"""
from __future__ import annotations
import base64, hashlib, io, json, os, re, zlib
from pathlib import Path
CONTEXT=b'PaperSignal-exact-source-visual-audit-v1'
PRIOR_RUN='cell-review-ef695c09efdd4e42ae6c4dbc619c7b3c'
RECIPIENT='38eabc2d53df4324a6541fb27ac80156478d0141afe343024d01ab41b9ca7017'
PAGES={'B01':(17,'0.9548'),'B02':(10,'49.942'),'B09':(9,'0.929'),'B10':(15,'0.20')}

def seal(payload:bytes,recipient_hex:str)->str:
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey,X25519PublicKey
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
    recipient=X25519PublicKey.from_public_bytes(bytes.fromhex(recipient_hex))
    ephemeral=X25519PrivateKey.generate()
    public=ephemeral.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)
    nonce=os.urandom(12)
    key=HKDF(algorithm=hashes.SHA256(),length=32,salt=None,info=CONTEXT).derive(ephemeral.exchange(recipient))
    cipher=AESGCM(key).encrypt(nonce,zlib.compress(payload,9),CONTEXT)
    return base64.b64encode(public+nonce+cipher).decode('ascii')

def emit(label:str,data:dict)->None:
    raw=json.dumps(data,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
    encoded=seal(raw,RECIPIENT)
    chunks=[encoded[i:i+3500] for i in range(0,len(encoded),3500)]
    for i,chunk in enumerate(chunks):
        print(json.dumps({'event':'sealed_visual_chunk','label':label,'index':i,'total':len(chunks),'data':chunk}),flush=True)
    print(json.dumps({'event':'sealed_visual_manifest','label':label,'chunks':len(chunks),'ciphertext_sha256':hashlib.sha256(encoded.encode()).hexdigest(),'plaintext_sha256':hashlib.sha256(raw).hexdigest()}),flush=True)

def source_lines(page)->list:
    return [{'text':''.join(s['text'] for s in ln['spans']),'bbox':list(ln['bbox'])} for b in page.get_text('dict')['blocks'] if b.get('type')==0 for ln in b.get('lines',[])]

def prepare(source,spec:dict)->None:
    import fitz
    from PIL import Image
    pdf,identity,owner=source.get_pdf(spec)
    body,_=source.request(f'/storage/v1/object/{source.artifact_bucket}/{owner}/benchmarks/{PRIOR_RUN}/{spec["id"]}.json')
    packet=json.loads(body)
    if packet.get('id')!=spec['id'] or packet.get('identity',{}).get('sha256')!=spec['sha256']:raise ValueError('Packet identity mismatch')
    page_number,hint=PAGES[spec['id']]
    with fitz.open(stream=pdf,filetype='pdf') as doc:
        if len(doc)!=spec['pages']:raise ValueError('Page count mismatch')
        diagnostics=[]
        for i,p in enumerate(doc,1):
            lines=source_lines(p)
            captions=[{'text':x['text'][:160],'bbox':x['bbox']} for x in lines if re.match(r'^\s*Table\s+(?:\d+|[A-Z]\d+|[IVX]+)\b',x['text'])]
            if captions or i not in packet['selection']['selected']:
                diagnostics.append({'page':i,'selected':i in packet['selection']['selected'],'captions':captions,'numeric_tokens':sum(bool(re.fullmatch(r'[−-]?\d+\.\d+[*]*',w[4])) for w in p.get_text('words'))})
        page=doc[page_number-1];lines=source_lines(page);hits=page.search_for(hint)
        captions=[x for x in lines if re.match(r'^\s*Table\s+\d+[.:]',x['text'])]
        y0,y1=35.,page.rect.height-30
        if hits:
            before=[x for x in captions if x['bbox'][1]<hits[0].y0]
            after=[x for x in captions if x['bbox'][1]>hits[0].y1]
            if before:y0=max(x['bbox'][1] for x in before)-3
            if after:y1=min(x['bbox'][1] for x in after)-4
        crop=fitz.Rect(20,y0,page.rect.width-20,y1)
        pix=page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),clip=crop,colorspace=fitz.csGRAY,alpha=False)
        image=Image.frombytes('L',(pix.width,pix.height),pix.samples).point(lambda p:255 if p>=190 else 0,mode='1')
        stream=io.BytesIO();image.save(stream,format='PNG',optimize=True);png=stream.getvalue()
        words=[list(w[:5]) for w in page.get_text('words') if fitz.Rect(w[:4]).intersects(crop)]
        previous=next((r for r in packet['source_pages'] if r['page']==page_number),None)
        if previous is not None:
            original=base64.b64decode(previous['png_base64'],validate=True)
            if hashlib.sha256(original).hexdigest()!=previous['png_sha256']:raise ValueError('Stored render hash mismatch')
        emit(spec['id']+'-source',{'id':spec['id'],'source_sha256':identity['sha256'],'page':page_number,'crop':list(crop),'dpi':108,'display_transform':'grayscale threshold190; no OCR; source raster','png_base64':base64.b64encode(png).decode(),'png_sha256':hashlib.sha256(png).hexdigest(),'words':words,'prior_render_hash_checked':previous is not None,'annotations':[]})
        print(json.dumps({'event':'source_inventory_diagnostic','id':spec['id'],'source_sha256':identity['sha256'],'diagnostics':diagnostics,'source_hint_found_on_display_page':bool(hits),'display_png_bytes':len(png),'human_reviewed_cells':0,'promotion_eligible':False}),flush=True)
        run=next(r for r in packet['candidate_runs'] if r['variant']=='all' and r['repeat']==1)
        emit(spec['id']+'-candidates',{'id':spec['id'],'page':page_number,'source_sha256':identity['sha256'],'tables':[t for t in run['tables'] if t['page']==page_number]})

def main()->int:
    from benchmark.table_shadow import StorageSource
    source=StorageSource()
    if source.bucket!='papers':raise ValueError('Unexpected source bucket')
    specs=json.loads(Path('/benchmark/table_corpus.sha256.json').read_text())['papers'];errors=[]
    for spec in specs:
        if spec['id'] not in PAGES:continue
        try:prepare(source,spec)
        except Exception as exc:errors.append({'id':spec['id'],'error_type':type(exc).__name__})
    print(json.dumps({'event':'source_visual_export_complete','errors':errors,'database_writes':0,'storage_writes':0,'provider_calls':0,'promotion_eligible':False}),flush=True)
    return bool(errors)
if __name__=='__main__':raise SystemExit(main())
