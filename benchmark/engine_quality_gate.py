"""Fail-closed evaluator of predeclared PaperSignal release evidence.

This only validates evidence structure and consistency, not authenticity.
Reviewer identity, source rows, API bills and live E2E need external verification.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
import re
from pathlib import Path

POLICY_PATH = Path(__file__).with_name('engine_release_gates_2026-11-17.json')
_SHA256 = re.compile(r'[a-f0-9]{64}\Z')
_GIT_SHA = re.compile(r'[a-f0-9]{40}\Z')
_HISTORICAL = {'B01': 4, 'B02': 6, 'B03': 1, 'B05': 2, 'B09': 3, 'B10': 2}


def sha(value, git=False):
    return isinstance(value, str) and bool((_GIT_SHA if git else _SHA256).fullmatch(value))


def number(value, positive=False):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and (value > 0 if positive else value >= 0)


def reviewers_valid(item):
    reviews = item.get('reviewers', [])
    return (
        isinstance(reviews, list) and len(reviews) >= 2
        and all(isinstance(r, dict) and isinstance(r.get('reviewer_id'), str)
                and bool(r['reviewer_id'].strip())
                and r.get('verdict') in {'supported', 'corrected', 'rejected'} for r in reviews)
        and len({r['reviewer_id'] for r in reviews}) == len(reviews)
        and sha(item.get('source_sha256'))
        and (len({r['verdict'] for r in reviews}) == 1
             or isinstance(item.get('disagreement_resolution_ref'), str)
             and bool(item['disagreement_resolution_ref'].strip()))
    )


def p95(values):
    return sorted(values)[math.ceil(0.95 * len(values)) - 1]


def evaluate(policy, evidence):
    """Compute gate status. Unknown, unavailable or incomplete values block release."""
    gates = {item['id']: [] for item in policy['quality_gates']}
    req = {item['id']: item['requirements'] for item in policy['quality_gates']}
    frozen = policy['frozen_production']
    candidate = evidence.get('candidate_commit')
    base = evidence.get('baseline') or {}
    corpus = evidence.get('corpus') or {}
    regression = corpus.get('regression') or []
    heldout = corpus.get('heldout') or []

    def check(gate, condition, reason):
        if not condition:
            gates[gate].append(reason)

    check('Q0', sha(candidate, git=True) and candidate != frozen['commit'], 'distinct candidate Git SHA required')
    check('Q0', base.get('commit') == frozen['commit']
          and base.get('analysis_version') == frozen['analysis_version'], 'frozen source/version mismatch')
    for field in ('model_config_sha256', 'prompt_sha256', 'schema_sha256', 'extraction_sha256'):
        check('Q0', sha(base.get(field)), f'missing locked {field}')
    valid_regression = (
        isinstance(regression, list) and len(regression) == req['Q0']['locked_original_papers']
        and all(isinstance(x, dict) and sha(x.get('sha256')) and type(x.get('pages')) is int
                and x['pages'] > 0 for x in regression)
        and {x['id'] for x in regression if isinstance(x, dict) and 'id' in x}
        == {f'B{i:02d}' for i in range(1, 11)}
        and sum(x['pages'] for x in regression if isinstance(x, dict) and type(x.get('pages')) is int) == 209
    )
    check('Q0', valid_regression, 'B01-B10 original PDF hashes and 209 page total required')
    valid_heldout = (
        isinstance(heldout, list) and len(heldout) >= req['Q0']['min_heldout_papers']
        and all(isinstance(x, dict) and isinstance(x.get('id'), str)
                and x['id'] not in {f'B{i:02d}' for i in range(1, 11)}
                and sha(x.get('sha256')) and type(x.get('pages')) is int and x['pages'] > 0
                and sha(x.get('lock_commit'), git=True)
                and x.get('locked_before_candidate') is True for x in heldout)
        and len({x['id'] for x in heldout if isinstance(x, dict) and 'id' in x}) == len(heldout)
        and len({x['sha256'] for x in heldout if isinstance(x, dict) and 'sha256' in x}) == len(heldout)
    )
    check('Q0', valid_heldout, '2+ held-out PDFs must be uniquely SHA-locked before tuning')

    # A reviewer cannot certify an arbitrary 64-hex string. Each review must
    # anchor to the *actual declared PDF* and a visible source page and quote.
    paper_meta = {
        item['id']: item for item in regression + heldout
        if isinstance(item, dict) and isinstance(item.get('id'), str)
    }

    def source_anchor_valid(item):
        paper = paper_meta.get(item.get('paper_id'))
        if not paper or item.get('source_sha256') != paper.get('sha256'):
            return False
        page = item.get('source_page')
        quote = item.get('source_quote')
        if type(page) is not int or page < 1:
            return False
        if type(paper.get('pages')) is int and page > paper['pages']:
            return False
        if not isinstance(quote, str) or len(quote.strip()) < 8:
            return False
        anchor_ref = item.get('source_evidence_ref')
        return isinstance(anchor_ref, str) and bool(anchor_ref.strip())

    audit = evidence.get('human_review') or {}
    legacy = audit.get('legacy') or []
    claims = audit.get('claims') or []
    legacy_valid = (
        isinstance(legacy, list) and len(legacy) == req['Q0']['review_required_to_adjudicate']
        and all(isinstance(x, dict) and reviewers_valid(x) and source_anchor_valid(x) and x.get('resolved') is True
                and x.get('critical_unresolved') is False
                and (x.get('source_confirmed_recovery') is not True or
                     all(r['verdict'] in {'supported', 'corrected'} for r in x['reviewers']))
                for x in legacy)
        and Counter(x.get('paper_id') for x in legacy if isinstance(x, dict)) == _HISTORICAL
        and len({x.get('id') for x in legacy if isinstance(x, dict)}) == len(legacy)
    )
    check('Q0', legacy_valid, '18 historical cases require 2 independent, recorded reviewer decisions')
    check('Q1', legacy_valid, '18 historical findings remain unadjudicated')
    claims_valid = (
        isinstance(claims, list) and len(claims) >= req['Q1']['human_reviewed_material_claims_min']
        and all(isinstance(x, dict) and reviewers_valid(x) and source_anchor_valid(x) and type(x.get('supported')) is bool
                and x.get('critical_false_approval') is False
                and (x['supported'] is False or
                     all(r['verdict'] in {'supported', 'corrected'} for r in x['reviewers']))
                for x in claims)
        and len({x.get('id') for x in claims if isinstance(x, dict)}) == len(claims)
    )
    check('Q1', claims_valid, '50+ distinct, independently reviewed material claims required')
    precision = sum(x['supported'] for x in claims) / len(claims) if claims_valid else None
    check('Q1', precision is not None and precision >= req['Q1']['source_supported_precision_min'],
          'independent precision must be at least 98%')
    check('Q1', type(audit.get('critical_false_approvals')) is int
          and audit['critical_false_approvals'] == 0, 'critical false approvals must be measured at zero')
    check('Q1', type(audit.get('previously_approved_lost')) is int
          and audit['previously_approved_lost'] == 0, 'existing human-approved findings cannot be lost')
    check('Q1', number(audit.get('legacy_quotes_retained'))
          and audit['legacy_quotes_retained'] >= req['Q1']['legacy_exact_quotes_retained_min'],
          '346 verified prior page/quote pairs not preserved')
    check('Q1', number(audit.get('screen_passed_retained'))
          and audit['screen_passed_retained'] >= req['Q1']['current_validator_screen_passed_supported_min'],
          '54 prior validated findings not preserved')
    recovered = sum(x.get('source_confirmed_recovery') is True for x in legacy) if legacy_valid else 0
    recall_gain = audit.get('answerable_recall_gain_pp')
    check('Q1', recovered >= req['Q1']['source_confirmed_recoveries_min_if_no_recall_improvement']
          or (number(recall_gain) and recall_gain >=
              req['Q1']['heldout_answerable_recall_gain_pp_if_no_four_recoveries']),
          'requires 4 source-backed recoveries or >=5pp independently measured recall')
    heldout_ids = {x['id'] for x in heldout} if valid_heldout else set()
    heldout_claims = [x for x in claims if isinstance(x, dict) and x.get('paper_id') in heldout_ids]
    heldout_good = (
        claims_valid and bool(heldout_ids) and bool(heldout_claims)
        and {x['paper_id'] for x in heldout_claims} == heldout_ids
        and sum(x['supported'] for x in heldout_claims) / len(heldout_claims)
        >= req['Q1']['source_supported_precision_min']
        and audit.get('heldout_all_page_citations_verified') is True
    )
    check('Q1', heldout_good, 'held-out paper precision/citation accuracy not established')

    corpus_hashes = {x['sha256'] for x in regression + heldout} if valid_regression and valid_heldout else set()
    pipeline = evidence.get('pipeline') or {}
    before = pipeline.get('baseline_runs') or []
    after = pipeline.get('candidate_runs') or []

    def index_runs(runs, commit):
        if not isinstance(runs, list):
            return None
        indexed = {}
        for run in runs:
            if not isinstance(run, dict):
                return None
            pair = (run.get('paper_sha256'), run.get('repeat'))
            if (pair[0] not in corpus_hashes or type(pair[1]) is not int or pair[1] < 1
                    or pair in indexed or run.get('commit') != commit or run.get('success') is not True
                    or not isinstance(run.get('model_path'), str) or not run['model_path']
                    or not number(run.get('latency_ms'), positive=True)
                    or not number(run.get('cost_usd'))
                    or not number(run.get('peak_rss_mb'), positive=True)
                    or type(run.get('provider_attempts')) is not int or run['provider_attempts'] < 1
                    or type(run.get('prompt_tokens')) is not int or run['prompt_tokens'] < 1
                    or type(run.get('output_tokens')) is not int or run['output_tokens'] < 1):
                return None
            indexed[pair] = run
        return indexed

    left, right = index_runs(before, frozen['commit']), index_runs(after, candidate)
    expected = {(digest, repeat) for digest in corpus_hashes
                for repeat in range(1, req['Q2']['paired_repeats_min'] + 1)}
    paired = (bool(expected) and left is not None and right is not None
              and left.keys() == right.keys() and expected.issubset(left.keys())
              and all(left[pair]['model_path'] == right[pair]['model_path'] for pair in left))
    check('Q2', paired, 'complete 2+ paired full-pipeline runs with matching model paths required')
    metrics = None
    if paired:
        bp95, cp95 = p95([x['latency_ms'] for x in before]), p95([x['latency_ms'] for x in after])
        bcost, ccost = sum(x['cost_usd'] for x in before), sum(x['cost_usd'] for x in after)
        bmem, cmem = max(x['peak_rss_mb'] for x in before), max(x['peak_rss_mb'] for x in after)
        metrics = {'baseline_p95_ms': bp95, 'candidate_p95_ms': cp95,
                   'baseline_cost_usd': bcost, 'candidate_cost_usd': ccost,
                   'baseline_peak_rss_mb': bmem, 'candidate_peak_rss_mb': cmem}
        check('Q2', cp95 <= bp95 * req['Q2']['full_pipeline_p95_relative_max'], 'full-pipeline p95 worsened >5%')
        check('Q2', bcost > 0 and ccost <= bcost * req['Q2']['provider_cost_relative_max'],
              'provider cost missing or worsened >5%')
        check('Q2', cmem <= bmem * req['Q2']['peak_memory_relative_max'], 'peak RSS worsened >10%')
    check('Q2', pipeline.get('cost_basis') in {'provider_billable', 'verified_public_rate'},
          'verified provider cost basis missing')
    for field in ('service_failures_not_worse', 'provider_recovery_not_worse',
                  'backend_tests_pass', 'frontend_build_pass'):
        check('Q2', pipeline.get(field) is True, f'{field} not verified')

    release = evidence.get('release_evidence') or {}
    for field, required in req['P0'].items():
        if required is not True:
            continue
        item = release.get(field) or {}
        check('P0', item.get('passed') is True and item.get('commit') == candidate
              and isinstance(item.get('evidence_ref'), str) and bool(item['evidence_ref'].strip()),
              f'{field} missing external, commit-bound verification')

    structural_passed = not any(gates.values())
    return {'record_type': 'STRUCTURAL_CHECK_NOT_INDEPENDENT_CERTIFICATION',
            'candidate_commit': candidate,
            'gates': {name: {'status': 'BLOCKED' if reasons else 'PASS', 'failures': reasons}
                      for name, reasons in gates.items()},
            'human_claim_precision': precision, 'source_confirmed_recoveries': recovered,
            'pipeline_metrics': metrics,
            'structural_checks_passed': structural_passed,
            # Never issue deployment permission from self-reported JSON or test fixtures.
            'final_deploy_allowed': False,
            'next_action': ('INDEPENDENT_SOURCE_REVIEW_AND_RELEASE_OWNER_SIGNOFF' if structural_passed
                            else 'COMPLETE_MISSING_OR_FAILED_GATES'),
            'warning': 'Verify reviewer independence, source PDFs, bills, build logs and E2E before release.'}


def main():
    parser = argparse.ArgumentParser(description='PaperSignal release gate evidence checker')
    parser.add_argument('--evidence', required=True, type=Path)
    parser.add_argument('--policy', type=Path, default=POLICY_PATH)
    args = parser.parse_args()
    report = evaluate(json.loads(args.policy.read_text(encoding='utf-8')),
                      json.loads(args.evidence.read_text(encoding='utf-8')))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    # Zero exit status means structural validation passed, NOT release authorization.
    raise SystemExit(0 if report['structural_checks_passed'] else 1)


if __name__ == '__main__':
    main()
