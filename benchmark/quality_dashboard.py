#!/usr/bin/env python3
"""Render a transparent, offline HTML quality dashboard from benchmark scorecard JSON."""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


def _pct(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return "미측정"
    return f"{value * 100:.1f}%"


def _bar(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return '<span class="na">미측정</span>'
    width = max(0.0, min(100.0, float(value) * 100))
    return f'<div class="bar"><span style="width:{width:.1f}%"></span></div><small>{_pct(value)}</small>'


def render_dashboard(scorecard: dict[str, Any]) -> str:
    rows = scorecard.get("results", [])
    if not isinstance(rows, list):
        rows = []
    completed = [r for r in rows if isinstance(r, dict) and r.get("status") != "not_run"]
    not_run = [r for r in rows if isinstance(r, dict) and r.get("status") == "not_run"]
    avg = lambda key: (
        sum(r[key] for r in completed if isinstance(r.get(key), (int, float)))
        / len([r for r in completed if isinstance(r.get(key), (int, float))])
        if any(isinstance(r.get(key), (int, float)) for r in completed) else None
    )
    table_rows = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        paper_id = html.escape(str(row.get("paper_id", "—")))
        title = html.escape(str(row.get("title", "—")))
        if row.get("status") == "not_run":
            table_rows.append(
                f"<tr><th>{paper_id}</th><td>{title}</td><td colspan='4'><span class='na'>분석 결과 없음</span></td></tr>"
            )
            continue
        missing = row.get("gold_fact_missing", [])
        missing_text = html.escape(", ".join(map(str, missing)) if isinstance(missing, list) else "—")
        table_rows.append(
            f"<tr><th>{paper_id}</th><td>{title}</td>"
            f"<td>{_bar(row.get('gold_fact_coverage_screen'))}</td>"
            f"<td>{_bar(row.get('claim_evidence_coverage'))}</td>"
            f"<td>{_bar(row.get('citation_page_precision'))}</td>"
            f"<td>{_bar(row.get('human_score'))}</td></tr>"
            f"<tr class='detail'><td></td><td colspan='5'>미충족 Gold fact: {missing_text}</td></tr>"
        )
    body = "\n".join(table_rows) or "<tr><td colspan='6'>점수 데이터가 없습니다.</td></tr>"
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PaperSignal 품질 대시보드</title>
<style>
:root{{color-scheme:light dark;font-family:system-ui,-apple-system,sans-serif}}
body{{margin:0;padding:24px;background:Canvas;color:CanvasText}}main{{max-width:1200px;margin:auto}}
h1{{font-size:1.65rem}}.muted,.detail{{color:GrayText}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin:20px 0}}
.card{{border:1px solid GrayText;border-radius:12px;padding:16px}}.value{{font-size:1.6rem;font-weight:700}}
table{{width:100%;border-collapse:collapse;font-size:.9rem}}th,td{{padding:10px;border-bottom:1px solid GrayText;text-align:left;vertical-align:top}}
.bar{{height:8px;background:color-mix(in srgb,CanvasText 15%,Canvas);border-radius:8px;min-width:90px;overflow:hidden;margin:3px 0}}
.bar span{{display:block;height:100%;background:#169b70}}small{{color:GrayText}}.na{{color:GrayText}}
.notice{{border-left:4px solid #c18b2e;padding:12px;background:color-mix(in srgb,#c18b2e 10%,Canvas);margin:18px 0}}
@media(max-width:700px){{body{{padding:12px}}table{{font-size:.78rem}}th,td{{padding:6px}}}}
</style></head><body><main>
<h1>PaperSignal 논문 분석 품질 대시보드</h1>
<p class="muted">Benchmark v{html.escape(str(scorecard.get('benchmark_version','—')))} · 자동 생성 · 원문 감수 전</p>
<section class="cards">
<div class="card"><div class="muted">분석 완료</div><div class="value">{len(completed)} / {html.escape(str(scorecard.get('paper_count','—')))}</div></div>
<div class="card"><div class="muted">미분석</div><div class="value">{len(not_run)}</div></div>
<div class="card"><div class="muted">Gold fact 커버리지 평균</div><div class="value">{_pct(avg('gold_fact_coverage_screen'))}</div></div>
<div class="card"><div class="muted">근거 포함률 평균</div><div class="value">{_pct(avg('claim_evidence_coverage'))}</div></div>
<div class="card"><div class="muted">페이지 인용 정확도 평균</div><div class="value">{_pct(avg('citation_page_precision'))}</div></div>
<div class="card"><div class="muted">인간 감수 점수 평균</div><div class="value">{_pct(avg('human_score'))}</div></div>
</section>
<div class="notice"><strong>해석 주의:</strong> Gold fact alias 일치율은 의미 정확도가 아닙니다. 페이지 인용 정확도는 원문 PDF 텍스트를 제공한 경우에만 측정됩니다. 인간 감수 점수가 없으면 미측정으로 표시하며 자동 점수로 대체하지 않습니다. 이 대시보드는 어떠한 finding도 승인하지 않습니다.</div>
<table><thead><tr><th>논문</th><th>제목</th><th>Gold fact</th><th>주장 근거 포함률</th><th>페이지 인용 정확도</th><th>인간 감수</th></tr></thead>
<tbody>{body}</tbody></table>
<p class="muted">생성된 값은 입력 scorecard에 있는 값만 사용합니다. 미측정 값은 미측정으로 유지됩니다.</p>
</main></body></html>"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scorecard", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("benchmark/results/quality-dashboard.html"))
    args = parser.parse_args()
    data = json.loads(args.scorecard.read_text(encoding="utf-8"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_dashboard(data), encoding="utf-8")
    print(f"Wrote dashboard: {args.out}")


if __name__ == "__main__":
    main()
