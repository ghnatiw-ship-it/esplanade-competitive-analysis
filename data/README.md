# Shared Research Data

This folder is the source of truth for research that is used in more than one app view.

## Current authority

- `bar_cart_deep_dive.json`
  - Authoritative Bar Cart competitive dataset
  - Used by:
    - `../streamlit_app.py`
    - `/Users/grahamhnatiw/Local/bar_cart_competitor_dashboard.py`

## Collaboration rule

If Claude or Codex updates Bar Cart competitor research, update `bar_cart_deep_dive.json` first.
Do not patch the same facts separately in multiple app files.
