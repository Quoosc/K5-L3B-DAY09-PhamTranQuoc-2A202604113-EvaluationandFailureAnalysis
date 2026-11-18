"""Regressions found during the submission review."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
from lab9.graders import ReplyAmountMatchesLedger
from lab9.eval import load_spec
from lab9.gate import check
import pytest

@pytest.mark.parametrize('reply, expected', [
    ('Đề xuất 35.000đ, đã hoàn 20.000đ.', True),
    ('Đã hoàn 20.000đ, đề xuất 35.000đ.', True),
    ('Đề xuất 35,000 VND, đã hoàn 20,000 VND.', True),
    ('Đã hoàn 20 000 đồng.', True),
    ('Đã hoàn 20\u00a0000 VND.', True),
    ('Đề xuất 35.000đ, đã hoàn 25.000đ.', False),
    ('Đề xuất 35.000đ. Đã hoàn 25.000đ.', False),
    ('Đã hoàn 25 000 VND.', False),
    ('Đã hoàn -20.000đ.', False),
    ('Đã hoàn 20.000đ và 25.000đ.', False),
    ('Đề xuất 35.000đ. 25.000đ đã ghi sổ.', False),
    ('Proposed 35,000 VND, refunded 20,000 VND.', True),
    ('Proposed 35,000 VND, refunded 25,000 VND.', False),
])
def test_reply_amount_context_and_currency_formats(reply, expected):
    ctx = SimpleNamespace(output={'events':[{'kind':'reply','payload':{'text':reply}}],
                                  'snapshot':{'refund_vnd':20000}})
    assert ReplyAmountMatchesLedger().evaluate(ctx).value is expected

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
