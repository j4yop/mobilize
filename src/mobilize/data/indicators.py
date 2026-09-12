"""Indicator universe for the sovereign ESG panel.

Sources: World Bank Open Data API (api.worldbank.org) and FRED (fredgraph.csv).
All indicators are free and keyless.

ESG pillar mapping follows the World Bank Sovereign ESG Data Framework
methodology: Environmental, Social, Governance pillars plus macro controls.
"""

# Countries: fixed universe of 35 (frozen after M1 sign-off).
# Mix of DM (for curve proxies) and EM across regions.
COUNTRIES: dict[str, str] = {
    "USA": "United States",
    "CAN": "Canada",
    "GBR": "United Kingdom",
    "DEU": "Germany",
    "FRA": "France",
    "ITA": "Italy",
    "ESP": "Spain",
    "NLD": "Netherlands",
    "SWE": "Sweden",
    "CHE": "Switzerland",
    "JPN": "Japan",
    "AUS": "Australia",
    "KOR": "Korea, Rep.",
    "CHN": "China",
    "IND": "India",
    "IDN": "Indonesia",
    "THA": "Thailand",
    "MYS": "Malaysia",
    "PHL": "Philippines",
    "VNM": "Vietnam",
    "ZAF": "South Africa",
    "EGY": "Egypt, Arab Rep.",
    "NGA": "Nigeria",
    "KEN": "Kenya",
    "MAR": "Morocco",
    "BRA": "Brazil",
    "MEX": "Mexico",
    "CHL": "Chile",
    "COL": "Colombia",
    "PER": "Peru",
    "ARG": "Argentina",
    "POL": "Poland",
    "CZE": "Czechia",
    "HUN": "Hungary",
    "TUR": "Turkiye",
}

# Indicator definitions. higher_is_better is applied AFTER inversion flags:
#   direction=+1  -> raw value used (higher = better)
#   direction=-1  -> value inverted (higher raw = worse, e.g. emissions)
INDICATORS: dict[str, dict] = {
    # ---- Environmental ----
    "EN.GHG.CO2.PC.CE.AR5": {
        "pillar": "E",
        "name": "CO2 emissions per capita (AR5)",
        "direction": -1,
    },
    "EG.FEC.RNEW.ZS": {
        "pillar": "E",
        "name": "Renewable energy consumption (% of final energy)",
        "direction": +1,
    },
    "NY.ADJ.DRES.GN.ZS": {
        "pillar": "E",
        "name": "Natural resource depletion (% of GNI)",
        "direction": -1,
    },
    "EN.ATM.PM25.MC.M3": {
        "pillar": "E",
        "name": "PM2.5 air pollution, mean annual exposure (ug/m3)",
        "direction": -1,
    },
    "ER.H2O.FWTL.ZS": {
        "pillar": "E",
        "name": "Annual freshwater withdrawals (% of internal resources)",
        "direction": -1,
    },
    # ---- Social ----
    "SP.DYN.LE00.IN": {
        "pillar": "S",
        "name": "Life expectancy at birth (years)",
        "direction": +1,
    },
    "SE.ENR.PRSC.FM.ZS": {
        "pillar": "S",
        "name": "School enrollment, primary and secondary (gross %)",
        "direction": +1,
    },
    "SH.STA.MMRT": {
        "pillar": "S",
        "name": "Maternal mortality ratio (per 100,000 live births)",
        "direction": -1,
    },
    "SI.POV.GINI": {
        "pillar": "S",
        "name": "Gini index",
        "direction": -1,
    },
    "SH.H2O.BASW.ZS": {
        "pillar": "S",
        "name": "People using basic drinking water services (%)",
        "direction": +1,
    },
    # ---- Governance (WGI, via WDI source) ----
    "GOV_WGI_PV_EST": {"pillar": "G", "name": "WGI: Political Stability", "direction": +1},
    "GOV_WGI_GE_EST": {"pillar": "G", "name": "WGI: Government Effectiveness", "direction": +1},
    "GOV_WGI_RQ_EST": {"pillar": "G", "name": "WGI: Regulatory Quality", "direction": +1},
    "GOV_WGI_RL_EST": {"pillar": "G", "name": "WGI: Rule of Law", "direction": +1},
    "GOV_WGI_CC_EST": {"pillar": "G", "name": "WGI: Control of Corruption", "direction": +1},
    "GOV_WGI_VA_EST": {"pillar": "G", "name": "WGI: Voice and Accountability", "direction": +1},
    # ---- Macro controls (not scored; used in M2 backtest layer) ----
    "NY.GDP.MKTP.KD.ZG": {
        "pillar": "MACRO",
        "name": "GDP growth (annual %)",
        "direction": 0,
    },
    "GC.DOD.TOTL.GD.ZS": {
        "pillar": "MACRO",
        "name": "Central government debt (% of GDP)",
        "direction": 0,
    },
    "FP.CPI.TOTL.ZG": {
        "pillar": "MACRO",
        "name": "Inflation, consumer prices (annual %)",
        "direction": 0,
    },
    "FI.RES.TOTL.CD": {
        "pillar": "MACRO",
        "name": "Total reserves (current US$)",
        "direction": 0,
    },
    "NY.GDP.MKTP.CD": {
        "pillar": "MACRO",
        "name": "GDP (current US$)",
        "direction": 0,
    },
}

PILLARS: tuple[str, ...] = ("E", "S", "G")

# FRED series for the US curve / bond-return proxy layer (M2/M4).
FRED_CURVE_SERIES: dict[str, str] = {
    "1Y": "DGS1",
    "2Y": "DGS2",
    "3Y": "DGS3",
    "5Y": "DGS5",
    "7Y": "DGS7",
    "10Y": "DGS10",
    "20Y": "DGS20",
}

# Backtest window: scores are observable at the END of year t-1 and drive
# weights held through year t. Panel starts one year earlier so the first
# rebalance (for FY2013) can use Dec-2012 data without look-ahead.
PANEL_START_YEAR: int = 2012
START_YEAR: int = 2013
END_YEAR: int = 2024

# Portfolio construction parameters.
REBALANCE_MONTH: int = 12  # scores observed at end of December
EXCLUDED_BOTTOM_PCT: float = 0.20  # screened portfolio drops bottom quintile
TILT_POWER: float = 2.0  # weight ∝ score^TILT_POWER in the tilted portfolio

# Bond-return proxy parameters.
# All yield series are ~10-year benchmark tenor (US: DGS10; OECD series are
# long-term/10y-equivalent), so the portfolio duration matches that tenor.
PROXY_DURATION: float = 8.0  # modified duration of the ~10Y proxy sovereign portfolio
RF_ANNUAL: float = 0.02  # risk-free rate for Sharpe/Sortino (conservative USD T-bill proxy)
