"""Run the Rhino Bond pricing lab: baseline pricing + governance sensitivity.

Writes data/processed/outcome_bond.parquet and prints a summary.
Also extracts South Africa's governance score from the M1 panel for context.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from mobilize.outcome.monte_carlo import (  # noqa: E402
    RhinoMCConfig,
    drift_sensitivity,
    governance_sensitivity,
    price_wcb,
)
from mobilize.outcome.terms import RhinoBondTerms, wcb_cashflows  # noqa: E402

DATA_DIR = REPO_ROOT / "data" / "processed"
PANEL_PATH = DATA_DIR / "esg_panel.parquet"
OUT_PATH = DATA_DIR / "outcome_bond.parquet"


def main() -> None:
    terms = RhinoBondTerms()
    cfg = RhinoMCConfig()

    print("=" * 70)
    print("WILDLIFE CONSERVATION BOND ('RHINO BOND') — MONTE CARLO PRICING LAB")
    print("=" * 70)
    print(
        f"\nDeal: USD {terms.size_usd/1e6:.0f}m, 5y, issue {terms.issue_price:.2%}, "
        f"no coupon, par redemption, max success ${terms.max_success_payment_usd/1e6:.2f}m"
    )

    # South Africa governance context from our own M1 panel
    zaf_gov = None
    if PANEL_PATH.exists():
        panel = pd.read_parquet(PANEL_PATH)
        zaf = panel[(panel["iso3"] == "ZAF") & (panel["year"] == 2022)]
        if len(zaf) and pd.notna(zaf["pillar_G"].iloc[0]):
            zaf_gov = float(zaf["pillar_G"].iloc[0])
            print(f"\nSouth Africa governance pillar (2022, this repo's M1 panel): {zaf_gov:.1f}/100")

    # ---- Baseline pricing ----
    print("\n[1/4] Baseline pricing (governance-neutral) ...")
    base = price_wcb(terms, cfg)
    print_pricing(base, "baseline")

    # ---- With South Africa governance ----
    if zaf_gov is not None:
        print(f"\n[2/4] Pricing with South Africa governance = {zaf_gov:.0f} ...")
        sa = price_wcb(terms, cfg, gov_score=zaf_gov)
        print_pricing(sa, "south africa")

    # ---- Drift sensitivity (the key model input) ----
    print("\n[3/4] Drift sensitivity (conservation effectiveness) ...")
    drift_df = pd.DataFrame(drift_sensitivity(terms, cfg))
    print("\nDrift | P(>4%) | E[success]/$1k | E[return] | Concession (pp) | Leverage")
    print("-" * 72)
    for _, r in drift_df.iterrows():
        print(
            f" {r.drift:4.0%}  | {r.p_tier3:.3f}  |   ${r.expected_success_per_1000:5.2f}"
            f"    |  {r.expected_annual_return:.2%}   |     {r.concession_pp:5.2f}      |  {r.donor_leverage:.2f}x"
        )

    # ---- Governance sensitivity schedule ----
    print("\n[4/4] Governance -> required success premium schedule ...")
    sens = governance_sensitivity(terms, cfg)
    sens_df = pd.DataFrame(sens)
    print("\nGov score | P(any success) | Required success/$1k | Concession (pp)")
    print("-" * 62)
    for _, r in sens_df.iterrows():
        print(
            f"   {r.gov_score:4.0f}   |     {r.p_success:.3f}       |"
            f"      ${r.required_success_per_1000:6.2f}       |   {r.concession_pp:5.2f}"
        )

    # ---- Cash-flow envelope sanity ----
    print("\nCash-flow envelope per $1,000:")
    for x in (0.0, 0.01, 0.03, 0.05):
        cf = wcb_cashflows(terms, x)
        print(
            f"  X={x:4.0%}: pay ${cf.issue_price:.2f} at t0 -> receive "
            f"${cf.redemption:.0f} + ${cf.success_payment:.2f} success at T "
            f"(profit ${cf.investor_profit_no_success:.2f}-${cf.investor_profit_max_success:.2f})"
        )

    # ---- Save ----
    rows = []
    for label, res in [("baseline", base)] + (
        [("south_africa", sa)] if zaf_gov is not None else []
    ):
        flat = {"scenario": label}
        flat.update(res)
        rows.append(flat)
    scenarios = pd.DataFrame(rows)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    scenarios.to_parquet(OUT_PATH)
    sens_df.to_parquet(OUT_PATH.with_name("outcome_bond_sensitivity.parquet"))
    drift_df.to_parquet(OUT_PATH.with_name("outcome_bond_drift.parquet"))
    print(f"\nSaved: {OUT_PATH} and sensitivity schedule")

    # headline interpretation
    print("\n" + "=" * 70)
    print("HEADLINE")
    print("=" * 70)
    print(
        f"Expected success payment: ${base['expected_success_per_1000']:.2f}/$1,000"
        f" (${base['expected_total_success_usd']/1e6:.2f}m total)"
    )
    print(
        f"Investor expected return: {base['expected_annual_return']:.2%}/yr "
        f"vs vanilla IBRD {base['vanilla_yield']:.2%} -> concession {base['concession_pp']:.2f}pp"
    )
    print(
        f"Donor (GEF) expected outlay: ${base['donor_expected_outlay_usd']/1e6:.2f}m; "
        f"conservation mobilized ~${base['conservation_usd']/1e6:.1f}m -> "
        f"leverage ~{base['donor_leverage']:.1f}x"
    )
    lo, hi = sens_df["required_success_per_1000"].min(), sens_df["required_success_per_1000"].max()
    print(
        f"\nGovernance sensitivity: across gov scores 10-90, the required success "
        f"payment to hold investor economics fixed spans ${lo:.2f}-${hi:.2f}/$1,000 "
        f"({(hi-lo):.2f} spread) — the 'governance success premium'."
    )


def print_pricing(res: dict, label: str) -> None:
    print(f"  --- {label} ---")
    print(
        f"  Tier probabilities: fail={res['p_fail']:.3f}  t1(0-2%)={res['p_tier1']:.3f}"
        f"  t2(2-4%)={res['p_tier2']:.3f}  t3(>4%)={res['p_tier3']:.3f}"
    )
    print(
        f"  Expected success: ${res['expected_success_per_1000']:.2f}/$1k "
        f"(${res['expected_total_success_usd']/1e6:.2f}m)"
    )
    print(
        f"  Investor E[return]: {res['expected_annual_return']:.2%}/yr | "
        f"concession vs vanilla: {res['concession_pp']:.2f}pp"
    )
    print(
        f"  Simulated growth: mean {res['growth_mean']:.2%}, std {res['growth_std']:.2%}"
    )


if __name__ == "__main__":
    main()
