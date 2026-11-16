import hashlib
import json
import os
from pathlib import Path
import sys
import types
import urllib.error
import uuid

import pytest
from benchmark.table_shadow import check_bytes, run_isolated, summarize, StorageSource, NoRedirect


def test_unlocked_local_bytes_not_claimed_as_original():
    b=b"%PDF-test"; r=check_bytes(b,{"bytes":len(b),"etag":"x"})
    assert r["source_identity"]=="unverified_local"
    assert r["sha256"]==hashlib.sha256(b).hexdigest()


def test_storage_etag_and_size_checked():
    b=b"%PDF-test";s={"bytes":len(b),"etag":"abc"}
    assert check_bytes(b,s,'"abc"')["source_identity"]=="storage_download"
    with pytest.raises(ValueError): check_bytes(b,s,'"wrong"')
    with pytest.raises(ValueError): check_bytes(b+b"x",s,'"abc"')


def test_sha_lock_enforced():
    b=b"%PDF-test";s={"bytes":len(b),"sha256":"0"*64}
    with pytest.raises(ValueError): check_bytes(b,s)
    s["sha256"]=hashlib.sha256(b).hexdigest()
    assert check_bytes(b,s)["source_identity"]=="sha256_locked_local"


def test_empty_or_successful_smoke_never_grants_promotion():
    for rows in ([],[{"engine":"camelot-stream","status":"ok","wall_seconds":1,"peak_rss_mib":90,"table_count":100}]):
        assert summarize(rows)["promotion_eligible"] is False
        assert "human_reviewed_exact_cell_gold_missing" in summarize(rows)["blocking_gates"]


def test_failures_not_averaged_as_zero_latency():
    r=summarize([{"engine":"camelot-stream","status":"timeout","wall_seconds":60},
                 {"engine":"camelot-stream","status":"ok","wall_seconds":10,"peak_rss_mib":99}])
    e=r["engines"]["camelot-stream"]
    assert e["failures"]==1 and e["p50_wall_seconds_successes_only"]==10


def test_timeout_returns_explicit_failure(monkeypatch,tmp_path):
    import subprocess
    def timeout(*a,**kw): raise subprocess.TimeoutExpired("child",1)
    monkeypatch.setattr(subprocess,"run",timeout)
    r=run_isolated(tmp_path/"x.pdf","camelot-stream",tmp_path/"r.json",1,1)
    assert r["status"]=="timeout"


def test_parser_children_receive_no_provider_or_storage_secrets(monkeypatch,tmp_path):
    import subprocess
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY","do-not-copy")
    monkeypatch.setenv("GEMINI_API_KEY","do-not-copy")
    def run(*a,**kw):
        assert "SUPABASE_SERVICE_ROLE_KEY" not in kw["env"]
        assert "GEMINI_API_KEY" not in kw["env"]
        return types.SimpleNamespace(returncode=1)
    monkeypatch.setattr(subprocess,"run",run)
    assert run_isolated(tmp_path/"x.pdf","pymupdf-text",tmp_path/"r.json",1,1)["status"]=="process_error"


def test_redirects_refused():
    with pytest.raises(ValueError): NoRedirect().redirect_request(None,None,302,"",{},"https://other.example")


def test_storage_ambiguous_filename_refused():
    s=StorageSource.__new__(StorageSource)
    s.request=lambda path:(b'[{},{}]',{})
    with pytest.raises(ValueError): s.get_pdf({"filename":"B01.pdf"})


def test_wrong_project_refused(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL","https://other.supabase.co")
    with pytest.raises(ValueError): StorageSource()


def test_public_artifact_bucket_refused():
    s=StorageSource.__new__(StorageSource);s.artifact_bucket="papersignal-benchmark-artifacts"
    s.request=lambda *a:(b'{"public":true}',{})
    with pytest.raises(ValueError): s.ensure_artifact_bucket()


def test_new_artifact_bucket_private_and_no_source_bucket_mutation():
    s=StorageSource.__new__(StorageSource);s.artifact_bucket="papersignal-benchmark-artifacts"; calls=[]
    def request(path,data=None):
        calls.append((path,data))
        if len(calls)==1: raise urllib.error.HTTPError("",404,"",{},None)
        return b'{"public":false}',{}
    s.request=request;s.ensure_artifact_bucket()
    body=json.loads(calls[1][1])
    assert body["public"] is False and body["allowed_mime_types"]==["application/json"]
    assert body["id"]=="papersignal-benchmark-artifacts"


def test_private_artifact_paths_cannot_overwrite_paper():
    s=StorageSource.__new__(StorageSource);s.upload=True;s.artifact_bucket="papersignal-benchmark-artifacts";s.run_id="tables-test";s.artifact_ready=True
    calls=[];s.request=lambda path,data:calls.append((path,data))
    owner=str(uuid.uuid4());assert s.save_artifact(owner,"B01",{"ok":True})
    assert calls[0][0].endswith(owner+"/benchmarks/tables-test/B01.json")
    with pytest.raises(ValueError): s.save_artifact(owner,"../paper.pdf",{})


def test_real_synthetic_pdf_end_to_end(tmp_path):
    import fitz
    pdf=tmp_path/"fixture.pdf"
    doc=fitz.open();page=doc.new_page();page.insert_text((72,72),"Synthetic control: coefficient -0.154***")
    doc.save(pdf);doc.close()
    result=run_isolated(pdf,"pymupdf-text",tmp_path/"result.json",1,20)
    assert result["status"]=="ok" and result["page_count"]==1
    assert "-0.154***" in result["pages"][0]["text"]
    assert result["peak_rss_mib"]>0 and result["wall_seconds"]>0

@pytest.mark.parametrize("engine", ["camelot-lattice", "camelot-stream"])
def test_real_camelot_regression_table(tmp_path, engine):
    import fitz
    pdf=tmp_path/"regression.pdf";doc=fitz.open();p=doc.new_page(width=612,height=792)
    xs=[72,225,370,525];ys=[90,120,150,180,210]
    for x in xs: p.draw_line((x,ys[0]),(x,ys[-1]),width=1)
    for y in ys: p.draw_line((xs[0],y),(xs[-1],y),width=1)
    rows=[["Variable","Model (1)","Model (2)"],["AR_Amihud","-0.154***","0.00168***"],
          ["Std. error","(0.031)","(0.0004)"],["Observations","120","120"]]
    for r,row in enumerate(rows):
        for c,text in enumerate(row): p.insert_text((xs[c]+6,ys[r]+20),text,fontsize=10)
    doc.save(pdf);doc.close()
    result=run_isolated(pdf,engine,tmp_path/(engine+".json"),1,30)
    assert result["status"]=="ok"
    extracted=[row for t in result["tables"] for row in t["rows"]]
    assert ["AR_Amihud","-0.154***","0.00168***"] in extracted
    assert ["Std. error","(0.031)","(0.0004)"] in extracted
