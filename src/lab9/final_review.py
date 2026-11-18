"""Reproducible review evidence; never changes the instructor variants or Lab 8."""
import json
import copy
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
    for bug, claim in [('leaky_trace','C-005'), ('ignore_denied','C-007'),
                       ('ticket_trust','C-002'), ('sum_parts','C-014'),
                       ('pre_deducted','C-014'), ('stale_clause','C-006'),
                       ('sibling_refund','C-001'), ('misreport','C-008')]:
        name = 'review_' + bug
        SHAPES[name] = make_shape(name, frozenset({'no_override', bug}))
        evidence[bug] = investigate(name, claim, 11)
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
    print('Review evidence written; money formats and integrity probes PASS')
    for bug, case in evidence.items():
        if not isinstance(case, dict): continue
        t = case['trial']
        print(bug, t['result']['claim_id'], t['lab8_reason'], t['snapshot'], t['unexpected_rows'])

if __name__ == '__main__':
    main()
