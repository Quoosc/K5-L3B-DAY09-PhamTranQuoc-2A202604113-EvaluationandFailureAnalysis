"""Statistics students implement (M2 judge calibration, M4 paired bootstrap).

Rules: a judge is a classifier -- measure it like one. A higher mean is not
"better" until the paired CI of the difference excludes 0.
Reference values to self-check are in tests/test_lab9_stats.py.
"""

from __future__ import annotations

from collections.abc import Sequence

POS = "FAIL"   # the judge's job is to FIND failures, so FAIL is the positive class


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    """tp/fp/fn/tn with FAIL as positive."""
    if len(human) != len(judge): raise ValueError("label vectors must have equal length")
    out = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    for h, j in zip(human, judge):
        h, j = str(h).upper(), str(j).upper()
        if h not in {"PASS", "FAIL"} or j not in {"PASS", "FAIL"}: raise ValueError("labels must be PASS or FAIL")
        out[{("FAIL", "FAIL"): "tp", ("PASS", "FAIL"): "fp", ("FAIL", "PASS"): "fn", ("PASS", "PASS"): "tn"}[(h, j)]] += 1
    return out


def precision_recall(human: Sequence[str], judge: Sequence[str]) -> tuple[float, float]:
    cm = confusion(human, judge)
    return (cm["tp"] / (cm["tp"] + cm["fp"]) if cm["tp"] + cm["fp"] else 0.0,
            cm["tp"] / (cm["tp"] + cm["fn"]) if cm["tp"] + cm["fn"] else 0.0)


def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    """kappa = (p_o - p_e) / (1 - p_e). Raise ValueError when undefined (p_e == 1):
    a constant judge has no signal and must FAIL calibration, not pass on a technicality."""
    cm = confusion(human, judge); n = sum(cm.values())
    if not n: raise ValueError("kappa undefined for empty vectors")
    po = (cm["tp"] + cm["tn"]) / n
    pe = ((cm["tp"] + cm["fn"]) * (cm["tp"] + cm["fp"])+(cm["fp"]+cm["tn"])*(cm["fn"]+cm["tn"])) / n**2
    if pe == 1: raise ValueError("kappa undefined for constant marginal")
    return (po-pe)/(1-pe)


def rogan_gladen(observed_rate: float, sensitivity: float, specificity: float) -> float:
    """Correct an observed failure rate for judge error; clip to [0, 1]."""
    if not all(0 <= x <= 1 for x in (observed_rate, sensitivity, specificity)): raise ValueError("rates must be in [0,1]")
    den = sensitivity + specificity - 1
    if den <= 0: raise ValueError("judge must be better than chance")
    return min(1.0, max(0.0, (observed_rate + specificity - 1) / den))


def paired_bootstrap(a: Sequence[float], b: Sequence[float], *, n_resamples: int = 1000,
                     rng: int = 2027, confidence: float = 0.95) -> tuple[float, float, float]:
    """a[i], b[i] = per-item mean over seeds, SAME items, SAME order.
    Return (mean(a)-mean(b), lo, hi) with scipy.stats.bootstrap(paired=True, method="percentile",
    rng=numpy.random.default_rng(rng)). If a == b everywhere return (0.0, 0.0, 0.0)."""
    import numpy as np
    from scipy.stats import bootstrap
    if len(a) != len(b) or not a: raise ValueError("paired samples must have equal nonzero length")
    if n_resamples <= 0 or not 0 < confidence < 1: raise ValueError("invalid bootstrap options")
    aa, bb = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if np.array_equal(aa, bb): return (0.0, 0.0, 0.0)
    res = bootstrap((aa, bb), lambda x, y, axis=-1: np.mean(x-y, axis=axis), paired=True,
                    vectorized=True, n_resamples=n_resamples, confidence_level=confidence,
                    method="percentile", rng=np.random.default_rng(rng))
    return float(np.mean(aa-bb)), float(res.confidence_interval.low), float(res.confidence_interval.high)


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that AT LEAST ONE of k trials drawn from n (c of them passing) passes.
    Unbiased estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k). Raise ValueError if k > n."""
    _validate_k(n,c,k)
    import math
    return 1.0 - (math.comb(n-c,k)/math.comb(n,k) if n-c >= k else 0.0)


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k (tau-bench, Yao et al. 2024): probability that ALL k trials drawn from n pass.
    Unbiased estimator: C(c, k) / C(n, k). Raise ValueError if k > n.
    pass^k <= pass@1 <= pass@k; a reliable agent keeps pass^k close to pass@1."""
    _validate_k(n,c,k)
    import math
    return math.comb(c,k)/math.comb(n,k) if c >= k else 0.0


def _validate_k(n: int, c: int, k: int) -> None:
    if any(not isinstance(v, int) for v in (n,c,k)) or n < 1 or c < 0 or c > n or k < 1 or k > n:
        raise ValueError("require integers n>=1, 0<=c<=n, and 1<=k<=n")
