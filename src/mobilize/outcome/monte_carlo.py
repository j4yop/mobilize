"""Monte Carlo pricing engine for the Wildlife Conservation Bond.

Model
-----
Rhino population N_t follows geometric Brownian motion (in log space):

    N_t = N_0 * exp(sum of (mu_d - 0.5*sigma_d^2)*dt + sigma_d*sqrt(dt)*Z_t)

where mu_d is the annual net growth DRIFT (births - deaths - poaching +
conservation effect) and sigma_d the annual volatility of the growth rate.
The realized 5-year growth rate is

    X = (N_T - N_0) / N_0          (population growth, per press-release tiers)

Wait — the official KPI is the ANNUALIZED growth rate over the term
("Final Rhino Population Growth Rate"). We interpret X as the annualized
(compound) growth: X = (N_T/N_0)^(1/T) - 1, matching how Conservation Alpha
reports it. We compute BOTH and price off the annualized definition, with
the alternative disclosed.

Pricing outputs
---------------
- P(X in each tier) -> expected success payment per $1,000
- Investor expected return: (1000 + E[success]) / issue_price per $1,000,
  annualized
- Comparison: vanilla IBRD 5y bond yield at issuance (Mar 2022 ~1.75% area,
  parameterized from the AAA curve) -> the "concession" investors make
- Donation leverage: conservation dollars mobilized per dollar of GEF
  success-payment risk + investor concession

Governance sensitivity (the novel link)
----------------------------------------
Conservation execution risk scales with country governance quality: we
model mu_d = mu_base * f(gov_score) where f is increasing in governance
(noise-reduction interpretation), and sigma_d = sigma_base * g(gov_score)
where g is decreasing (better institutions -> lower execution variance).
Both f and g are simple, disclosed functional forms with tunable
elasticities. The dashboard shows: required success payment (to hold
investor expected return fixed) as governance varies — the "success
premium schedule".
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from mobilize.outcome.terms import RhinoBondTerms


@dataclass(frozen=True)
class RhinoMCConfig:
    n_paths: int = 100_000
    seed: int = 42
    mu_base: float = 0.04  # base annual growth drift (parks' recent track record ~4%)
    sigma_base: float = 0.03  # annual vol of the growth rate
    vanilla_yield: float = 0.0175  # IBRD 5y USD area, Mar-2022 (AAA curve)


def simulate_growth_rates(
    cfg: RhinoMCConfig,
    n_years: float = 5.0,
    gov_score: float | None = None,
    mu_override: float | None = None,
    sigma_override: float | None = None,
) -> np.ndarray:
    """Simulate annualized rhino growth rates X under GBM.

    Returns array of X = (N_T/N_0)^(1/T) - 1 per path.
    Governance (0-100) shifts mu up and sigma down (disclosed elasticities).
    """
    rng = np.random.default_rng(cfg.seed)
    mu = cfg.mu_base if mu_override is None else mu_override
    sigma = cfg.sigma_base if sigma_override is None else sigma_override
    if gov_score is not None:
        # f: drift scales +0.5pp per 10 governance points above 50
        mu = mu + 0.005 * (gov_score - 50.0) / 10.0
        # g: vol scales -10% per 10 governance points above 50 (floored)
        sigma = max(sigma * (1 - 0.01 * (gov_score - 50.0) / 10.0), 0.005)
    dt = 1.0
    steps = int(n_years)
    # antithetic variates for stability
    z = rng.standard_normal((cfg.n_paths // 2, steps))
    z = np.vstack([z, -z])
    log_growth = (mu - 0.5 * sigma**2) * n_years + sigma * np.sqrt(dt) * z.sum(axis=1)
    total_growth = np.exp(log_growth) - 1.0
    return (1.0 + total_growth) ** (1.0 / n_years) - 1.0


def price_wcb(
    terms: RhinoBondTerms,
    cfg: RhinoMCConfig,
    gov_score: float | None = None,
    mu_override: float | None = None,
    sigma_override: float | None = None,
) -> dict:
    """Full pricing of the WCB under the GBM model.

    Returns dict with tier probabilities, expected success payment,
    investor return decomposition, and leverage metrics.
    """
    xs = simulate_growth_rates(
        cfg, terms.tenor_years, gov_score, mu_override, sigma_override
    )

    # tier probabilities
    p_fail = float(np.mean(xs <= 0.0))
    p_t1 = float(np.mean((xs > 0.0) & (xs <= 0.02)))
    p_t2 = float(np.mean((xs > 0.02) & (xs <= 0.04)))
    p_t3 = float(np.mean(xs > 0.04))

    per_1000 = np.array(
        [
            terms.success_payment_per_1000(x) for x in (0.0, 0.01, 0.03, 0.05)
        ]
    )  # representative tier payments
    expected_success = (
        p_fail * per_1000[0] + p_t1 * per_1000[1] + p_t2 * per_1000[2] + p_t3 * per_1000[3]
    )

    issue = terms.issue_price * 1_000.0
    expected_total = 1_000.0 + expected_success
    expected_ann_return = (expected_total / issue) ** (1 / terms.tenor_years) - 1

    # concession vs vanilla IBRD bond
    concession = cfg.vanilla_yield - expected_ann_return

    # leverage: conservation $ mobilized per $ of donor + investor subsidy
    # ZAR/USD ~15.0 at the March-2022 pricing date (disclosed assumption)
    conservation_usd = terms.conservation_payment_zar / 15.0
    investor_subsidy_usd = concession * terms.size_usd * (
        (1 - (1 + cfg.vanilla_yield) ** -terms.tenor_years) / cfg.vanilla_yield
    ) if cfg.vanilla_yield > 0 else 0.0
    donor_risk_usd = terms.max_success_payment_usd * (1 - p_fail)
    denom = investor_subsidy_usd + donor_risk_usd
    leverage = conservation_usd / denom if denom > 0 else np.nan

    return {
        "p_fail": p_fail,
        "p_tier1": p_t1,
        "p_tier2": p_t2,
        "p_tier3": p_t3,
        "p_any_success": 1 - p_fail,
        "expected_success_per_1000": float(expected_success),
        "expected_total_success_usd": float(expected_success) * terms.size_usd / 1_000.0,
        "issue_price_per_1000": issue,
        "expected_annual_return": float(expected_ann_return),
        "vanilla_yield": cfg.vanilla_yield,
        "concession_pp": float(concession * 100),
        "conservation_usd": float(conservation_usd),
        "donor_expected_outlay_usd": float(donor_risk_usd),
        "investor_subsidy_usd": float(investor_subsidy_usd),
        "donor_leverage": float(leverage),
        "growth_mean": float(xs.mean()),
        "growth_std": float(xs.std()),
    }


def required_success_payment_for_target_return(
    terms: RhinoBondTerms,
    cfg: RhinoMCConfig,
    target_return: float,
    gov_score: float | None = None,
) -> float:
    """Solve: what success payment per $1,000 (tier-3, uniform) makes the
    investor's expected annual return equal to target_return?

    This is the "success premium schedule" — how much a donor must offer
    as a function of country governance, holding investor economics fixed.
    """
    xs = simulate_growth_rates(cfg, terms.tenor_years, gov_score)
    p_success = float(np.mean(xs > 0.0))  # any success tier receives payment
    # expected return equation: (1000 + p_success * S) / issue = (1+y)^T
    issue = terms.issue_price * 1_000.0
    target_total = issue * (1 + target_return) ** terms.tenor_years
    needed_success = target_total - 1_000.0
    return needed_success / p_success if p_success > 0 else float("inf")


def drift_sensitivity(
    terms: RhinoBondTerms,
    cfg: RhinoMCConfig,
    mus: tuple[float, ...] = (0.02, 0.03, 0.04, 0.05, 0.06),
) -> list[dict]:
    """Pricing across drift assumptions — the model's most sensitive input."""
    out = []
    for mu in mus:
        p = price_wcb(terms, cfg, mu_override=mu)
        out.append(
            {
                "drift": mu,
                "p_any_success": p["p_any_success"],
                "p_tier3": p["p_tier3"],
                "expected_success_per_1000": p["expected_success_per_1000"],
                "expected_annual_return": p["expected_annual_return"],
                "concession_pp": p["concession_pp"],
                "donor_leverage": p["donor_leverage"],
            }
        )
    return out


def governance_sensitivity(
    terms: RhinoBondTerms,
    cfg: RhinoMCConfig,
    target_return: float | None = None,
    gov_range: tuple[float, float] = (10.0, 90.0),
    steps: int = 9,
) -> list[dict]:
    """Required success payment schedule across governance scores.

    Uses the issuer-country (South Africa) governance pillar range from the
    M1 panel as context; here we sweep a generic 0-100 governance score.
    target_return defaults to the baseline (no-governance-shift) expected
    return, so the schedule isolates pure execution-risk effects.
    """
    base = price_wcb(terms, cfg)
    target = target_return if target_return is not None else base["expected_annual_return"]
    out = []
    for gov in np.linspace(gov_range[0], gov_range[1], steps):
        req = required_success_payment_for_target_return(terms, cfg, target, float(gov))
        p = price_wcb(terms, cfg, gov_score=float(gov))
        out.append(
            {
                "gov_score": float(gov),
                "required_success_per_1000": float(req),
                "p_success": p["p_any_success"],
                "expected_return": p["expected_annual_return"],
                "concession_pp": p["concession_pp"],
            }
        )
    return out


def outcome_bond_comparisons() -> list[dict]:
    """Static comparison table of all seven IBRD outcome bonds.

    Returns per-bond: guaranteed return, maximum potential return, and the
    outcome-linked spread (max - min), computed from the official terms in
    mobilize.outcome.terms. Used by the dashboard's bond-family tab.
    """
    from mobilize.outcome.terms import (
        ALL_BONDS,
        CapitalAtRiskTerms,
        DiscountLinkedTerms,
        OutcomeBondTerms,
        RhinoBondTerms,
    )

    rows: list[dict] = []
    for key, b in ALL_BONDS.items():
        if isinstance(b, RhinoBondTerms):
            # Rhino: guaranteed return comes from the issue discount only;
            # max return = discount + full tier-3 success payment
            guaranteed = (1_000.0 / (b.issue_price * 1_000.0)) ** (1 / b.tenor_years) - 1
            max_total = (
                (1_000.0 + b.success_tiers[-1][1])
                / (b.issue_price * 1_000.0)
            ) ** (1 / b.tenor_years) - 1
            variable_note = "GEF success payment at maturity ($0-$91.73/$1k, tiered)"
            structure = "discount + terminal success payment"
        elif isinstance(b, DiscountLinkedTerms):
            guaranteed = (1_000.0 / (b.issue_price * 1_000.0)) ** (1 / b.tenor_years) - 1
            max_total = b.max_total_return
            variable_note = f"semi-annual {b.outcome_unit} linked coupons (capped)"
            structure = "discount + capped variable coupons"
        elif isinstance(b, OutcomeBondTerms):
            guaranteed = b.fixed_coupon
            max_total = b.max_total_return
            variable_note = f"annual {b.outcome_unit} linked interest"
            structure = "par + fixed + outcome-linked coupon"
        elif isinstance(b, CapitalAtRiskTerms):
            guaranteed = b.fixed_coupon
            max_total = b.fixed_coupon  # no upside; the risk is on principal
            variable_note = (
                f"repayment of {b.principal_at_risk_share:.0%} principal conditional on "
                f"{b.outcome_unit.lower()}"
            )
            structure = "capital-at-risk note"
        else:  # pragma: no cover
            continue
        rows.append(
            {
                "key": key,
                "name": getattr(b, "name", "Wildlife Conservation (Rhino) Bond"),
                "size_usd": float(b.size_usd),
                "tenor_years": float(getattr(b, "tenor_years", 0)),
                "maturity": getattr(b, "maturity", ""),
                "guaranteed_return": float(guaranteed),
                "max_total_return": float(max_total),
                "outcome_spread_pp": float((max_total - guaranteed) * 100),
                "outcome_unit": getattr(b, "outcome_unit", "rhino growth tiers"),
                "outcome_payer": getattr(b, "outcome_payer", "GEF"),
                "country": getattr(b, "country", "South Africa"),
                "theme": getattr(b, "theme", "black rhino conservation"),
                "structure": structure,
                "variable_note": variable_note,
                "principal_protected": False
                if isinstance(b, CapitalAtRiskTerms)
                else bool(getattr(b, "principal_protected", True)),
                "url": getattr(b, "url", ""),
            }
        )
    return rows
