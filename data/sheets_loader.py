"""Load data from Google Sheets (public CSV export) with fallback to hardcoded data.

Google Sheets can be exported as CSV without authentication if the sheet
is shared as "Anyone with the link can view."

Export URL pattern:
  https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={TAB_NAME}

This module provides:
  - fetch_sheet_tab(): fetch a single tab as a DataFrame
  - load_sheets_config(): read the config file that maps data keys to sheet URLs
  - load_all_sheets(): fetch all configured tabs, returning a dict of DataFrames
"""
from __future__ import annotations

import json
import logging
from io import StringIO
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "sheets_config.json"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; EsplanadeApp/1.0)",
}


def _sheet_csv_url(spreadsheet_id: str, tab_name: str) -> str:
    """Build the public CSV export URL for a Google Sheet tab."""
    from urllib.parse import quote
    return (
        f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        f"/gviz/tq?tqx=out:csv&sheet={quote(tab_name)}"
    )


def fetch_sheet_tab(
    spreadsheet_id: str,
    tab_name: str,
    timeout: int = 10,
) -> pd.DataFrame | None:
    """Fetch a single Google Sheet tab as a DataFrame.

    Returns None if the fetch fails (network error, 403, etc.).
    """
    url = _sheet_csv_url(spreadsheet_id, tab_name)
    try:
        req = Request(url, headers=_HEADERS)
        with urlopen(req, timeout=timeout) as resp:
            csv_text = resp.read().decode("utf-8-sig")
        df = pd.read_csv(StringIO(csv_text))
        # Drop fully empty rows and columns
        df = df.dropna(how="all").dropna(axis=1, how="all")
        return df
    except Exception as exc:
        logger.warning("Failed to fetch sheet tab %s/%s: %s", spreadsheet_id, tab_name, exc)
        return None


def load_sheets_config() -> dict[str, Any]:
    """Load the sheets configuration file.

    Returns a dict like:
    {
        "spreadsheet_id": "1ABC...",
        "tabs": {
            "competitors_sy": {"tab": "SY Competitors", "venue": "Scotland Yard", "type": "competitors"},
            "social_sy": {"tab": "SY Social", "venue": "Scotland Yard", "type": "social"},
            ...
        }
    }
    """
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to load sheets config: %s", exc)
        return {}


def save_sheets_config(config: dict[str, Any]) -> None:
    """Save the sheets configuration."""
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")


@st.cache_data(ttl=300, show_spinner=False)
def _cached_fetch(spreadsheet_id: str, tab_name: str) -> pd.DataFrame | None:
    """Cached version of fetch_sheet_tab (5-minute TTL)."""
    return fetch_sheet_tab(spreadsheet_id, tab_name)


def load_all_sheets(config: dict[str, Any] | None = None) -> dict[str, pd.DataFrame]:
    """Fetch all configured sheet tabs.

    Returns a dict keyed by the config key (e.g. "competitors_sy") with DataFrame values.
    Skips any tab that fails to load.
    """
    if config is None:
        config = load_sheets_config()
    if not config:
        return {}

    spreadsheet_id = config.get("spreadsheet_id", "")
    if not spreadsheet_id:
        return {}

    results = {}
    for key, tab_config in config.get("tabs", {}).items():
        tab_name = tab_config.get("tab", "")
        if not tab_name:
            continue
        df = _cached_fetch(spreadsheet_id, tab_name)
        if df is not None and not df.empty:
            results[key] = df

    return results


def setup_default_config(spreadsheet_id: str) -> dict[str, Any]:
    """Create a default config for a new spreadsheet.

    Assumes the spreadsheet has tabs named after venues/data types.
    """
    config = {
        "spreadsheet_id": spreadsheet_id,
        "tabs": {
            "competitors_sy": {"tab": "SY Competitors", "venue": "Scotland Yard", "type": "competitors"},
            "competitors_bc": {"tab": "BC Competitors", "venue": "Bar Cathedral", "type": "competitors"},
            "competitors_dolly": {"tab": "Dolly Competitors", "venue": "Dolly's", "type": "competitors"},
            "competitors_osf": {"tab": "OSF Competitors", "venue": "Old Spaghetti Factory", "type": "competitors"},
            "competitors_eloise": {"tab": "Eloise Competitors", "venue": "Eloise", "type": "competitors"},
            "competitors_barcart": {"tab": "Bar Cart Competitors", "venue": "Bar Cart", "type": "competitors"},
            "social_sy": {"tab": "SY Social", "venue": "Scotland Yard", "type": "social"},
            "social_dolly": {"tab": "Dolly Social", "venue": "Dolly's", "type": "social"},
            "social_osf": {"tab": "OSF Social", "venue": "Old Spaghetti Factory", "type": "social"},
            "pricing": {"tab": "Pricing", "venue": "all", "type": "pricing"},
            "local_search": {"tab": "Local Search", "venue": "all", "type": "local_search"},
        },
    }
    save_sheets_config(config)
    return config
