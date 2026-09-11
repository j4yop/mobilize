"""Wildlife Conservation Bond ("Rhino Bond") — deal terms and cash-flow model.

All terms from the official World Bank press release (March 23, 2022):
https://www.worldbank.org/en/news/press-release/2022/03/23/wildlife-conservation-bond-boosts-south-africa-s-efforts-to-protect-black-rhinos-and-support-local-communities

Structure:
- IBRD (AAA/Aaa) issues a 5y USD 150m bond at 94.84, no coupon, par redemption.
- Instead of coupons, conservation investment payments (ZAR 152m over 5y)
  fund rhino conservation at Addo Elephant NP & Great Fish River NR.
- At maturity, investors receive a Conservation Success Payment (funded by a
  GEF performance-based grant) tiered on the 5-year black rhino growth rate X:

    X <= 0%        -> $0.00  per $1,000
    0% < X <= 2%    -> $36.69 per $1,000
    2% < X <= 4%    -> $73.38 per $1,000
    X > 4%          -> $91.73 per $1,000   (max total $13.76m)

So investor return = principal protection (AAA) + a call option on rhino growth,
written by GEF, purchased by investors via the 5.16% issue-price discount.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RhinoBondTerms:
    """Official WCB transaction terms (all public)."""

    size_usd: float = 150_000_000.0
    issue_price: float = 0.9484  # percent of nominal
    tenor_years: float = 5.0
    settlement: str = "2022-03-31"
    maturity: str = "2027-03-31"
    isin: str = "US45906M3A71"
    conservation_payment_zar: float = 152_000_000.0
    max_success_payment_usd: float = 13_760_000.0

    # Success payment per $1,000 nominal, tiered on 5y rhino growth rate X.
    success_tiers: tuple[tuple[float, float], ...] = (
        # (upper bound of X, payment per $1,000); X <= lower -> $0
        (0.00, 0.00),
        (0.02, 36.69),
        (0.04, 73.38),
        (float("inf"), 91.73),
    )

    # Baseline black rhino population at AENP + GFRNR (publicly reported
    # ~2,000 combined at inception). Parameterized for the Monte Carlo.
    baseline_population: float = 2_000.0

    def success_payment_per_1000(self, growth_rate: float) -> float:
        """Success payment per $1,000 nominal for a realized growth rate X."""
        for upper, payment in self.success_tiers:
            if growth_rate <= upper:
                return payment
        return self.success_tiers[-1][1]

    def total_success_payment_usd(self, growth_rate: float) -> float:
        """Total success payment (USD) for a realized growth rate X."""
        per_1000 = self.success_payment_per_1000(growth_rate)
        return per_1000 * (self.size_usd / 1_000.0)


@dataclass
class BondCashFlows:
    """Per-$1,000 cash-flow decomposition of the WCB vs a vanilla bullet."""

    issue_price: float  # paid at t=0 (per $1,000 nominal)
    redemption: float  # received at maturity
    success_payment: float  # outcome-dependent, received at maturity
    vanilla_coupon: float = 0.0  # coupon of the comparable vanilla bond
    vanilla_price: float = 100.0

    @property
    def investor_profit_no_success(self) -> float:
        """Profit vs issue price if the project fails (X <= 0)."""
        return self.redemption - self.issue_price

    @property
    def investor_profit_max_success(self) -> float:
        return self.redemption + self.success_payment - self.issue_price


def wcb_cashflows(terms: RhinoBondTerms, realized_growth: float) -> BondCashFlows:
    """Cash-flow envelope of the WCB given a realized rhino growth rate."""
    per_1000_issue = terms.issue_price * 1_000.0
    success = terms.success_payment_per_1000(realized_growth)
    return BondCashFlows(
        issue_price=per_1000_issue,
        redemption=1_000.0,
        success_payment=success,
    )


def vanilla_bond_yield_to_maturity(
    price: float, coupon: float, tenor_years: float, face: float = 100.0
) -> float:
    """Solve the YTM of a bullet bond (annual coupons) by bisection.

    price: clean price per 100 face; coupon: annual rate as decimal.
    """
    lo, hi = -0.99, 1.0

    def pv(y: float) -> float:
        return sum(
            coupon * face / (1 + y) ** t for t in range(1, int(tenor_years) + 1)
        ) + face / (1 + y) ** tenor_years

    for _ in range(200):
        mid = (lo + hi) / 2
        if pv(mid) > price:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def equivalent_vanilla_coupon(
    terms: RhinoBondTerms,
    expected_success_payment: float,
    vanilla_yield: float,
) -> float:
    """Coupon that makes a vanilla bullet bond (priced at par with this coupon
    equal to vanilla_yield) economically equivalent to the WCB's expected
    compensation (issue discount + expected success payment).
    """
    # WCB expected total compensation per $1,000 at maturity:
    # redemption + E[success] - issue price = 1000*(1 + y)^T  (vanilla total value)
    expected_total = 1_000.0 + expected_success_payment
    issue = terms.issue_price * 1_000.0
    # annualized compound return implied by the WCB's expected payoff
    implied_annual = (expected_total / issue) ** (1 / terms.tenor_years) - 1
    # The vanilla equivalent: coupon bond at price=issue with YTM=implied_annual
    # coupon c such that PV(c, y=implied_annual) = issue/10 (per 100 face)
    price_per_100 = (issue / 1_000.0) * 100.0
    lo, hi = 0.0, 0.5
    for _ in range(200):
        mid = (lo + hi) / 2
        pv = sum(
            mid * 100 / (1 + implied_annual) ** t
            for t in range(1, int(terms.tenor_years) + 1)
        ) + 100 / (1 + implied_annual) ** terms.tenor_years
        if pv < price_per_100:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2
