"""Reproducible review evidence; never changes the instructor variants or Lab 8."""
import json
import copy
import csv
from pathlib import Path
from types import SimpleNamespace
from lab8.shapes import SHAPES
from lab9.variant_agent import make_shape
from lab9.trace_case import investigate
from lab9.graders import ReplyAmountMatchesLedger
from lab9.eval import load_spec, run_eval
from lab9 import gate, mutation, variants

def main():
    variants.register()
    evidence = {}
    coding = []
    first_wrong = {'leaky_trace': (1, 'FM-01'), 'ignore_denied': (4, 'FM-02'),
                   'ticket_trust': (3, 'FM-03'), 'sum_parts': (4, 'FM-04'),
                   'pre_deducted': (5, 'FM-05'), 'stale_clause': (3, 'FM-06'),
                   'sibling_refund': (4, 'FM-07'), 'misreport': (4, 'FM-08')}
    for bug, claim in [('leaky_trace','C-005'), ('ignore_denied','C-007'),
                       ('ticket_trust','C-002'), ('sum_parts','C-014'),
                       ('pre_deducted','C-014'), ('stale_clause','C-006'),
                       ('sibling_refund','C-001'), ('misreport','C-008')]:
        name = 'review_' + bug
        SHAPES[name] = make_shape(name, frozenset({'no_override', bug}))
        evidence[bug] = investigate(name, claim, 11)
        step, fm = first_wrong[bug]
        trial = evidence[bug]['trial']
        event = trial['events'][step-1]
        coding.append({'anchor': f'A{len(coding)+1:02}', 'fm': fm, 'shape': name,
                       'claim_id': claim, 'seed': 11, 'first_wrong_step': step,
                       'kind': event['kind'], 'payload': json.dumps(event['payload'], ensure_ascii=False),
                       'ledger': json.dumps(trial['snapshot'], ensure_ascii=False),
                       'evidence': f'review_evidence.json#{bug}'})
    evidence['fixed_controls'] = {c: investigate('fixed', c, 11)
                                  for c in sorted({r['claim_id'] for r in coding})}
    assert all(c['trial']['lab8_pass'] for c in evidence['fixed_controls'].values())
    for text, want in [('Da hoan 25.000 đồng.', False),
                       ('Đề xuất 35.000đ; đã hoàn 20.000đ.', True)]:
        ctx = SimpleNamespace(output={'events':[{'kind':'reply','payload':{'text':text}}],
                                      'snapshot':{'refund_vnd':20000}})
        assert ReplyAmountMatchesLedger().evaluate(ctx).value == want
    spec = load_spec(Path('config/metric_spec_v2.yaml'))
    base = json.loads(Path('reports/baseline_v2.json').read_text('utf8'))
    for trap in ['row_nan','duplicate','evaluator_failure','relabel']:
        rep = copy.deepcopy(base)
        if trap == 'row_nan': rep['rows'][0]['pass_rate'] = float('nan')
        if trap == 'duplicate': rep['rows'][-1] = copy.deepcopy(rep['rows'][0])
        if trap == 'evaluator_failure': rep['evaluator_failures'] = ['simulated failure']
        if trap == 'relabel': rep['rows'][0]['slices'] = ['changed']
        assert gate.check(rep, base, spec)[0], trap
    evidence['integrity_probes'] = '4/4 blocked; baseline self comparison passes'
    assert not gate.check(base, base, spec)[0]
    out = Path('reports/review_evidence.json')
    out.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf8')
    with Path('reports/coding_sheet.csv').open('w', encoding='utf8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(coding[0]))
        writer.writeheader()
        writer.writerows(coding)
    print('Review evidence written; money formats and integrity probes PASS')
    for bug, case in evidence.items():
        if not isinstance(case, dict) or 'trial' not in case: continue
        t = case['trial']
        print(bug, t['result']['claim_id'], t['lab8_reason'], t['snapshot'], t['unexpected_rows'])

if __name__ == '__main__':
    main()
