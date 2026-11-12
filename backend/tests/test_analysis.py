import pytest
from app.main import extract_pages,extractive_result,validate_evidence

def test_invalid_pdf_rejected():
    with pytest.raises(ValueError): extract_pages(b"not pdf")
def test_extract_has_no_model_findings():
    result=extractive_result(2,[{"page":1,"text":"Asset pricing and volatility factors."}])
    assert result["mode"]=="extractive"
    assert result["evidence"][0]["page"]==1
def test_quote_requires_same_page_verbatim():
    pages=[{"page":2,"text":"Liquidity risk premium was observed in this study."}]
    assert validate_evidence([{"page":2,"quote":"Liquidity risk premium"},{"page":1,"quote":"Liquidity risk premium"}],pages)==[{"page":2,"quote":"Liquidity risk premium"}]
