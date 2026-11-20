#!/usr/bin/env python3
"""Build a human-review Markdown packet from exported PaperSignal analyses."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _safe(value: Any) -> str:
    if value is None or value == "":
        return "확인 불가"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).replace("\r", " ").replace("\n", " ").strip()


def _evidence(items: Any) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    output = []
    for item in items:
        if not isinstance(item, dict):
            continue
        quote = item.get("quote")
        page = item.get("page")
        if isinstance(quote, str) and quote.strip():
            output.append({"page": page, "quote": quote.strip()})
    return output


def _finding_status(item: dict[str, Any]) -> str:
    for key in ("verification_status", "evidence_status", "quality_status", "status"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "review_required"


def build_packet(manifest: dict[str, Any], results: Any) -> str:
    rows = results.get("results", results) if isinstance(results, dict) else results
    by_id: dict[str, dict[str, Any]] = {}
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            paper_id = row.get("paper_id") or row.get("benchmark_id")
            analysis = row.get("analysis") or row.get("result")
            if paper_id and isinstance(analysis, dict):
                by_id[str(paper_id)] = analysis

    lines = [
        "# PaperSignal — human evidence review packet",
        "",
        "> 자동 생성된 검토 보조 자료입니다. 어떤 주장도 자동으로 승인하지 않습니다. 반드시 동일 버전의 출판사 PDF 원문과 표·열·각주를 직접 확인하세요.",
        "",
        "## Review checklist",
        "",
        "- [ ] PDF 제목·저자·연도·DOI 일치",
        "- [ ] 연구표본·기간·빈도·관측단위 일치",
        "- [ ] 표 번호와 모델/열(column) 식별 일치",
        "- [ ] 변수명·계수·부호·단위가 원문 표와 일치",
        "- [ ] 표준오차/t-statistic 및 유의성 별표 확인",
        "- [ ] 별표의 의미를 설명하는 표 각주 확인",
        "- [ ] 인용 문구가 지정 페이지에 실제 존재",
        "- [ ] 인과관계 표현이 논문 식별전략을 과장하지 않음",
        "- [ ] 최종 판정과 검토자 메모 기록",
        "",
        "## Findings",
        "",
    ]
    total = 0
    for paper in manifest.get("papers", []):
        if not isinstance(paper, dict):
            continue
        paper_id = str(paper.get("id", "UNKNOWN"))
        analysis = by_id.get(paper_id)
        lines.extend([f"### {paper_id} — {_safe(paper.get('title'))}", ""])
        if not analysis:
            lines.extend(["분석 결과가 제공되지 않았습니다.", ""])
            continue
        findings = analysis.get("findings", [])
        if not isinstance(findings, list) or not findings:
            lines.extend(["검토할 finding이 없습니다.", ""])
            continue
        for index, finding in enumerate(findings, start=1):
            if not isinstance(finding, dict):
                continue
            total += 1
            evidence = _evidence(finding.get("evidence"))
            lines.extend([
                f"#### {paper_id}-F{index:02d}",
                "",
                f"- 자동 상태: {_safe(_finding_status(finding))}",
                f"- 주장: {_safe(finding.get('claim') or finding.get('text'))}",
                f"- 표 참조: {_safe(finding.get('table_reference') or finding.get('table'))}",
                f"- 모델/열: {_safe(finding.get('model_or_column') or finding.get('column'))}",
                f"- 추정치: {_safe(finding.get('estimate'))}",
                f"- 통계적 유의성: {_safe(finding.get('statistical_significance') or finding.get('significance'))}",
                f"- 방향: {_safe(finding.get('direction'))}",
                "- 직접 근거:",
            ])
            if evidence:
                for item in evidence:
                    lines.append(f"  - PDF p.{_safe(item['page'])}: “{item['quote']}”")
            else:
                lines.append("  - 직접 인용 근거 없음")
            lines.extend([
                "- 검토자 판정: [미검토 / 승인 / 수정 필요 / 기각]",
                "- 원문 PDF 페이지·표·열 확인:",
                "- 검토자 메모:",
                "",
            ])
    lines.extend([
        "## Review summary",
        "",
        f"- 포함된 finding 수: {total}",
        "- 승인된 finding 수: 0 (이 문서는 자동 승인하지 않음)",
        "- 최종 감수 전까지 review_required 상태를 유지하세요.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("benchmark/manifest.json"))
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("benchmark/results/human-review-packet.md"))
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    results = json.loads(args.results.read_text(encoding="utf-8"))
    packet = build_packet(manifest, results)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(packet, encoding="utf-8")
    print(f"Wrote review packet: {args.out}")


if __name__ == "__main__":
    main()
