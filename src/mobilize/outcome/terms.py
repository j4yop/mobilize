"""IBRD outcome bonds — deal terms and cash-flow models.

All terms from official World Bank press releases / Treasury Q&A documents
(public). The Wildlife Conservation Bond ("Rhino Bond") is the flagship and
the only one with a third-party donor success payment (GEF); the others use
outcome-linked coupon components funded by credit sales (ITMOs/CRUs/VCUs/
Plastic Credits) with offtake partners.

Structure taxonomy:
- "discount-linked":  zero coupon, issued at a discount, terminal success
                      payment (Rhino Bond), or capped variable coupons
                      (Vietnam ER Bond, issued at 97.38%).
- "par-linked":       issued at par, low fixed coupon + outcome-linked
                      variable coupon (Clean Cooking, Amazon, Plastic,
                      Spekboom).
- "capital-at-risk":  principal partially at risk on outcome (UNICEF bond).

Sources:
- Rhino Bond: worldbank.org press release 2022/03/23 (Wildlife Conservation Bond)
- Clean Cooking: press release 2025/12/05 + Treasury Q&A (KliK Foundation / ITMOs)
- Amazon Reforestation: press release 2024/08/13 + Q&A (Microsoft / CRUs via Mombak)
- Plastic Waste: press release 2024/01/24 + FAQ (Citi / Plastic Collective)
- Vietnam Emissions Reduction: press release 2023/02/14 + Q&A (Citi / VCUs)
- Spekboom Restoration: press release 2026/04/23 + Q&A (Amazon / CRUs via Imperative)
- UNICEF (CAR 129): press release 2021/03/04 (capital-at-risk note, donation-linked)
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


@dataclass(frozen=True)
class OutcomeBondTerms:
    """Generic IBRD outcome-bond terms (par, fixed + outcome-linked coupon).

    models the "par-linked" family: investors get a guaranteed low fixed
    coupon plus a variable outcome-linked coupon funded by credit sales.
    """

    key: str
    name: str
    size_usd: float
    tenor_years: float
    settlement: str
    maturity: str
    fixed_coupon: float  # annual guaranteed coupon (decimal)
    max_total_return: float  # maximum potential annualized return (decimal)
    outcome_unit: str  # e.g. "ITMOs", "CRUs", "VCUs", "Plastic Credits"
    outcome_payer: str  # offtake partner
    hedge_bank: str  # forward-flow agreement bank
    project_usd: float  # ~foregone coupon frontloaded to the project
    country: str
    theme: str
    issue_price: float = 1.0  # par
    # outcome-linked coupon economics (per $100,000 denomination unless noted)
    variable_cap_per_100k: float = 0.0  # cumulative ceiling of linked interest
    principal_protected: bool = True
    url: str = ""


@dataclass(frozen=True)
class DiscountLinkedTerms:
    """Discount-issued, variable-coupon outcome bond (Vietnam ER bond)."""

    key: str
    name: str
    size_usd: float
    issue_price: float  # < 1.0
    tenor_years: float
    settlement: str
    maturity: str
    fixed_coupon: float  # 0.0 for the Vietnam bond
    max_total_return: float
    outcome_unit: str
    outcome_payer: str
    hedge_bank: str
    project_usd: float
    country: str
    theme: str
    url: str = ""


@dataclass(frozen=True)
class CapitalAtRiskTerms:
    """Capital-at-risk outcome note (UNICEF bond CAR 129)."""

    key: str
    name: str
    size_usd: float
    tenor_years: float
    settlement: str
    maturity: str
    fixed_coupon: float
    principal_at_risk_share: float  # fraction of principal contingent on outcome
    outcome_unit: str
    outcome_payer: str
    country: str
    theme: str
    issue_price: float = 1.0
    url: str = ""


# ---------------------------------------------------------------------------
# Registry of all seven IBRD outcome bonds (terms from public sources; see
# module docstring for per-bond citations).
# ---------------------------------------------------------------------------

RHINO_BOND = RhinoBondTerms()

CLEAN_COOKING = OutcomeBondTerms(
    key="clean_cooking",
    name="Clean Cooking Outcome Bond",
    size_usd=200_000_000.0,
    tenor_years=6.3,  # Dec 12 2025 -> Mar 31 2032 ("long 6-year")
    settlement="2025-12-12",
    maturity="2032-03-31",
    fixed_coupon=0.01093,
    max_total_return=0.04282,
    outcome_unit="ITMOs (Art. 6.2)",
    outcome_payer="KliK Foundation (Switzerland)",
    hedge_bank="Standard Chartered",
    project_usd=30_500_000.0,  # foregone coupon frontloaded to UpEnergy
    country="Ghana",
    theme="Clean cooking access (415k devices, 1.3m people)",
    url="https://www.worldbank.org/en/news/press-release/2025/12/05/world-bank-s-new-outcome-bond-supports-clean-cooking-initiative-in-ghana",
)

AMAZON_REFORESTATION = OutcomeBondTerms(
    key="amazon_reforestation",
    name="Amazon Reforestation-Linked Bond",
    size_usd=225_000_000.0,
    tenor_years=9.0,  # Aug 20 2024 -> Jul 31 2033
    settlement="2024-08-20",
    maturity="2033-07-31",
    fixed_coupon=0.01745,
    max_total_return=0.04362,
    outcome_unit="Carbon Removal Units (CRUs)",
    outcome_payer="Microsoft (via Mombak)",
    hedge_bank="HSBC",
    project_usd=36_000_000.0,  # foregone coupon to Mombak reforestation
    country="Brazil",
    theme="Amazon reforestation with native species",
    url="https://www.worldbank.org/en/news/press-release/2024/08/13/investors-support-amazon-reforestation-through-record-breaking-usd-225-million-world-bank-outcome-bond",
)

PLASTIC_WASTE = OutcomeBondTerms(
    key="plastic_waste",
    name="Plastic Waste Reduction-Linked Bond",
    size_usd=100_000_000.0,
    tenor_years=7.0,  # Jan 31 2024 -> Jan 31 2031
    settlement="2024-01-31",
    maturity="2031-01-31",
    fixed_coupon=0.0175,
    max_total_return=0.0375,  # ~$20m linked interest over $100m / 7y approx.
    outcome_unit="Plastic Credits + VCUs (Verra)",
    outcome_payer="Citi & Plastic Collective",
    hedge_bank="Citi",
    project_usd=14_000_000.0,  # up-front financing mobilized
    variable_cap_per_100k=19_468.25 + 532.99,  # plastic-credit + VCU ceilings
    country="Ghana + Indonesia",
    theme="Plastic collection & recycling (~230k tons over 10y)",
    url="https://www.worldbank.org/en/news/press-release/2024/01/24/world-bank-s-new-outcome-bond-helps-communities-remove-and-recycle-plastic-waste",
)

SPEKBOOM = OutcomeBondTerms(
    key="spekboom",
    name="Spekboom Restoration Outcome Bond",
    size_usd=120_000_000.0,
    tenor_years=14.5,  # Apr 30 2026 -> Nov 2 2040 ("long 14-year")
    settlement="2026-04-30",
    maturity="2040-11-02",
    fixed_coupon=0.0241,
    max_total_return=0.05078,
    outcome_unit="CRUs (Verra VM0047 ARR)",
    outcome_payer="Amazon (via Imperative)",
    hedge_bank="BNP Paribas",
    project_usd=25_000_000.0,  # foregone coupon to Imperative
    country="South Africa",
    theme="Spekboom land restoration (50,000 ha, ~11,000 jobs)",
    url="https://www.worldbank.org/en/news/press-release/2026/04/23/world-bank-prices-14-year-spekboom-restoration-outcome-bond-in-south-africa",
)

VIETNAM_EMISSIONS = DiscountLinkedTerms(
    key="vietnam_emissions",
    name="Emissions Reduction-Linked Bond",
    size_usd=50_000_000.0,
    issue_price=0.9738,  # discount issue
    tenor_years=5.0,  # Feb 22 2023 -> Mar 31 2028
    settlement="2023-02-22",
    maturity="2028-03-31",
    fixed_coupon=0.0,  # no fixed coupon
    max_total_return=0.0484,
    outcome_unit="VCUs (Verra)",
    outcome_payer="Citi",
    hedge_bank="Citi",
    project_usd=0.0,  # coupons foregone & frontloaded via Citi FFA
    country="Vietnam",
    theme="Clean drinking water (300k purifiers, 2m children)",
    url="https://www.worldbank.org/en/news/press-release/2023/02/14/emission-reduction-linked-bond-helps-provide-clean-drinking-water-to-two-million-children-in-vietnam",
)

UNICEF_BOND = CapitalAtRiskTerms(
    key="unicef",
    name="UNICEF Bond (Capital-at-Risk Note 129)",
    size_usd=100_000_000.0,
    tenor_years=5.0,  # Mar 4 2021 -> Mar 4 2026
    settlement="2021-03-04",
    maturity="2026-03-04",
    fixed_coupon=0.01291,
    principal_at_risk_share=0.5,  # UNICEF tranche conditional on donations
    outcome_unit="Private donations (18 target countries)",
    outcome_payer="UNICEF",
    country="18 countries",
    theme="COVID-19 response & child resilience (front-loaded $50m)",
    url="https://www.worldbank.org/en/news/press-release/2021/03/04/world-bank-bond-expands-support-to-covid-19-resilience-through-the-united-nations-childrens-fund-unicef",
)

ALL_BONDS: dict[str, object] = {
    "rhino": RHINO_BOND,
    "clean_cooking": CLEAN_COOKING,
    "amazon_reforestation": AMAZON_REFORESTATION,
    "plastic_waste": PLASTIC_WASTE,
    "spekboom": SPEKBOOM,
    "vietnam_emissions": VIETNAM_EMISSIONS,
    "unicef": UNICEF_BOND,
}


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
