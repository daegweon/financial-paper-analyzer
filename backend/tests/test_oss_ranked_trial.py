from benchmark import oss_ranked_trial as rank
import fitz

def sample_pdf():
    doc=fitz.open()
    p=doc.new_page()
    p.insert_text((50,75),"Original Table 2 alpha -0.42")
    data=doc.tobytes()
    doc.close()
    return data

def test_pypdfium2_page_text_without_fitz_fallback():
    count,pages=rank.read_pages(sample_pdf(),"pypdfium2")
    assert count==1 and "alpha -0.42" in pages[0]["text"]

def test_pdfplumber_page_text_without_fitz_fallback():
    count,pages=rank.read_pages(sample_pdf(),"pdfplumber")
    assert count==1 and "alpha -0.42" in pages[0]["text"]

def test_unsupported_engine_must_not_fall_back_to_baseline():
    import pytest
    with pytest.raises(ValueError):
        rank.read_pages(sample_pdf(),"grobid")

def test_control_char_filter_and_page_limit():
    assert rank.normalize_page("alpha  " + chr(0) + " beta")=="alpha beta"

def test_later_candidates_never_claim_accuracy():
    later=rank.blocked_later_candidates()
    assert [i["backend"] for i in later]==["grobid","mineru","marker"]
    assert all(i["status"]=="not_executed" and i["source_quote_accuracy"] is None for i in later)
