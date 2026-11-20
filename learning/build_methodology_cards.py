#!/usr/bin/env python3
"""Build standalone Korean junior learning cards from the curated methodology catalog."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

def validate_catalog(data):
    methods = data.get('methods') if isinstance(data, dict) else None
    if not isinstance(methods, list) or not methods:
        raise ValueError('catalog methods must be a non-empty list')
    seen = set()
    required = ('id','title','level','category','concept','formula','read_table','caveats','quiz')
    for item in methods:
        if not isinstance(item, dict) or any(not item.get(key) for key in required):
            raise ValueError('each method must include all learning fields')
        if item['id'] in seen:
            raise ValueError(f'duplicate method id: {item["id"]}')
        seen.add(item['id'])
        if not isinstance(item['read_table'], list) or not isinstance(item['caveats'], list):
            raise ValueError(f'{item["id"]}: read_table and caveats must be lists')
        if not item['quiz'].get('question') or not item['quiz'].get('answer'):
            raise ValueError(f'{item["id"]}: quiz requires question and answer')
    return data

def render_cards(data):
    validate_catalog(data)
    lines = ['# 금융논문 읽기를 위한 계량경제학 방법론 카드', '', '> 일반 교육용 콘텐츠입니다. 특정 논문에서 실제로 사용된 방법론이나 추정 결과를 의미하지 않습니다.', '']
    for item in data['methods']:
        lines.extend([f'## {item["title"]}', '', f'- 난이도: {item["level"]}', f'- 분야: {item["category"]}', '', '### 핵심 개념', '', item['concept'], '', '### 대표 수식', '', f'`{item["formula"]}`', '', '### 논문 결과표 읽는 순서', ''])
        lines.extend([f'{i}. {v}' for i, v in enumerate(item['read_table'], 1)])
        lines.extend(['', '### 해석 시 주의점', ''])
        lines.extend([f'- {v}' for v in item['caveats']])
        lines.extend(['', '### 이해도 확인', '', f'**질문:** {item["quiz"]["question"]}', '', f'**해설:** {item["quiz"]["answer"]}', '', '---', ''])
    return '\n'.join(lines)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, default=Path(__file__).with_name('methodology_catalog.json'))
    parser.add_argument('--out', type=Path, default=Path('learning/methodology-cards.md'))
    args = parser.parse_args()
    data = validate_catalog(json.loads(args.catalog.read_text(encoding='utf-8')))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_cards(data), encoding='utf-8')
    print(f'Generated {len(data["methods"])} methodology cards: {args.out}')

if __name__ == '__main__':
    main()