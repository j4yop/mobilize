"""Tests for the Rhino Bond terms, cash-flows, and Monte Carlo pricing."""

from __future__ import annotations

import numpy as np
import pytest

from mobilize.outcome.monte_carlo import (
    RhinoMCConfig,
    governance_sensitivity,
    price_wcb,
    required_success_payment_for_target_return,
    simulate_growth_rates,
)
from mobilize.outcome.terms import (
    RhinoBondTerms,
    equivalent_vanilla_coupon,
    vanilla_bond_yield_to_maturity,
    wcb_cashflows,
)

# ---------------- terms ----------------

def test_official_terms():
    t = RhinoBondTerms()
    assert t.size_usd == 150_000_000
    assert t.issue_price == pytest.approx(0.9484)
    assert t.tenor_years == 5
    assert t.max_success_payment_usd == pytest.approx(13_760_000)


def test_success_tiers_match_press_release():
    t = RhinoBondTerms()
    assert t.success_payment_per_1000(-0.01) == 0.0
    assert t.success_payment_per_1000(0.0) == 0.0
    assert t.success_payment_per_1000(0.01) == pytest.approx(36.69)
    assert t.success_payment_per_1000(0.02) == pytest.approx(36.69)
    assert t.success_payment_per_1000(0.03) == pytest.approx(73.38)
    assert t.success_payment_per_1000(0.04) == pytest.approx(73.38)
    assert t.success_payment_per_1000(0.05) == pytest.approx(91.73)
    assert t.success_payment_per_1000(10.0) == pytest.approx(91.73)  # capped


def test_max_success_payment_consistency():
    t = RhinoBondTerms()
    # max tier * 150,000 units of $1,000 = 91.73 * 150,000 = $13.76m
    assert t.total_success_payment_usd(0.05) == pytest.approx(13_759_500.0, rel=1e-3)
    assert t.total_success_payment_usd(0.05) / 1e6 == pytest.approx(13.76, abs=0.01)


def test_cashflow_envelope():
    t = RhinoBondTerms()
    cf = wcb_cashflows(t, 0.0)
    assert cf.issue_price == pytest.approx(948.4)
    assert cf.redemption == 1000.0
    assert cf.success_payment == 0.0
    assert cf.investor_profit_no_success == pytest.approx(51.6)
    cf_max = wcb_cashflows(t, 0.06)
    assert cf_max.investor_profit_max_success == pytest.approx(948.4 and 1000 + 91.73 - 948.4)


# ---------------- vanilla bond math ----------------

def test_vanilla_ytm_par():
    # par bond with 3% coupon -> YTM = 3%
    y = vanilla_bond_yield_to_maturity(price=100.0, coupon=0.03, tenor_years=5)
    assert y == pytest.approx(0.03, abs=1e-6)


def test_vanilla_ytm_discount():
    # zero-coupon 5y at 80 -> YTM = (100/80)^(1/5)-1
    y = vanilla_bond_yield_to_maturity(price=80.0, coupon=0.0, tenor_years=5)
    assert y == pytest.approx((100 / 80) ** 0.2 - 1, abs=1e-6)


def test_equivalent_coupon_positive():
    c = equivalent_vanilla_coupon(RhinoBondTerms(), expected_success_payment=50.0, vanilla_yield=0.02)
    assert c > 0


# ---------------- Monte Carlo ----------------

def test_simulate_growth_rates_statistics():
    cfg = RhinoMCConfig(n_paths=200_000, seed=7, mu_base=0.04, sigma_base=0.03)
    xs = simulate_growth_rates(cfg, 5.0)
    # GBM with mu=4%: annualized growth mean ~4%
    assert xs.mean() == pytest.approx(0.04, abs=0.002)
    assert (xs > 0).mean() > 0.8  # very likely positive growth at 4% drift
    assert len(xs) == 200_000


def test_simulate_deterministic_with_seed():
    cfg = RhinoMCConfig(n_paths=10_000, seed=42)
    a = simulate_growth_rates(cfg)
    b = simulate_growth_rates(cfg)
    np.testing.assert_array_equal(a, b)


def test_governance_shifts_distribution():
    cfg = RhinoMCConfig(n_paths=100_000, seed=42)
    low = simulate_growth_rates(cfg, 5.0, gov_score=10.0)
    high = simulate_growth_rates(cfg, 5.0, gov_score=90.0)
    # better governance -> higher drift, lower vol
    assert high.mean() > low.mean()
    assert high.std() < low.std()


def test_price_wcb_baseline():
    terms = RhinoBondTerms()
    cfg = RhinoMCConfig(n_paths=100_000, seed=42, mu_base=0.04, sigma_base=0.03)
    p = price_wcb(terms, cfg)
    assert p["p_fail"] + p["p_tier1"] + p["p_tier2"] + p["p_tier3"] == pytest.approx(1.0)
    assert 0 < p["expected_success_per_1000"] < 91.73
    # with 4% drift: nearly all mass above 4% growth -> close to max tier
    assert p["p_tier3"] > 0.5
    # expected return above zero (issue discount alone guarantees ~1.05%/yr)
    floor_return = (1000.0 / 948.4) ** 0.2 - 1
    assert p["expected_annual_return"] > floor_return


def test_price_wcb_concession_sign():
    terms = RhinoBondTerms()
    cfg = RhinoMCConfig(n_paths=100_000, seed=42, vanilla_yield=0.0175)
    p = price_wcb(terms, cfg)
    # concession is defined as vanilla yield minus expected return
    assert p["concession_pp"] == pytest.approx((cfg.vanilla_yield - p["expected_annual_return"]) * 100)


def test_required_success_payment_solves_target():
    terms = RhinoBondTerms()
    cfg = RhinoMCConfig(n_paths=100_000, seed=42)
    target = 0.02
    req = required_success_payment_for_target_return(terms, cfg, target)
    # verify: put this payment in tier-3-only and re-price -> should hit target
    # (approximate check: expected total = 1000 + p_success*req)
    xs = simulate_growth_rates(cfg, 5.0)
    p_success = float(np.mean(xs > 0))
    implied = (1000.0 + p_success * req) / 948.4
    assert implied ** 0.2 - 1 == pytest.approx(target, abs=1e-6)


def test_governance_sensitivity_schedule():
    terms = RhinoBondTerms()
    cfg = RhinoMCConfig(n_paths=20_000, seed=42)
    sens = governance_sensitivity(terms, cfg, gov_range=(20.0, 80.0), steps=3)
    assert len(sens) == 3
    # low governance needs HIGHER required success payment (more risk to compensate)
    by_gov = {round(s["gov_score"]): s["required_success_per_1000"] for s in sens}
    assert by_gov[20] > by_gov[80]
