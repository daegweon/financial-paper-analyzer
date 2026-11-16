from benchmark.marker_cpu_phase import page_text

def test_flatten_html_nodes_without_leaking_structure():
    obj={"block_type":"Page","children":[{"block_type":"Text","html":"<p>Return <b>-0.42</b></p>"},{"block_type":"Table","html":"<table><tr><td>t-stat</td><td>2.8</td></tr></table>"}]}
    text=page_text(obj)
    assert "Return -0.42" in text and "t-stat" in text and "2.8" in text

def test_unlocated_or_missing_content_not_invented():
    assert page_text({"block_type":"Page","children":[]})==""
