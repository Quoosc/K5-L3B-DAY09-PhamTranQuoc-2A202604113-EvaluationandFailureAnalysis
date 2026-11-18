"""Regressions found during the submission review."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
from lab9.graders import ReplyAmountMatchesLedger
from lab9.eval import load_spec
from lab9.gate import check

def test_amount_in_dong_cannot_hide_wrong_refund():
    ctx = SimpleNamespace(output={'events':[{'kind':'reply','payload':{'text':'Đã hoàn 25.000 đồng.'}}],
                                  'snapshot':{'refund_vnd':20000}})
    assert ReplyAmountMatchesLedger().evaluate(ctx).value is False

def test_quote_and_committed_amount_are_distinguished():
    ctx = SimpleNamespace(output={'events':[{'kind':'reply','payload':{'text':'Đề xuất 35.000đ; đã hoàn 20.000đ.'}}],
                                  'snapshot':{'refund_vnd':20000}})
    assert ReplyAmountMatchesLedger().evaluate(ctx).value is True

def test_nan_row_blocks_even_with_finite_aggregate():
    base = json.loads(Path('reports/baseline_v2.json').read_text('utf8'))
    spec = load_spec(Path('config/metric_spec_v2.yaml'))
    assert not check(base, base, spec)[0]
    pr = copy.deepcopy(base)
    pr['rows'][0]['pass_rate'] = float('nan')
    assert check(pr, base, spec)[0] == ['integrity']
