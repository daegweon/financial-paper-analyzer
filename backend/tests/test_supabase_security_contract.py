"""Static security-contract tests for the Supabase schema migrations.

These tests do not mutate the hosted database. They protect the ownership/RLS
invariants that must also be exercised by the separately approved live E2E.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "supabase" / "migrations"


def compact_sql() -> str:
    files = sorted(MIGRATIONS.glob("*.sql"))
    assert files, "Supabase migrations must be present in the repository"
    return re.sub(r"\s+", "", "\\n".join(path.read_text() for path in files).lower())


def test_every_user_data_table_enables_row_level_security():
    sql = compact_sql()
    for table in ("papers", "analyses", "analysis_jobs"):
        assert f"altertablepublic.{table}enablerowlevelsecurity;" in sql


def test_papers_are_restricted_to_the_authenticated_owner():
    sql = compact_sql()
    assert "createpolicypapers_select_ownonpublic.papersforselecttoauthenticatedusing((selectauth.uid())=user_id);" in sql
    assert "createpolicypapers_insert_ownonpublic.papersforinserttoauthenticatedwithcheck((selectauth.uid())=user_idandstorage_pathlike(user_id::text||'/%'));" in sql
    assert "createpolicypapers_update_ownonpublic.papersforupdatetoauthenticatedusing((selectauth.uid())=user_id)withcheck((selectauth.uid())=user_idandstorage_pathlike(user_id::text||'/%'));" in sql


def test_analyses_and_jobs_cannot_be_reassigned_to_another_user():
    sql = compact_sql()
    assert "createpolicyanalyses_select_ownonpublic.analysesforselecttoauthenticatedusing((selectauth.uid())=user_id);" in sql
    assert "createpolicyanalyses_insert_ownonpublic.analysesforinserttoauthenticatedwithcheck((selectauth.uid())=user_id);" in sql
    assert "createpolicyanalysis_jobs_select_ownonpublic.analysis_jobsforselecttoauthenticatedusing((selectauth.uid())=user_id);" in sql
    assert "createpolicyanalysis_jobs_update_ownonpublic.analysis_jobsforupdatetoauthenticatedusing((selectauth.uid())=user_id)withcheck((selectauth.uid())=user_id);" in sql
    assert "createpolicyanalysis_jobs_insert_ownonpublic.analysis_jobsforinserttoauthenticatedwithcheck((selectauth.uid())=user_idandexists(select1frompublic.paperspwherep.id=paper_idandp.user_id=(selectauth.uid())));" in sql


def test_private_pdf_storage_is_owner_scoped_and_not_public():
    sql = compact_sql()
    assert "values('papers','papers',false,31457280,array['application/pdf'])" in sql
    assert "createpolicypapers_storage_owner_insertonstorage.objectsforinserttoauthenticatedwithcheck(bucket_id='papers'and(storage.foldername(name))[1]=(selectauth.uid())::text);" in sql
    assert "createpolicypapers_storage_owner_selectonstorage.objectsforselecttoauthenticatedusing(bucket_id='papers'and(storage.foldername(name))[1]=(selectauth.uid())::text);" in sql
    assert "createpolicypapers_storage_owner_deleteonstorage.objectsfordeletetoauthenticatedusing(bucket_id='papers'and(storage.foldername(name))[1]=(selectauth.uid())::text);" in sql


def test_public_roles_do_not_receive_user_table_access():
    sql = compact_sql()
    assert "revokeallonpublic.papers,public.analysesfromanon,authenticated;" in sql
    assert "grantselect,insertonpublic.paperstoauthenticated;" in sql
    assert "grantselect,insertonpublic.analysestoauthenticated;" in sql
    assert "grantselect,insertonpublic.analysis_jobstoauthenticated;" in sql
    assert "grantselect,insertonpublic.paperstoanon;" not in sql
    assert "grantselect,insertonpublic.analysestoanon;" not in sql
