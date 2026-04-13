from pathlib import Path
from typing import Optional
import math
import numpy as np

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from charts import (
    pricing_bar_chart, pricing_scatter,
    social_scatter, social_followers_bar, social_platform_heatmap,
    portfolio_stacked_bar,
    teardown_radar, teardown_sidebyside_bar,
    osf_menu_grouped_bar,
)

from data.portfolio_data import (
    BC_SOCIAL_AUDIT,
    COMPETITOR_PRICING,
    COMPETITORS,
    DOLLY_BACHELORETTE_MARKETING,
    DOLLY_BACHELORETTE_BENCHMARK,
    DOLLY_BACHELORETTE_PACKAGES,
    DOLLY_FEMALE_SAFETY_FRAMEWORK,
    DOLLY_LAUNCH_FRAMEWORK,
    DOLLY_OFF_PEAK_BENCHMARK,
    DOLLY_OFF_PEAK_FRAMEWORK,
    DOLLY_OFF_PEAK_KPIS,
    DOLLY_SOCIAL_AUDIT,
    DOLLY_SOCIAL_HANDLES,
    ELOISE_AWARD_COMPETITION,
    ELOISE_DEMAND_AUDIT,
    ELOISE_DEMAND_SOURCES,
    ELOISE_SOCIAL_AUDIT,
    LOCAL_SEARCH_AUDIT,
    LOCAL_SEARCH_KEYWORDS,
    OSF_SOCIAL_AUDIT,
    OSF_MENU_ANALYSIS,
    OSF_MENU_ANALYSIS_SOURCES,
    RESEARCH_CATEGORY_COLUMNS,
    SY_SOCIAL_AUDIT,
    TIER_LABELS,
    VENUES,
    VENUE_RECOMMENDATIONS,
    load_bar_cart_deep_dive,
    load_venue_research_tables,
)

st.set_page_config(
    page_title="Esplanade Restaurants — Competitive Analysis",
    page_icon="🍽️",
    layout="wide",
)

# --- GLOBAL TABLE STYLE ---

_OUR_VENUES = {"Scotland Yard", "Bar Cart", "Bar Cathedral", "Eloise", "Dolly's", "Old Spaghetti Factory"}

_TABLE_CSS = (
    '<style>'
    '.wt { width:100%; border-collapse:collapse; font-size:14px; color:#111827; background:#ffffff; }'
    '.wt th,.wt td { text-align:left; padding:8px 10px; border-bottom:1px solid #e0e0e0;'
    ' white-space:normal; word-wrap:break-word; color:#111827; background:#ffffff; }'
    '.wt th { background:#f5f5f5; color:#111827; font-weight:600; position:sticky; top:0; z-index:1; }'
    '.wt tr:hover td { background:#fafafa; }'
    '.wt tr.venue-highlight td { font-weight:700; background:#e8f5e9; }'
    '@media (max-width: 768px) { .wt { font-size:12px; } .wt th,.wt td { padding:6px 8px; } .wt th { position:static; } }'
    '</style>'
)

_INTEGER_LIKE_COLUMNS = {
    "Google Reviews",
    "IG Followers",
    "Total Posts",
    "Action Count",
}


def _format_table_cell(column_name, value):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    if column_name in _INTEGER_LIKE_COLUMNS:
        numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
        if pd.notna(numeric):
            return f"{int(numeric):,}"
    return str(value)


def show_table(df, max_height=None, highlight_venues=False):
    """Render a DataFrame as an HTML table with text wrapping.
    If highlight_venues=True, bold-highlight rows where the Name column matches one of our venues.
    """
    row_label_column = next((col for col in ["Name", "Bar"] if col in df.columns), None)
    should_highlight_venues = highlight_venues or (
        row_label_column is not None
        and df[row_label_column].astype(str).isin(_OUR_VENUES).any()
    )

    if should_highlight_venues and row_label_column:
        # Build HTML manually to add class to our venue rows
        cols = list(df.columns)
        header = "".join(f"<th>{c}</th>" for c in cols)
        rows_html = ""
        for _, row in df.iterrows():
            row_label = str(row.get(row_label_column, ""))
            cls = ' class="venue-highlight"' if row_label in _OUR_VENUES else ""
            cells = "".join(f"<td>{_format_table_cell(c, row[c])}</td>" for c in cols)
            rows_html += f"<tr{cls}>{cells}</tr>"
        html = f'<table class="wt"><thead><tr>{header}</tr></thead><tbody>{rows_html}</tbody></table>'
    else:
        display_df = df.copy()
        for column in display_df.columns:
            if column in _INTEGER_LIKE_COLUMNS:
                display_df[column] = display_df[column].map(lambda value: _format_table_cell(column, value))
        html = display_df.to_html(index=False, escape=True, classes="wt")
    wrapper = f'<div style="max-height:{max_height}px;overflow-y:auto;">{html}</div>' if max_height else html
    st.markdown(_TABLE_CSS + wrapper, unsafe_allow_html=True)


def _split_menu_entry(value):
    text = str(value).strip()
    if not text:
        return "", ""
    if "exact current price varies" in text.lower() or "not verified" in text.lower():
        return "Varies / n/a", text
    if "not currently listed" in text.lower() or "no " in text.lower():
        return "n/a", text

    name_part, sep, remainder = text.partition(" — ")
    if sep:
        price_part, semi, desc_part = remainder.partition("; ")
        if semi:
            return price_part.strip(), f"{name_part.strip()}; {desc_part.strip()}".strip()
        return price_part.strip(), name_part.strip()
    return "", text


def build_osf_menu_display_table(df):
    brands = ["Old Spaghetti Factory", "Scaddabush", "East Side Mario's", "Olive Garden"]
    rows = []
    for _, row in df.iterrows():
        display_row = {("Item", ""): row["Item"]}
        for brand in brands:
            price, description = _split_menu_entry(row[brand])
            display_row[(brand, "Price")] = price
            display_row[(brand, "Description")] = description
        rows.append(display_row)
    display_df = pd.DataFrame(rows)
    display_df.columns = pd.MultiIndex.from_tuples(display_df.columns)
    return display_df


def _format_optional_metric(value):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "n/a"
    if isinstance(value, (int, np.integer)):
        return f"{value:,}"
    if isinstance(value, float):
        return f"{int(value):,}" if value.is_integer() else f"{value:.1f}"
    return str(value)


BASE_PATH = Path(__file__).parent
ASSETS_PATH = BASE_PATH / "assets" / "logos"
ELOISE_DOCS_PATH = BASE_PATH / "assets" / "docs" / "eloise"
BAR_CART_DATA, BAR_CART_SNAPSHOT, BAR_CART_COMPETITOR_AUDIT, BAR_CART_PROGRAMMING, BAR_CART_RECOMMENDATIONS = load_bar_cart_deep_dive(BASE_PATH)
VENUE_RESEARCH_TABLES = load_venue_research_tables(BASE_PATH)


def _slugify(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_")


def find_logo(name: str) -> Optional[Path]:
    """Return the first matching logo file for a brand or venue."""
    if not ASSETS_PATH.exists():
        return None

    slug = _slugify(name)
    if slug == "scotland_yard":
        preferred = ASSETS_PATH / "scotland_yard.png"
        if preferred.exists():
            return preferred

    candidates = []
    for ext in ("png", "jpg", "jpeg", "svg", "webp"):
        candidates.extend(
            [
                ASSETS_PATH / f"{slug}.{ext}",
                ASSETS_PATH / f"{slug}_logo.{ext}",
                ASSETS_PATH / f"logo_{slug}.{ext}",
            ]
        )

    for path in candidates:
        if path.exists():
            return path

    for path in ASSETS_PATH.iterdir():
        if path.is_file() and slug in _slugify(path.stem):
            return path

    return None


def render_brand_header():
    st.title("Competitive Analysis")
    st.caption("Esplanade Restaurants Group — The Esplanade, Toronto")
    st.caption("Source: Google Drive competitor research + web research (April 2026)")


def render_venue_logo(venue_name: str):
    logo_path = find_logo(venue_name)
    if logo_path:
        st.image(str(logo_path), width=220)


def render_takeout_gallery(df: pd.DataFrame):
    if df.empty:
        st.info("No verified guest-shot packaged-arrival photos are loaded yet for this venue.")
        return
    grouped = df.groupby("Item Group", sort=False)
    for item_group, group_df in grouped:
        st.markdown(f"### {item_group}")
        cols = st.columns(min(2, max(1, len(group_df))))
        for idx, (_, row) in enumerate(group_df.iterrows()):
            with cols[idx % len(cols)]:
                st.markdown(f"**{row['Competitor']}**")
                st.caption(row["Comparable Item"])
                photo_asset = str(row.get("Photo Asset URL", "") or "").strip()
                if photo_asset:
                    st.image(photo_asset, use_container_width=True)
                else:
                    st.warning("No verified packaged-arrival photo loaded yet.")
                st.markdown(f"**Package Type:** {row['Package Type']}")
                st.markdown(f"**Evidence:** {row['Evidence']}")
                st.markdown(f"[Evidence Source]({row['Evidence URL']})")
                st.markdown(f"[Photo Source]({row['Photo URL']})")
                st.caption(row["Read"])
        st.divider()


def render_download_buttons(file_specs, columns=2):
    cols = st.columns(columns)
    for idx, (label, path) in enumerate(file_specs):
        with cols[idx % columns]:
            file_path = Path(path)
            if file_path.exists():
                suffix = file_path.suffix.lower()
                mime = "application/octet-stream"
                if suffix == ".pdf":
                    mime = "application/pdf"
                elif suffix == ".md":
                    mime = "text/markdown"
                elif suffix == ".txt":
                    mime = "text/plain"
                st.download_button(
                    label=label,
                    data=file_path.read_bytes(),
                    file_name=file_path.name,
                    mime=mime,
                    width="stretch",
                )
            else:
                st.caption(f"Missing: {file_path.name}")

# --- SY TEARDOWN DATA ---

SY_TEARDOWNS = {
    "Score on King": {
        "address": "107 King St E, Toronto, ON M5C 1G6",
        "neighbourhood": "St. Lawrence / Downtown Core",
        "parent": "Score Hospitality Group; Toronto operates Score on King and Score on Queen",
        "founded": "2019 in Toronto; now expanded to a second Toronto location, Score on Queen",
        "website": "scoreonking.com and scoreonqueen.com",
        "positioning": "High-energy multi-location sports-bar brand built around Caesar culture, game-day occasions, and group dining",
        "screenshot": "https://cloud.inference.sh/app/files/t/2pcvdb1k/cu8lxt43.png",
        "google_rating": 4.4, "google_reviews": 1621,
        "yelp_rating": 3.8, "yelp_reviews": 74,
        "ig_handle": "@scoreonking", "ig_followers": 10000, "ig_posts": 572,
        "platforms": "IG, FB, TikTok", "posts_per_week": "~1.6",
        "menus": ["All Day", "Drinks", "Caesars", "Late Night", "Happy Hour", "Weekend Brunch", "Kids"],
        "signature_items": [
            "Caesar Towers — over-the-top cocktails piled with food. Voted #1 Caesar bar in Toronto.",
            "30 taps on draft",
            "Pulled pork, birria tacos, mac & cheese — comfort food focus",
        ],
        "review_strengths": [
            "Caesar towers — 'the best Caesars are found here'",
            "Fun, energetic vibe — brought a portable TV for a customer's team",
            "Great for groups and sports nights",
            "Pulled pork 'melted in our mouths'",
            "Patio on Church St",
        ],
        "review_weaknesses": [
            "Noise and crowd levels during peak",
            "Wait times and seating during busy periods",
            "Food quality variability on smaller plates/appetizers",
            "Alcohol/spirit pricing can feel expensive",
        ],
        "swot": {
            "strengths": ["Signature Caesar towers (viral, shareable)", "Strong social media (10K IG, TikTok active)", "Multi-menu strategy (brunch, late night, kids)", "Energetic atmosphere, great for groups", "Toronto proof of concept validated by second location"],
            "weaknesses": ["Yelp rating only 3.8", "Food quality inconsistency on some items", "Noise/crowd complaints", "Higher price point", "Brand identity still leans heavily on one hero product"],
            "opportunities": ["Caesar content continues to go viral", "Cross-promote between King and Queen locations", "Expand brunch/kids to capture family market", "Partnerships with sports leagues/teams"],
            "threats": ["New sports bars entering downtown market", "If Caesar trend fades, brand identity weakens", "Rising food costs", "Multi-location operating complexity can pressure consistency"],
        },
        "learns": [
            "Signature item strategy — entire brand built around one viral product",
            "Multi-location rollout — once a bar format works, duplicate it in a second neighborhood",
            "Menu segmentation — 7 menus vs SY's 1 captures more occasions",
            "Social-first mentality — every dish designed to be photographed",
            "Email capture on homepage — SY has no email marketing",
            "TikTok presence — SY is not on TikTok",
        ],
        "advantages": [
            "Google reviews: 4.7 vs 4.4, and 4,109 vs 1,621",
            "Heritage: 45 years vs 5 years — can't be replicated",
            "Football authenticity — SY is the real soccer pub",
            "Value: Yard Sale specials vs Score's higher pricing",
            "Consistency: Score gets mixed reviews; SY is 'reliable'",
        ],
    },
    "House on Parliament": {
        "address": "454 Parliament Street, Toronto, ON M5A 3A2",
        "neighbourhood": "Cabbagetown",
        "parent": "Family-owned (co-owners Tania & Beau)",
        "founded": "~2004–2005 (20+ years)",
        "website": "houseonparliament.com (WordPress)",
        "positioning": "Neighbourhood gastropub — 'Purveyors of Fine Fare, Liberation, + Diversion'",
        "screenshot": "https://cloud.inference.sh/app/files/t/2pcvdb1k/jifjcrbg.png",
        "google_rating": 4.7, "google_reviews": 3004,
        "yelp_rating": 4.1, "yelp_reviews": 346,
        "ig_handle": "@hop_to", "ig_followers": 5185, "ig_posts": 897,
        "platforms": "IG, FB, Twitter/X", "posts_per_week": "~1.7",
        "menus": ["Daily Fare", "Weekend Brunch", "Sweets", "Beers & Ciders", "Wines", "Fancy Drinks", "Whiskey Et Al"],
        "signature_items": [
            "Scotch Eggs — wild boar, pheasant & cognac. #1 talked-about item.",
            "Sticky Toffee Pudding / Banoffee — 'most amazing cake I've ever had'",
            "Steak & Wild Mushroom Pie — elevated comfort food",
            "Galbi Ribs & Kimchi Frites — Korean-style short ribs ($35)",
            "Named cocktails: Idiocracy, The Charlottina, Smoked Jalapeño Margarita",
        ],
        "review_strengths": [
            "'One of the best meals I had in Toronto'",
            "'The Unofficial Living Room of My Life' — deep emotional connection",
            "Scotch Eggs are the #1 talked-about item",
            "Warm, cozy, familiar atmosphere — 'feels like home'",
            "Locally sourced meat (Wellington County)",
            "Open 365 days/year including holidays",
            "Rooftop patio is a summer draw",
            "Staff knowledgeable about beer and whiskey",
        ],
        "review_weaknesses": [
            "'Service was horrible, cold, unattentive' — occasional inconsistency",
            "No reservations — can mean waits during peak",
            "Unclaimed on Yelp — not managing online reputation",
            "WordPress site — functional but not modern",
        ],
        "swot": {
            "strengths": ["Highest Google rating (4.7, tied with SY)", "Deep community loyalty — 20+ years", "Elevated gastropub menu with rotating daily specials", "Open 365 days/year", "7 separate curated menus", "Strong cocktail program ('Fancy Drinks')", "Family-owned — authentic"],
            "weaknesses": ["No reservations — loses planned occasions", "Unclaimed on Yelp", "Service inconsistency", "No email marketing or loyalty program", "Cabbagetown limits downtown foot traffic"],
            "opportunities": ["Claim Yelp listing", "Launch email newsletter", "Add reservation system for off-peak", "Instagram growth potential"],
            "threats": ["New gastropubs entering market", "Rising food costs (locally sourced)", "Staff turnover", "Competitors with stronger digital presence"],
        },
        "learns": [
            "Daily rotating specials updated on website — creates repeat visits",
            "Signature hero dishes people tell friends about (Scotch Eggs, Sticky Toffee Pudding)",
            "Menu segmentation — 7 pages vs 1 signals depth and expertise",
            "Emotional connection — reviews call it 'living room of my life'",
            "No reservations framed as hospitality: 'we don't want anyone pressured to leave'",
        ],
        "advantages": [
            "Location: Esplanade is downtown + near venues. Cabbagetown is residential.",
            "Sports identity: SY owns the football occasion. HoP doesn't do sports.",
            "Reservations: SY accepts them; HoP doesn't.",
            "Heritage: 45 years vs 20 — more history to tell.",
            "Value: Yard Sale specials vs HoP's $35 galbi ribs.",
        ],
    },
    "Fox on John": {
        "address": "106 John St, Toronto, ON M5V 2E1",
        "neighbourhood": "Entertainment District / King West",
        "parent": "Independent",
        "founded": "~2019",
        "website": "foxonjohn.ca (Squarespace)",
        "positioning": "'A Modern English Restaurant' — all-day venue 9am–2am, 22 separate menus",
        "screenshot": "https://cloud.inference.sh/app/files/t/2pcvdb1k/zn6btnxr.png",
        "google_rating": 4.6, "google_reviews": 5500,
        "yelp_rating": 3.5, "yelp_reviews": 246,
        "ig_handle": "@foxonjohn", "ig_followers": 19000, "ig_posts": 1685,
        "platforms": "IG, FB, TikTok, Twitter", "posts_per_week": "~3.6",
        "menus": ["Bottomless Brunch ($59.95)", "Brunch", "Food", "Dessert", "Kids", "Daily Specials", "TGIT Thursdays", "Lunch Prix-Fixe", "Express Lunch", "After D9rk (late night)", "Heaven Til 7 Happy Hour", "Drinks", "Signature Cocktails", "Beer", "Wine", "Spirits", "Mocktails", "Bottle Service", "Gluten-Free", "Vegetarian", "Vegan", "Group Activities"],
        "signature_items": [
            "Bottomless Brunch at $59.95 — all-inclusive, massive social media driver",
            "CN Tower patio views — #1 mentioned feature in reviews",
            "Signature cocktail program with dedicated menu",
            "After D9rk late-night menu (9pm–close)",
            "Bottle service — nightclub-style upsell unusual for a pub",
            "Jan 2026: all menu items capped at $20.26 (aggressive promo)",
        ],
        "review_strengths": [
            "CN Tower patio views — #1 feature",
            "Bottomless brunch extremely popular and social-media-friendly",
            "Cocktails consistently praised",
            "Staff described as friendly and attentive",
            "Entertainment (magicians, DJs) on event nights",
            "Location convenience — near Entertainment District venues",
            "Large, spacious venue with multiple areas",
        ],
        "review_weaknesses": [
            "'Too noisy for conversation' — common peak-hour complaint",
            "Food quality 'hit or miss' — inconsistency noted",
            "Yelp 3.5 vs Google 4.6 — polarizing",
            "Some dishes described as salty",
            "Long wait times during peak brunch",
            "Magician entertainment not appreciated by all",
        ],
        "swot": {
            "strengths": ["Strongest social media in SY comp set (19K IG, 4 platforms)", "22 menus capturing every occasion", "CN Tower patio views (unique asset)", "All-day 9am–2am operation", "Bottomless brunch drives massive traffic", "Online ordering, gift cards, catering, email capture"],
            "weaknesses": ["Yelp only 3.5 — polarizing reviews", "Food quality inconsistency noted", "Noise complaints during peak", "Higher price point than traditional pubs", "'Modern English' positioning is vague", "TripAdvisor only 3.4"],
            "opportunities": ["Aggressive promo strategy shows willingness to compete", "Catering + private events = B2B revenue SY doesn't have", "Entertainment programming differentiates", "Blog + email = owned marketing channel"],
            "threats": ["Yelp/TripAdvisor gap could erode trust", "Over-extension risk — 22 menus may dilute quality", "New venues in Entertainment District", "Dependence on brunch traffic"],
        },
        "learns": [
            "Reign Company (professional hospitality marketing group) runs Fox's social — dedicated team, not just an owner posting. This is the #1 reason for the follower gap.",
            "Viral TikTok-first content strategy — comedic skits (fake burglary = 130K views) cross-pollinate to IG. SY match-day atmosphere is equally filmable but not being captured.",
            "Bottomless brunch ($59.95) is a built-in UGC engine — groups photograph and tag organically. SY needs its own 'must-photograph' moment.",
            "CN Tower patio = location-driven UGC magnet. SY can't replicate this, but could create its own visual hook.",
            "Promotional pricing stunts generate press — Jan 2026 all items capped at $20.26 got earned media. Marketing disguised as pricing.",
            "Menu segmentation principle — SY should add dedicated drinks, happy hour, brunch, kids menus at minimum",
            "Email capture, online ordering (Toast), gift cards, blog — digital infrastructure SY doesn't have",
        ],
        "advantages": [
            "Google rating: 4.7 vs 4.6 — SY more consistently well-reviewed",
            "Not polarizing — Fox's Yelp 3.5 / TripAdvisor 3.4 shows polarization. SY reviews are uniform.",
            "Heritage: 45 years vs ~5 — can't be bought",
            "Football/sports identity — Fox doesn't own any sports occasion",
            "Value pricing — Yard Sale vs $59.95 bottomless brunch",
            "Focus — SY knows what it is. Fox tries to be everything (22 menus may dilute).",
        ],
    },
    "Duke of Cornwall": {
        "address": "400 University Ave, Toronto, ON M5G 1S5",
        "neighbourhood": "Discovery District",
        "parent": "Duke Pubs (also Duke of York; Duke of Kent and Duke of Westminster CLOSED)",
        "founded": "~2018",
        "website": "dukepubs.ca (Squarespace)",
        "positioning": "'Brilliantly British' — weekday corporate pub, closed weekends",
        "screenshot": "",
        "google_rating": 4.2, "google_reviews": 791,
        "yelp_rating": 3.5, "yelp_reviews": 34,
        "ig_handle": "@duke_pubs", "ig_followers": 11000, "ig_posts": 430,
        "platforms": "IG, FB (Twitter dead)", "posts_per_week": "~1.0",
        "menus": ["Food Menu", "Drinks Menu"],
        "signature_items": [
            "Fish & Chips — classic British anchor",
            "Nachos ($18.99)",
            "Haggis Neeps & Tatties — British authenticity signal",
            "Sticky Toffee Pudding — praised dessert",
            "Pint + Fish & Chips combo $29.99 — value bundling",
        ],
        "review_strengths": [
            "Friendly service",
            "Good for group events/private rooms (195 capacity, St. Ives Room, Crantock Room)",
            "British atmosphere",
            "Sticky toffee pudding",
            "Draft selection",
            "Large patio",
        ],
        "review_weaknesses": [
            "Overpriced for portions",
            "Inconsistent food quality (chicken pot pie 'a bad joke')",
            "Cold food",
            "Slow service",
            "Closed weekends",
            "Shrinking brand (2 locations closed in past year)",
        ],
        "swot": {
            "strengths": ["Private event infrastructure (195 capacity, dedicated rooms)", "University Ave location (offices/hospitals)", "Delivery presence (DoorDash/Skip/Ritual)", "Wine promos (half-price before 4pm)"],
            "weaknesses": ["Closed weekends", "Shrinking brand (2 closures)", "Food consistency issues", "Low review volume", "No heritage (est. 2018)", "Diluted shared IG across locations"],
            "opportunities": ["Capture closed-location customers", "Corporate events in Discovery District", "Could open weekends"],
            "threats": ["Parent company financial stress", "Hybrid work reducing weekday traffic", "Stronger pubs with better reviews in market"],
        },
        "learns": [
            "Private event packaging with dedicated rooms and planner page",
            "Delivery platform presence (DoorDash, Skip, Ritual)",
            "Clear daily drink promos (half-price wine before 4pm)",
            "Email capture/newsletter",
            "PDF menu online for easy updates",
        ],
        "advantages": [
            "Heritage: 1978 vs 2018 — can't be replicated",
            "Google rating: 4.7 vs 4.2 — significantly stronger trust signal",
            "7-day operation vs weekday-only",
            "Brand stability vs contracting brand (2 closures)",
            "Dedicated IG account vs diluted shared handle",
            "5x review volume (4,109 vs 791)",
        ],
    },
    "The Auld Spot": {
        "address": "347 Danforth Ave, Toronto, ON M4K 1N7",
        "neighbourhood": "The Danforth / Riverdale",
        "parent": "Independent (turbulent — sold 2020 to 8590 Group, reopened 2022 under new management)",
        "founded": "1998",
        "website": "auldspotpub.ca",
        "positioning": "'Toronto's top pub on the Danforth' — gastropub with globally inspired scratch-made food",
        "screenshot": "",
        "google_rating": 4.5, "google_reviews": 1245,
        "yelp_rating": 3.75, "yelp_reviews": 95,
        "ig_handle": "@theauldspotpub", "ig_followers": 3157, "ig_posts": 0,
        "platforms": "IG, FB, Twitter/X", "posts_per_week": "~1.0",
        "menus": ["Food Menu", "Drinks Menu"],
        "signature_items": [
            "$1 Oyster Mondays — marquee category-defining weekly draw",
            "$1 Drummies",
            "Bacon Double Cheese Burger (grass-fed, sesame brioche, chipotle mayo) — #1 praised item",
            "Beer-battered haddock fish & chips",
            "Deep fried pork belly",
            "Mac and cheese",
        ],
        "review_strengths": [
            "Burgers — #1 praised item",
            "$1 Oyster Mondays — draws crowds",
            "Cozy, classy atmosphere",
            "Incredible fries",
            "Mac and cheese",
            "Craft beer curation",
            "Genuine neighbourhood feel",
            "Food quality above typical pub",
        ],
        "review_weaknesses": [
            "Pricing — #1 complaint ($20 burgers, $14-18 premium pints)",
            "Food poisoning incident December 2024",
            "Dark interior",
            "Inconsistent service",
            "Ownership turbulence still haunts reputation",
            "Food occasionally misses at the price point",
        ],
        "swot": {
            "strengths": ["$1 Oyster Monday (category-defining promotion)", "Scratch-made globally inspired food", "28-year institution (est. 1998)", "Larger social following than SY (3,157 vs 1,903)", "Good craft beer curation"],
            "weaknesses": ["Price perception problem", "Ownership instability (2 changes since 2020)", "Lower Google rating than SY (4.5 vs 4.7)", "Far fewer reviews than SY", "Food safety incident (Dec 2024)", "Dark interior", "No email capture"],
            "opportunities": ["Lean into oyster/seafood angle", "Brunch programming", "Patio potential", "Events/live music", "Delivery expansion"],
            "threats": ["Intense Danforth competition", "Price sensitivity among customers", "Food safety risk to reputation", "Gastropub category is crowded", "SY and others with stronger reviews"],
        },
        "learns": [
            "Create signature weekly draw like $1 Oyster Monday",
            "Elevate 1-2 menu items to 'famous' status (their burger is the #1 talked-about item)",
            "Food-forward social content drives IG growth",
            "Globally inspired menu language signals quality above typical pub",
        ],
        "advantages": [
            "Heritage: 1978 vs 1998 — nearly 30 more years of history",
            "Google rating: 4.7 vs 4.5",
            "3x review volume (4,109 vs 1,245)",
            "Sports identity — Auld Spot doesn't do sports",
            "Location: Esplanade higher traffic than Danforth",
            "Ownership stability — Auld Spot's ownership drama nearly killed them",
            "No price backlash — pricing is Auld Spot's #1 complaint",
        ],
    },
    "The Commoner Roncy": {
        "address": "2067 Dundas St W, Toronto, ON M6R 1W8",
        "neighbourhood": "Roncesvalles",
        "parent": "Independent",
        "founded": "Established Toronto neighbourhood restaurant and bar; active current Roncesvalles operation",
        "website": "thecommonerrestaurant.ca",
        "positioning": "Polished neighbourhood gastro-pub that blends comfort-food familiarity with a more date-night-capable room, stronger brunch pull, and a cleaner contemporary brand than a classic heritage pub.",
        "screenshot": None,
        "google_rating": 4.4, "google_reviews": 882,
        "yelp_rating": "n/a", "yelp_reviews": 0,
        "ig_handle": "@thecommonerrestaurant", "ig_followers": None, "ig_posts": None,
        "platforms": "IG, FB", "posts_per_week": "~2.0",
        "menus": ["Lunch", "Dinner", "Weekend Brunch", "Cocktails", "Craft Beer", "Wine", "Private Dining / Group Booking"],
        "signature_items": [
            "Bar Room Burger — the clearest menu anchor and a strong repeat-order pub item",
            "Weekend brunch and neighbourhood patio usage broaden demand beyond dinner-only pub traffic",
            "Craft beer plus classic cocktails gives it broader appeal than a beer-only pub lane",
        ],
        "review_strengths": [
            "Approachable but polished neighbourhood feel",
            "Strong fit for brunch, casual dinners, and date-adjacent local use",
            "Burger, truffle fries, and comfort-food staples repeatedly surface as draw items",
            "OpenTable sentiment is strong and group-friendly demand appears healthy",
        ],
        "review_weaknesses": [
            "Far less heritage and institutional identity than Scotland Yard",
            "Does not own a sports or football occasion",
            "Less downtown relevance for tourists, pre-game, or Esplanade foot traffic",
            "Social and review depth appear solid but not dominant at city scale",
        ],
        "swot": {
            "strengths": [
                "More polished contemporary room than a typical old-guard pub",
                "Brunch, cocktails, and neighbourhood-dinner flexibility broaden demand",
                "Strong OpenTable rating and booking activity for a single-location pub-adjacent restaurant",
                "Approachable upscale-pub positioning is easy to understand",
            ],
            "weaknesses": [
                "No deep heritage moat",
                "No sports identity or football-community ownership",
                "Roncesvalles is less strategically useful than the Esplanade for destination pub traffic",
                "Current public social metrics are harder to verify and appear less distinctive than top citywide pub brands",
            ],
            "opportunities": [
                "Deepen burger-and-brunch reputation into stronger citywide memory structures",
                "Use patio and neighbourhood identity to build local loyalty further",
                "Expand event and private-group packaging",
                "Turn polished room identity into more consistent social storytelling",
            ],
            "threats": [
                "Toronto has many polished neighbourhood gastro-pubs competing for the same guest",
                "If food execution softens, there is limited uniqueness to protect pricing",
                "Economic softness can hurt brunch and casual-premium frequency",
                "Destination pubs and sports bars can still outperform on occasion clarity",
            ],
        },
        "learns": [
            "A pub-adjacent restaurant can feel more current and polished without abandoning comfort-food familiarity.",
            "Brunch matters. The Commoner broadens demand by being useful at more than one daypart.",
            "Scotland Yard should study how a cleaner, more contemporary room can still feel approachable rather than formal.",
            "A strong burger-and-brunch reputation is a practical commercial asset, even without a giant entertainment hook.",
        ],
        "advantages": [
            "Scotland Yard has far more heritage and a stronger institutional identity.",
            "SY owns sports, football fandom, and game-day ritual in a way The Commoner does not.",
            "The Esplanade location gives SY stronger tourist, pre-event, and downtown convenience demand.",
            "SY has dramatically more Google-review volume and a stronger long-run trust signal.",
        ],
        "sources": [
            {"label": "The Commoner Roncy OpenTable", "url": "https://www.opentable.ca/r/the-commoner-roncy-toronto"},
            {"label": "The Commoner official site", "url": "https://www.thecommonerrestaurant.ca/"},
            {"label": "Hungry 416 profile", "url": "https://www.hungry416.com/best-brunch-in-toronto-by-neighbourhood/"},
        ],
    },
    "C'est What": {
        "address": "67 Front St E, Toronto, ON M5E 1B5",
        "neighbourhood": "St. Lawrence Market (same neighbourhood as SY — most direct local competitor)",
        "parent": "Independent, owner George Milbrandt since 1988 (38 years, has a Toronto parkette named after him)",
        "founded": "1988",
        "website": "cestwhat.com",
        "positioning": "'Toronto's original craft beer pub' — 'the granddaddy of craft beer bars' (NOW Toronto). 42 taps, all-Canadian.",
        "screenshot": "",
        "google_rating": 4.5, "google_reviews": 3400,
        "yelp_rating": 3.5, "yelp_reviews": 373,
        "ig_handle": "@cestwhatto", "ig_followers": 4006, "ig_posts": 500,
        "platforms": "IG, FB", "posts_per_week": "~1.1",
        "menus": ["Food Menu", "Beer List", "Whiskey List", "Group Booking Packages"],
        "signature_items": [
            "42 craft beer taps (8 on cask) — 100% Canadian/Ontario, ~300 different beers/year",
            "Bison Burger",
            "Curry, Pulled Pork, Poutine — comfort food anchors",
            "Board games & pool tables — non-drinking entertainment",
            "Live indie music programming",
            "Cask beer festivals — destination events",
        ],
        "review_strengths": [
            "Massive craft beer selection — #1 draw (42 taps, all-Canadian)",
            "Cozy underground atmosphere",
            "Board games increase dwell time",
            "Live music programming",
            "Strong community feel",
            "Consistent over decades",
            "#16 on TripAdvisor (drives tourist traffic)",
            "Knowledgeable staff",
            "Vegan/GF options",
        ],
        "review_weaknesses": [
            "Hard to find (basement entrance)",
            "Can feel dated/dark",
            "Food is 'good not great' compared to beer program",
            "Yelp only 3.5 (some service complaints)",
            "Limited capacity",
        ],
        "swot": {
            "strengths": ["42-tap all-Canadian craft beer program (unmatched)", "38-year heritage with original owner", "#16 TripAdvisor ranking", "Same neighbourhood as SY (captures shared foot traffic)", "Board games/entertainment for non-drinking occasions", "Group booking infrastructure with clear pricing", "Cask beer festivals (destination events)", "Vegan/GF accommodations"],
            "weaknesses": ["Basement location (poor discoverability)", "Food program secondary to beer", "Dated interior", "Lower IG following than potential", "No delivery presence", "Yelp rating only 3.5"],
            "opportunities": ["Could leverage TripAdvisor ranking for more tourist traffic", "Expand food program", "Modernize space", "Grow social media presence", "Email newsletter"],
            "threats": ["New craft beer bars eroding niche", "Rising costs", "Aging infrastructure", "SY and other pubs in same corridor"],
        },
        "learns": [
            "Expand craft beer rotation (42 taps is a magnet vs SY's standard selection)",
            "Add board games/non-sports entertainment for off-days",
            "Implement dietary accommodations (vegan/GF now table stakes)",
            "Grow TripAdvisor presence (#16 ranking drives tourist traffic SY doesn't capture)",
            "Group booking packages with clear pricing",
        ],
        "advantages": [
            "Street-level visibility vs hidden basement",
            "Higher Google rating (4.7 vs 4.5)",
            "More reviews (4,109 vs 3,400)",
            "Sports identity C'est What can't touch",
            "10 more years of heritage (1978 vs 1988)",
            "Broader appeal — C'est What is niche craft-beer-geek",
        ],
    },
    "The Caledonian": {
        "address": "856 College Street, Toronto, ON M6H 1A2",
        "neighbourhood": "Ossington / Little Italy",
        "parent": "Independent — owned by Donna and David Wolff (Scottish couple)",
        "founded": "October 2010 (16 years)",
        "website": "thecaledonian.ca",
        "positioning": "Toronto's Only Authentic Scottish Pub & Whisky Bar — uncontested niche",
        "screenshot": None,
        "google_rating": 4.7, "google_reviews": 1195,
        "yelp_rating": 4.0, "yelp_reviews": 163,
        "ig_handle": "@thecaledonian", "ig_followers": 5102, "ig_posts": 2280,
        "platforms": "IG, FB, Twitter", "posts_per_week": "~2.7",
        "menus": ["Food Menu", "Drinks Menu", "Whisky List (200+ malts)", "Events"],
        "signature_items": [
            "200+ whiskies — one of Canada's best selections, covers all Scotch regions",
            "Haggis, Neeps & Tatties ($16) — authentic Scottish",
            "Fish & Chips in Caledonian beer batter ($15) — Monday 2-for-1",
            "Haggis Burger with stilton or aged cheddar (~$18-20)",
            "Deep Fried Mars Bar ($7) — conversation-starter dessert",
            "Sticky Toffee Pudding ($7)",
        ],
        "review_strengths": [
            "Whisky selection — #1 draw, 'one of the best in Canada'",
            "Exceptionally knowledgeable staff on whisky",
            "Authentic Scottish identity — 'feels like Edinburgh'",
            "Outstanding fish & chips",
            "Cozy atmosphere and fantastic patio",
            "Burns Night events and live music",
            "Deep Fried Mars Bar — talkable, mentioned in every review",
            "Reasonable prices for the category",
        ],
        "review_weaknesses": [
            "Small/cramped interior — uncomfortable when full",
            "Extremely loud on busy nights",
            "Inconsistent service — ranges from excellent to 'atrocious'",
            "Slow food times — reports of hour-long waits",
            "No lunch hours (evening only)",
        ],
        "swot": {
            "strengths": ["Uncontested Scottish niche — only one in Toronto", "World-class whisky program (200+)", "Same Google rating as SY (4.7)", "Strong IG (5,102 followers, 2,280 posts)", "Talkable menu items"],
            "weaknesses": ["Tiny venue limits capacity", "Polarized service reviews", "No sports focus", "Evening-only hours", "Shallow beer (~6 taps)", "No email capture or TikTok"],
            "opportunities": ["Whisky education/masterclasses", "Short-form video content", "Whisky club email list", "Lunch expansion", "Distillery partnerships"],
            "threats": ["Rising College St rents", "Growing whisky bar competition", "Small venue revenue ceiling", "Service inconsistency eroding ratings", "Owner succession risk"],
        },
        "learns": [
            "Whisky/spirits depth — 200+ whiskies is a magnet. SY could expand and train staff.",
            "Cultural events — Burns Night drives traffic. SY should do more English cultural moments.",
            "IG volume — 2,280 posts vs SY's 127. Consistent posting compounds over years.",
            "Talkable items — Deep Fried Mars Bar costs nothing but generates word-of-mouth.",
            "Monday 2-for-1 Fish & Chips — simple weekly draw filling slowest night.",
        ],
        "advantages": [
            "Scale: SY is larger, no cramping/noise complaints",
            "Review volume: 4,109 vs 1,195 (3.4x more)",
            "Heritage: 48 years vs 16",
            "Sports identity: defensible moat Caledonian can't touch",
            "All-day operation: SY serves lunch; Caledonian is evening-only",
            "Beer program: ~17 taps vs ~6",
            "Service consistency: Caledonian's biggest vulnerability",
        ],
        "sources": [
            {"label": "The Caledonian", "url": "https://thecaledonian.ca/"},
            {"label": "Yelp", "url": "https://www.yelp.ca/biz/the-caledonian-toronto"},
            {"label": "Instagram", "url": "https://www.instagram.com/thecaledonian/"},
        ],
    },
}

BAR_CART_TEARDOWNS = {
    "BarChef": {
        "address": "472 Queen St W, Toronto, ON M5V 2B2",
        "neighbourhood": "Queen West",
        "parent": "Independent; founded by Frankie Solarik",
        "founded": "2008",
        "website": "barchef.com",
        "positioning": "Globally recognized modernist cocktail bar built around theatrical, multi-sensory drinks and destination-level cocktail credibility.",
        "screenshot": None,
        "google_rating": 4.7, "google_reviews": 2434,
        "yelp_rating": 4.6, "yelp_reviews": 737,
        "ig_handle": "@barchef", "ig_followers": None, "ig_posts": None,
        "platforms": "IG", "posts_per_week": "n/a",
        "menus": ["Modernist Cocktails", "Cocktail Classics", "Bar Snacks", "Private Events"],
        "signature_items": [
            "Multi-sensory modernist cocktails with smoke, aromatics, granitas, and edible components",
            "Global reputation tied to Frankie Solarik and Drink Masters credibility",
            "Special-occasion atmosphere that treats drinks as the main event",
        ],
        "review_strengths": [
            "Drinks are widely perceived as some of the most creative in Toronto",
            "The room feels intimate, date-night friendly, and high-drama",
            "BarChef has destination pull that extends beyond neighbourhood regular traffic",
            "The bar owns a very clear premium-cocktail identity",
        ],
        "review_weaknesses": [
            "Price point is materially above a typical casual bar occasion",
            "The concept is drinks-first and therefore less versatile for broad pub use cases",
            "Expectation levels are extreme, so misses become noticeable quickly",
            "The experience is less accessible for spontaneous, low-commitment social visits",
        ],
        "swot": {
            "strengths": [
                "Global cocktail credibility and one of the clearest drink identities in the city",
                "A true destination bar rather than only a neighbourhood venue",
                "High perceived uniqueness and memory value",
                "Founder halo gives instant authority",
            ],
            "weaknesses": [
                "Very expensive relative to a pub occasion",
                "Less suited to sports, repeat regular traffic, and broad social accessibility",
                "Food is secondary to drinks",
                "The brand is tightly tied to one premium lane",
            ],
            "opportunities": [
                "Continue converting prestige into events and private experiences",
                "Use founder media visibility to expand the halo further",
                "Deepen luxury-cocktail tourism positioning",
                "Create more premium add-on experiences",
            ],
            "threats": [
                "Premium cocktail spend is vulnerable to consumer pullback",
                "Expectation inflation can damage value perception",
                "New high-concept bars can challenge novelty",
                "Its narrow lane limits flexibility if drink demand softens",
            ],
        },
        "learns": [
            "Bar Cart should borrow the clarity of BarChef's positioning, not its price point. Guests know exactly why BarChef exists.",
            "Bar Cart can still benefit from one hero drink or ritualized serve that becomes synonymous with the venue.",
            "Memory structures matter. BarChef's drinks are retold; Bar Cart needs at least one equally retellable signature moment.",
            "Destination value is built by doing one thing unambiguously well.",
        ],
        "advantages": [
            "Bar Cart is more intimate, more East-core specific, and more useful for repeat date-night occasions.",
            "Bar Cart can win on neighbourhood convenience and familiarity while BarChef owns rarefied cocktail prestige.",
            "Bar Cart has stronger St. Lawrence / Esplanade adjacency and can become an easier default for nearby guests.",
            "BarChef is a splurge night; Bar Cart can be a weekly habit.",
        ],
        "sources": [
            {"label": "BarChef OpenTable", "url": "https://www.opentable.ca/r/barchef-toronto"},
            {"label": "BarChef Streets of Toronto", "url": "https://streetsoftoronto.com/restaurants/barchef/"},
            {"label": "BarChef official site", "url": "https://www.barchef.com/"},
        ],
    },
    "Civil Works": {
        "address": "50 Brant St, Toronto, ON M5V 3G9",
        "neighbourhood": "King West / Waterworks",
        "parent": "Civil Liberties group / Nick Kennedy team",
        "founded": "2024",
        "website": "civilworks.ca",
        "positioning": "Award-driven hidden cocktail bar pairing narrative-led drinks, design-forward atmosphere, and a more contemporary educational cocktail identity than a classic bar or pub.",
        "screenshot": None,
        "google_rating": 4.6, "google_reviews": 58,
        "yelp_rating": 5.0, "yelp_reviews": 1,
        "ig_handle": "@civwrksto", "ig_followers": None, "ig_posts": None,
        "platforms": "IG", "posts_per_week": "n/a",
        "menus": ["Cocktails", "Martinis", "Alcohol-Free", "Happy Hour", "Guided Tasting Experiences", "Private Events"],
        "signature_items": [
            "Narrative-driven cocktails with strong conceptual framing",
            "Water-focused tasting and spirit education experiences",
            "Strong hospitality credibility through the Civil Liberties lineage",
        ],
        "review_strengths": [
            "Atmosphere and cocktail creativity are the main draw",
            "The concept feels fresh, hidden, and modern",
            "Award recognition gives the bar immediate authority",
            "Private events and guided tastings broaden its use cases",
        ],
        "review_weaknesses": [
            "Still has a relatively small public review base",
            "Food is limited compared with a pub or restaurant bar",
            "Its relevance is narrower for group sports or casual regular traffic",
            "The concept may feel more niche than broad-market",
        ],
        "swot": {
            "strengths": [
                "Strong cocktail credibility through the Civil Liberties brand halo",
                "Fresh concept with distinct educational and narrative hooks",
                "High perceived originality",
                "Good fit for date-night and special-interest drinkers",
            ],
            "weaknesses": [
                "Small review base compared with legacy bars",
                "Limited food utility",
                "Not built for game-day or sports-driven volume",
                "More niche than neighbourhood-pub broadness",
            ],
            "opportunities": [
                "Build stronger destination status as review volume grows",
                "Expand event and guided-tasting experiences",
                "Leverage Waterworks adjacency for cross-traffic",
                "Convert creative-cocktail interest into repeat community",
            ],
            "threats": [
                "Cocktail novelty is a competitive category with fast follower bars",
                "If service or consistency slips, concept credibility weakens quickly",
                "Demand may skew occasion-based rather than habitual",
                "Small public review base makes sentiment swings more visible",
            ],
        },
        "learns": [
            "Bar Cart should note how Civil Works creates story and ritual around drinks rather than treating them as background.",
            "Programming can be educational as well as social; that makes a venue feel more purposeful.",
            "A hidden or distinctive room works best when the drink menu itself reinforces the identity.",
            "Bar Cart can borrow selective cocktail-storytelling without abandoning neighbourhood accessibility.",
        ],
        "advantages": [
            "Bar Cart is stronger for spontaneous neighbourhood use and pre- or post-dinner drinks on The Esplanade.",
            "Bar Cart has a simpler, more approachable frame for mainstream cocktail occasions.",
            "Civil Works is niche and concept-led; Bar Cart can remain warmer and more dependable.",
            "Bar Cart's location supports repeat local behaviour in ways a destination cocktail room does not.",
        ],
        "sources": [
            {"label": "Civil Works OpenTable", "url": "https://www.opentable.ca/r/civil-works-toronto"},
            {"label": "Civil Works official site", "url": "https://civilworks.ca/"},
            {"label": "Civil Works Streets of Toronto", "url": "https://streetsoftoronto.com/food/civil-works-waterworks-food-hall/"},
        ],
    },
    "CKTL & Co.": {
        "address": "330 Bay St, Toronto, ON M5J 0B6",
        "neighbourhood": "Financial District",
        "parent": "Independent / hospitality group venue",
        "founded": "2023",
        "website": "cktl.ca",
        "positioning": "Business-district cocktail lounge and social bar built around market-style pricing, happy hour, and group-friendly downtown convening.",
        "screenshot": None,
        "google_rating": 4.1, "google_reviews": 206,
        "yelp_rating": 4.4, "yelp_reviews": 5,
        "ig_handle": "@cktlandco", "ig_followers": None, "ig_posts": None,
        "platforms": "IG", "posts_per_week": "n/a",
        "menus": ["Cocktails", "Happy Hour", "Power Lunch", "Group Dining", "Experiences"],
        "signature_items": [
            "Market-pricing angle designed to gamify ordering and conversation",
            "Financial-district positioning around business meals, happy hour, and groups",
            "Power Lunch and social-exchange framing widen daypart relevance",
        ],
        "review_strengths": [
            "Useful for business meals and downtown group gatherings",
            "Happy hour and lunch utility make the venue commercially legible",
            "The concept has a distinctive pricing story",
            "Strong fit for Financial District usage patterns",
        ],
        "review_weaknesses": [
            "The concept is more clever than emotionally ownable",
            "It lacks the heritage and loyalty structure of a true neighbourhood pub",
            "Review depth is still limited",
            "The room reads more corporate lounge than beloved bar institution",
        ],
        "swot": {
            "strengths": [
                "Clear business-district utility",
                "Distinct market-pricing concept gives it a conversation hook",
                "Multi-daypart relevance through lunch and happy hour",
                "Group-friendly downtown format",
            ],
            "weaknesses": [
                "Lower emotional distinctiveness than a legacy pub",
                "Still building public review depth",
                "Corporate feel can limit attachment",
                "Concept hook may not sustain loyalty alone",
            ],
            "opportunities": [
                "Own lunch and after-work occasions more aggressively",
                "Turn the pricing mechanic into stronger brand theatre",
                "Expand business-group and client-entertainment use",
                "Convert convenience usage into repeat habit",
            ],
            "threats": [
                "Financial-district traffic can be volatile",
                "Novelty mechanics can feel gimmicky if not executed well",
                "Corporate-bar competition is crowded",
                "If service slips, convenience alone is not enough",
            ],
        },
        "learns": [
            "Bar Cart can borrow clearer daypart packaging. CKTL is easy to understand for lunch, happy hour, and business use.",
            "A venue benefits when the offer architecture is explicit rather than implied.",
            "Even cocktail bars can create stronger after-work and weekday framing without changing identity.",
            "Commercial clarity matters; guests should know when the venue is best used.",
        ],
        "advantages": [
            "Bar Cart has more independent personality and can feel less transactional than a PATH-adjacent lobby bar.",
            "Bar Cart is stronger for local identity and intimate atmosphere.",
            "CKTL is useful; Bar Cart can be memorable.",
            "Bar Cart can outperform on authenticity and atmosphere if it sharpens its occasion messaging.",
        ],
        "sources": [
            {"label": "CKTL & Co. OpenTable", "url": "https://www.opentable.ca/r/cktl-and-co-toronto"},
            {"label": "CKTL & Co. official site", "url": "https://cktl.ca/"},
            {"label": "CKTL & Co. Tripadvisor", "url": "https://www.tripadvisor.com/Restaurant_Review-g155019-d26714363-Reviews-CKTL_Co-Toronto_Ontario.html"},
        ],
    },
    "Slice of Life": {
        "address": "409 College St, Toronto, ON M5T 1T1",
        "neighbourhood": "Chinatown / Kensington Market",
        "parent": "Independent",
        "founded": "2024",
        "website": "sliceoflifebar.com",
        "positioning": "Intimate design-forward cocktail bar focused on inventive drinks, moody atmosphere, and small-group special-occasion visits.",
        "screenshot": None,
        "google_rating": 4.4, "google_reviews": 51,
        "yelp_rating": "n/a", "yelp_reviews": 0,
        "ig_handle": "@sliceoflifebar", "ig_followers": None, "ig_posts": None,
        "platforms": "IG", "posts_per_week": "n/a",
        "menus": ["Cocktails", "Lounge Seating", "Bar Counter", "Small Plates"],
        "signature_items": [
            "Nature-inspired cocktail menu with conceptual ingredient pairing",
            "Sexy, intimate room with strong date-night appeal",
            "Drinks-forward identity with a calm but polished service style",
        ],
        "review_strengths": [
            "Creative cocktails are the core product and receive the strongest praise",
            "The room feels stylish, intimate, and memorable",
            "Service is described as warm and low-key",
            "The concept is concise and easy to understand",
        ],
        "review_weaknesses": [
            "Very limited review depth so far",
            "Food is clearly secondary",
            "Small scale limits group utility",
            "Not built for high-volume mainstream occasions",
        ],
        "swot": {
            "strengths": [
                "Strong concept clarity and room identity",
                "Creative cocktails with high date-night value",
                "Intimate scale makes it feel special",
                "Easy to recommend for a specific mood and use case",
            ],
            "weaknesses": [
                "Small review base and limited commercial breadth",
                "Low group utility",
                "Food is secondary",
                "Less useful for broad repeat community occasions",
            ],
            "opportunities": [
                "Deepen destination status through cocktail credibility",
                "Build stronger digital word-of-mouth via drink photography",
                "Create special experiences and reservations scarcity",
                "Own the intimate date-night lane more decisively",
            ],
            "threats": [
                "Many Toronto cocktail bars compete on similar atmosphere-led positioning",
                "If novelty fades, the room alone may not hold demand",
                "A narrow use case can limit repeat volume",
                "Small venues are sensitive to reputation swings",
            ],
        },
        "learns": [
            "Bar Cart should notice how powerful a sharply defined atmosphere can be.",
            "A venue does not need to be broad to be memorable; it needs to be specific.",
            "Bar Cart can borrow more room-level storytelling and visual identity without abandoning comfort.",
            "Clear mood ownership helps guests self-select the right occasion.",
        ],
        "advantages": [
            "Bar Cart has broader utility for classic cocktail occasions and lower-friction repeat visits.",
            "Bar Cart can win on familiarity, service rhythm, and neighbourhood regulars.",
            "Slice of Life is niche; Bar Cart can remain a social default for the East core.",
            "Bar Cart has more range across dayparts and audience types than a high-concept late-night room.",
        ],
        "sources": [
            {"label": "Slice of Life OpenTable", "url": "https://www.opentable.ca/r/slice-of-life-toronto"},
            {"label": "Slice of Life official site", "url": "https://www.sliceoflifebar.com/"},
            {"label": "Condé Nast Traveler review", "url": "https://www.cntraveler.com/bars/toronto/slice-of-life"},
        ],
    },
    "No Vacancy": {
        "address": "74 Ossington Ave, Toronto, ON M6J 2Y7",
        "neighbourhood": "Trinity-Bellwoods / Ossington",
        "parent": "Independent",
        "founded": "2024",
        "website": "novacancybar.ca",
        "positioning": "Moody Ossington cocktail bar and restaurant positioned as a full-evening neighbourhood hangout rather than only a quick drinks stop.",
        "screenshot": None,
        "google_rating": 4.4, "google_reviews": 15,
        "yelp_rating": "n/a", "yelp_reviews": 0,
        "ig_handle": "@novacancybar", "ig_followers": None, "ig_posts": None,
        "platforms": "IG", "posts_per_week": "n/a",
        "menus": ["Cocktails", "Wine", "Globally Inspired Bites", "Dinner", "Late Night"],
        "signature_items": [
            "Motel-inspired, moody room design",
            "Cocktails plus a more substantial food offer than many cocktail bars",
            "Flexible positioning for starting, spending, or ending the night there",
        ],
        "review_strengths": [
            "Atmosphere is a major draw",
            "The room feels romantic and neighbourhood-relevant",
            "Cocktails and globally inspired bites expand its use case beyond drinks only",
            "The concept is socially versatile",
        ],
        "review_weaknesses": [
            "Very early-stage review base remains thin",
            "The brand is still proving consistency",
            "Neighbourhood-cool positioning can be hard to scale into loyalty",
            "It competes in a crowded Ossington bar corridor",
        ],
        "swot": {
            "strengths": [
                "Strong mood and design identity",
                "More full-evening utility than a pure cocktail den",
                "Good fit for date nights and casual neighbourhood hangs",
                "Ossington location gives cultural relevance",
            ],
            "weaknesses": [
                "Very small current review base",
                "Still building proof and consistency",
                "Not built for sports or broad game-day demand",
                "Heavy dependence on room feel and novelty",
            ],
            "opportunities": [
                "Own neighbourhood loyalty through repeat dinner-and-drinks traffic",
                "Turn design and room identity into stronger social content",
                "Refine food-and-drink pairing stories",
                "Deepen date-night and local-occasion ownership",
            ],
            "threats": [
                "Ossington is saturated with bars competing for the same cultural customer",
                "New venue buzz can fade quickly",
                "If service or vibe wobbles, there is plenty of substitution nearby",
                "Narrower use case than a general pub",
            ],
        },
        "learns": [
            "Bar Cart should note how a venue can create a more complete evening without becoming formal.",
            "Room design and tone can make a concept feel more intentional and recommendable.",
            "Bar Cart can benefit from stronger mood-setting and sharper pre/post-event framing.",
            "A bar does not need to be niche to feel curated; it just needs clearer atmosphere cues.",
        ],
        "advantages": [
            "Bar Cart is stronger for repeat neighbourhood routines and more consistent classic-cocktail positioning.",
            "Bar Cart's familiarity is more durable than a newer buzz-driven room.",
            "No Vacancy owns mood; Bar Cart can own habit and neighbourhood loyalty.",
            "Bar Cart has broader occasion coverage and higher functional utility for local guests.",
        ],
        "sources": [
            {"label": "No Vacancy OpenTable", "url": "https://www.opentable.ca/r/no-vacancy-toronto"},
            {"label": "No Vacancy official site", "url": "https://www.novacancybar.ca/"},
            {"label": "Streets of Toronto feature", "url": "https://streetsoftoronto.com/food/no-vacancy-ossington/"},
        ],
    },
    "Library Bar": {
        "address": "100 Front Street W, Toronto, ON M5J 1E3",
        "neighbourhood": "Financial District / Union Station",
        "parent": "Fairmont Royal York",
        "founded": "Legacy hotel bar; current iteration refreshed in recent years",
        "website": "librarybartoronto.com",
        "positioning": "Elegant landmark hotel cocktail bar built around classic glamour, top-tier service, and high-volume booking demand for premium business, date-night, and celebration occasions.",
        "screenshot": None,
        "google_rating": 4.5, "google_reviews": 800,
        "yelp_rating": 4.7, "yelp_reviews": 821,
        "ig_handle": "@librarybartoronto", "ig_followers": None, "ig_posts": None,
        "platforms": "IG", "posts_per_week": "n/a",
        "menus": ["Cocktails", "Lunch", "Dinner", "Dessert", "Experiences"],
        "signature_items": [
            "Birdbath Martini and other highly polished signature cocktails",
            "Luxury-hotel context with strong business-meeting and special-occasion utility",
            "One of the highest booking velocities in Toronto cocktail culture",
        ],
        "review_strengths": [
            "Service and atmosphere are consistently praised",
            "The bar feels elegant, polished, and highly occasion-friendly",
            "Cocktail quality and room design justify destination status",
            "Its Union-adjacent location gives major convenience for premium downtown use",
        ],
        "review_weaknesses": [
            "Price point is high and value can be questioned by some guests",
            "The concept is more luxury lounge than neighbourhood social hub",
            "Hotel context can feel less personal than a beloved independent pub",
            "Food and drink spend expectations are elevated",
        ],
        "swot": {
            "strengths": [
                "Top-tier booking demand and premium perception",
                "Strong service reputation",
                "Excellent location for business and celebration traffic",
                "Clear signature drinks and refined room identity",
            ],
            "weaknesses": [
                "High price point narrows accessibility",
                "Less useful as an everyday regulars venue",
                "Hotel-bar identity can feel formal or expensive",
                "Broad pub-social energy is not its lane",
            ],
            "opportunities": [
                "Continue scaling premium experiences and signature rituals",
                "Leverage hotel ecosystem for cross-traffic",
                "Own the Union / Royal York premium bar occasion even harder",
                "Expand cocktail notoriety through high-visibility signatures",
            ],
            "threats": [
                "Luxury bars compete heavily on consistency and service",
                "Economic softness can pressure premium spend",
                "Independent bars can outperform on personality",
                "High volume can erode intimacy if not managed well",
            ],
        },
        "learns": [
            "Bar Cart should pay attention to how Library Bar turns one signature cocktail into a citywide memory structure.",
            "Premium bars make the occasion legible before guests arrive. Bar Cart can do the same for date nights and Esplanade rituals.",
            "Service polish is itself a competitive differentiator.",
            "Clear destination identity helps a venue rise above convenience-only traffic.",
        ],
        "advantages": [
            "Bar Cart is more approachable and more useful for casual repeat social life.",
            "Bar Cart can win on regulars, intimacy, and neighbourhood energy instead of luxury polish.",
            "Library Bar is premium occasion-led; Bar Cart can remain broader and more democratic.",
            "Bar Cart's independent neighbourhood authenticity is harder to imitate than hotel elegance.",
        ],
        "sources": [
            {"label": "Library Bar OpenTable", "url": "https://www.opentable.ca/r/library-bar-fairmont-royal-york-toronto"},
            {"label": "Library Bar official site", "url": "https://www.librarybartoronto.com/"},
            {"label": "En Primeur Library Bar", "url": "https://www.enprimeurclub.com/bars/library-bar-toronto"},
        ],
    },
    "Secrette": {
        "address": "111C Queen Street East, Toronto, ON M5C 1S2",
        "neighbourhood": "Moss Park / Queen East",
        "parent": "Mary Aitken / Verity Group (also GEORGE Restaurant, Verity Women's Club, Ivy at Verity hotel)",
        "founded": "~2022",
        "website": "secretteonqueen.com",
        "positioning": "French-inspired luxury speakeasy hidden upstairs from Michelin-recommended GEORGE Restaurant",
        "screenshot": None,
        "google_rating": 4.3, "google_reviews": 150,
        "yelp_rating": 4.0, "yelp_reviews": 5,
        "ig_handle": "@secretteonqueen", "ig_followers": 1873, "ig_posts": 30,
        "platforms": "IG, FB", "posts_per_week": "~0.2",
        "menus": ["Cocktails (4 categories: Light/Complex/High-Spirited/Zero-Proof)", "Small Plates (from GEORGE kitchen)"],
        "signature_items": [
            "Japonaise 75 $22",
            "Golden Ticket (Buffalo Trace, Port) $22",
            "Premium martinis up to $38",
            "Coconut Pancake with Cured Trout $19",
            "Happy hour with complimentary GEORGE bites",
            "29 seats, Wed-Sat only",
        ],
        "review_strengths": [
            "Bartender John Ko praised for complex layered drinks",
            "Beautiful French interior",
            "Intimate date-night atmosphere",
            "Quality ingredients",
            "The hidden discovery experience",
        ],
        "review_weaknesses": [
            "'Overpriced' is dominant negative theme — $122+ for 3 cocktails",
            "Very small space (29 seats)",
            "Limited hours (Wed-Sat only)",
            "Food stops at 10pm",
            "Near-dormant social media (30 posts total)",
        ],
        "swot": {
            "strengths": [
                "Michelin halo from GEORGE",
                "Chef Loseto's 20-year pedigree",
                "Verity Group institutional backing",
                "Built-in clientele from GEORGE dinner guests",
            ],
            "weaknesses": [
                "Lower Google rating (4.3 vs Bar Cart 4.7)",
                "30 total IG posts",
                "29-seat revenue ceiling",
                "Overpriced perception hardening",
                "No programming or recurring events",
            ],
            "opportunities": [
                "Massively underutilized Instagram",
                "Could leverage GEORGE's Michelin press",
                "Happy hour with free bites is under-marketed",
            ],
            "threats": [
                "New speakeasies like Bar Cart with stronger digital strategies",
                "'Overpriced' narrative hardening",
                "If GEORGE loses Michelin, halo evaporates",
            ],
        },
        "learns": [
            "4-category cocktail organization (Light/Complex/High-Spirited/Zero-Proof) is guest-friendly",
            "Quarterly seasonal rotation creates return hooks",
            "Chef-driven food narrative — elevate Chef Hajare's credentials",
            "Happy hour with restaurant bites — consider Eloise amuse-bouche tie-in",
            "Get on OpenTable for discovery channel",
        ],
        "advantages": [
            "Google rating 4.7 vs 4.3 — major gap",
            "Zero 'overpriced' complaints vs Secrette's dominant negative",
            "Even modest social activity beats 30 total posts",
            "Andrew Whibley pedigree outshines outside Toronto",
            "Thursday jazz gives recurring reason to visit — Secrette has nothing",
            "60 seats vs 29 — 2x revenue headroom",
            "Broader hours",
        ],
        "sources": [
            {"label": "Secrette official site", "url": "https://secretteonqueen.com/"},
            {"label": "Secrette Instagram", "url": "https://www.instagram.com/secretteonqueen/"},
        ],
    },
    "Bar Pompette": {
        "address": "607 College Street, Toronto",
        "neighbourhood": "Little Italy",
        "parent": "Pompette Group (also Bakery Pompette, Bar Allegro, Pelican Wine Imports)",
        "founded": "2021",
        "website": "pompette.ca/barpompette",
        "positioning": "#1 Canada's 100 Best Bars 2025 + 2024. #7 NA 50 Best. #55 World's 50 Best. Art of Hospitality Award.",
        "screenshot": None,
        "google_rating": 4.8, "google_reviews": 153,
        "yelp_rating": 4.5, "yelp_reviews": 18,
        "ig_handle": "@barpompette_to", "ig_followers": 19000, "ig_posts": 143,
        "platforms": "IG, FB", "posts_per_week": "~1.0",
        "menus": ["Cocktails ($22 each)", "Snacks ($7-$14: olives, nuts, radishes, comte, jambon-beurre, saucisson, tarama)"],
        "signature_items": [
            "Cornichon (martini riff) $22 — signature",
            "Nitro Colada $22",
            "Paloma Quemada $22",
            "Ontario terroir + French technique philosophy",
            "Sunday jazz embedded in brand identity",
            "Walk-in only, ~30 seats + seasonal patio",
        ],
        "review_strengths": [
            "World-class cocktails",
            "Unpretentious atmosphere despite #1 ranking",
            "Engaging warm service (Art of Hospitality Award)",
            "Charming European aesthetic",
            "Back patio",
            "Sunday jazz",
        ],
        "review_weaknesses": [
            "Occasional service attitude/inattention",
            "Food overpriced for portions — 'one small triangle of cheese for $12'",
            "Wait times at peak",
            "Forgotten orders reported",
        ],
        "swot": {
            "strengths": [
                "#1 bar in Canada — awards moat",
                "MOF Barman owner (Maxime Hoerth)",
                "Best Sommelier in France co-owner",
                "Ontario terroir storytelling",
                "19K IG followers",
            ],
            "weaknesses": [
                "Snack-only food (no real dinner)",
                "30-seat capacity",
                "Walk-in only creates friction",
                "College St competition",
            ],
            "opportunities": [
                "Submit for Canada's 100 Best 2026 now",
                "Terroir storytelling transferable to Bar Cart",
            ],
            "threats": [
                "Awards attention wanes eventually",
                "Owner attention split across 5 businesses",
            ],
        },
        "learns": [
            "Terroir storytelling — name farms and suppliers on the menu",
            "Lock in 3-5 permanent signature cocktails as ordering rituals",
            "Elevate Thursday jazz to brand-identity level",
            "Submit for Canada's 100 Best Bars 2026 now",
            "Add $8-12 bar snacks alongside existing plates",
            "Train 'kind over cool' hospitality script",
        ],
        "advantages": [
            "Speakeasy entrance is inherently more viral than College St storefront",
            "Real food, not just snacks — Chicken 65 is a destination dish",
            "Tourism-adjacent location vs Little Italy requiring intentional travel",
            "Thursday > Sunday for jazz (start of weekend vs work-tomorrow)",
            "Untold story = blank canvas for maximum first-impression impact",
        ],
        "sources": [
            {"label": "Bar Pompette official site", "url": "https://pompette.ca/barpompette"},
            {"label": "Bar Pompette Instagram", "url": "https://www.instagram.com/barpompette_to/"},
        ],
    },
    "Compton Ave.": {
        "address": "1282 Dundas St W, Toronto",
        "neighbourhood": "Dundas West / Little Portugal",
        "parent": "Frankie Solarik Holdings (also BarChef, Prequel & Co. Apothecary, BarChef NYC)",
        "founded": "March 2024",
        "website": "comptonave.com",
        "positioning": "British-inspired cocktail bar by BarChef team. Canada's 100 Best 2025. London townhouse aesthetic.",
        "screenshot": None,
        "google_rating": 4.7, "google_reviews": 42,
        "yelp_rating": 3.5, "yelp_reviews": 11,
        "ig_handle": "@barcomptonave", "ig_followers": 16000, "ig_posts": 212,
        "platforms": "IG, FB", "posts_per_week": "~2.0",
        "menus": [
            "Signature Cocktails ($16-$26)", "Martini Selection ($19-$22)",
            "Draught Cocktails ($17-$23)", "Classics ($24-$26)",
            "Spirit-Free ($16)", "Food (Scotch Egg $11, Fish & Chips $16, Steak Diane $21)",
        ],
        "signature_items": [
            "Umami Old Fashioned $23",
            "Martini Hour: all martinis $12, Tue-Sun open to 8pm",
            "Scotch Egg $11 (on smoked hay, set ablaze)",
            "Steak Diane $21 (picanha, charcoal-grilled)",
            "Bone Marrow & Crumpets $14",
        ],
        "review_strengths": [
            "Cocktail creativity",
            "Moody opulent interior",
            "Attentive bartenders",
            "Martini Hour value ($12)",
            "Holiday pop-ups",
        ],
        "review_weaknesses": [
            "Food 'fine but not memorable'",
            "Seating management friction (30-min windows)",
            "Manager confrontation incident documented",
            "Weak TripAdvisor/Yelp",
        ],
        "swot": {
            "strengths": [
                "Celebrity owner (Netflix, NYT)",
                "Canada's 100 Best listing",
                "16K IG followers",
                "Martini Hour traffic driver",
                "Deep house-made ingredients",
                "Multi-venue ecosystem",
            ],
            "weaknesses": [
                "Service complaints",
                "Mediocre food reviews",
                "Dundas West saturation",
                "Solarik's attention split across 4+ venues",
                "No TikTok",
            ],
            "opportunities": [
                "Neither bar on TikTok — first-mover advantage",
                "Hidden-door content tailor-made for platform",
            ],
            "threats": [
                "Dundas West cocktail bar saturation",
                "Owner attention split",
            ],
        },
        "learns": [
            "Create a named happy hour (like Martini Hour) at gateway price for 5-7pm",
            "Develop low-cost iconic bar snack ($10-12) that appears in every review",
            "Pitch for Canada's 100 Best / blogTO",
            "Own TikTok first — hidden-door content is tailor-made",
            "Invest in IG consistency (3-4x/week)",
            "Market Eloise-to-Bar-Cart as two-act experience",
        ],
        "advantages": [
            "Zero local competition on The Esplanade vs saturated Dundas West",
            "Eloise-to-Bar Cart funnel vs standalone storefront",
            "Uniformly positive reviews — no service red flags",
            "South Asian food is unique lane vs crowded British pub space",
            "Andrew Whibley can build focused personal brand",
        ],
        "sources": [
            {"label": "Compton Ave. official site", "url": "https://comptonave.com/"},
            {"label": "Compton Ave. Instagram", "url": "https://www.instagram.com/barcomptonave/"},
        ],
    },
    "Civil Liberties": {
        "address": "878 Bloor St W, Toronto, ON M6G 1M5",
        "neighbourhood": "Bloor West / Bloorcourt",
        "parent": "Nick Kennedy, David Huynh, Cole Stanford (also Vit Beo, Civil Works, Third Place)",
        "founded": "2015",
        "website": "civillibertiesbar.com",
        "positioning": "No-menu bartender-led bespoke cocktails. NA 50 Best #21. Canada's 100 Best #3.",
        "screenshot": None,
        "google_rating": 4.7, "google_reviews": 1247,
        "yelp_rating": 4.0, "yelp_reviews": 65,
        "ig_handle": "@civlibto", "ig_followers": 15000, "ig_posts": 812,
        "platforms": "IG, FB, Twitter", "posts_per_week": "~1.5",
        "menus": [
            "No printed menu — bespoke cocktails crafted per guest",
            "Light bar snacks (hummus ~$7)",
            "Vit Beo next door for wings (~$12)",
            "Bar School: ticketed cocktail classes",
        ],
        "signature_items": [
            "Zero printed menu — bartenders interview guests and craft one-off drinks",
            "Cocktails ~$13-15",
            "Bar School seminars via Eventbrite",
            "'Kind over cool' hospitality philosophy",
            "Civil Works (sister venue) won Best Cocktail Menu at NA 50 Best 2025",
        ],
        "review_strengths": [
            "Bespoke experience unlike any other",
            "Bartender talent and knowledge",
            "Affordable pricing at world-class level ($13-15)",
            "'Kind over cool' warmth",
            "Great date spot",
            "Bar School education programming",
        ],
        "review_weaknesses": [
            "Loud music making conversation difficult",
            "20-min waits with no reservations",
            "Cramped seating",
            "No real food on-site",
            "Concept intimidating for first-timers",
        ],
        "swot": {
            "strengths": [
                "Decade of international awards",
                "15K IG followers",
                "No-menu concept is defensible moat",
                "Bar School creates revenue + community",
                "4.7 Google with 1,247 reviews",
            ],
            "weaknesses": [
                "No food on-site",
                "Walk-in only with waits",
                "Loud environment",
                "Concept requires explanation",
            ],
            "opportunities": [
                "Add 'Bartender's Choice' line item to capture bespoke appeal",
                "Launch cocktail masterclass nights",
            ],
            "threats": [
                "Civil Works may split team attention",
                "No-menu concept has a ceiling on casual market",
            ],
        },
        "learns": [
            "Add 'Bartender's Choice / Surprise Me' to menu — capture bespoke appeal without abandoning menu",
            "Launch cocktail masterclass nights on slow nights (Mon/Tue) — charge $60-80/person",
            "Consider a daily classic at $14-16 to match Civil Liberties' value perception",
            "Train 'kind over cool' warmth — the Eloise entrance should feel like a secret shared, not a gate",
            "Begin submitting for Canada's 100 Best Bars",
        ],
        "advantages": [
            "Full food menu in one venue vs two-venue workaround",
            "Speakeasy entrance as social media content driver",
            "Downtown tourist-accessible location",
            "Menu-driven accessibility for newcomers",
            "Thursday jazz programming",
            "Double the capacity",
        ],
        "sources": [
            {"label": "Civil Liberties official site", "url": "https://civillibertiesbar.com/"},
            {"label": "Civil Liberties Instagram", "url": "https://www.instagram.com/civlibto/"},
        ],
    },
    "Mother": {
        "address": "874 Queen Street West, Toronto, ON M6J 1G3",
        "neighbourhood": "Trinity-Bellwoods / Queen West",
        "parent": "Massimo Zitti (Diageo World Class Bartender of the Year 2022)",
        "founded": "May 2019",
        "website": "motherdrinks.co",
        "positioning": "Fermentation-forward cocktail bar with narrative menu chapters. Canada's 100 Best #12. NA 50 Best #44. Sustainability Award.",
        "screenshot": None,
        "google_rating": 4.7, "google_reviews": 980,
        "yelp_rating": 4.0, "yelp_reviews": 65,
        "ig_handle": "@mothercocktailbar", "ig_followers": 20000, "ig_posts": 500,
        "platforms": "IG, FB, TikTok (39.6K followers!), YouTube", "posts_per_week": "~3.0",
        "menus": [
            "Narrative menu chapters (current: 'The 5th Horizon')",
            "Food: small-plate sharable",
            "Zero-proof section (first-class)",
        ],
        "signature_items": [
            "Truffle Croissant (croissant distillate, truffle, chamomile, amaro, scotch)",
            "Mother Gibson $16",
            "Jerk Karaage $12 (cheapest protein)",
            "Koji Aged Beef Tartare $20",
            "Zero-proof: Petit Bonhomme, Faux Negroni, Virgo",
            "Menu chapters rotate seasonally",
        ],
        "review_strengths": [
            "Innovation and storytelling",
            "Fermentation uniqueness",
            "Staff warmth",
            "Zero-proof quality best-in-class",
            "Food quality",
            "Beautiful menu design",
        ],
        "review_weaknesses": [
            "Reservations essentially required",
            "Small portions for price",
            "Can feel exclusive/intimidating to casual visitors",
        ],
        "swot": {
            "strengths": [
                "Fermentation USP no one can replicate",
                "Narrative chapters create content cycles",
                "Zitti's personal brand (World Class winner)",
                "TikTok: 39.6K followers + 345K likes",
                "Sustainability Award",
                "4.7 Google with 980 reviews",
            ],
            "weaknesses": [
                "Saturated Queen West corridor",
                "Reservation-required limits spontaneity",
                "High-concept can feel intimidating",
                "Key-person risk on Zitti",
            ],
            "opportunities": [
                "Seasonal chapter naming turns refreshes into launchable events",
                "Zero-proof section captures growing non-drinking market",
            ],
            "threats": [
                "Queen West competition",
                "If concept feels too exclusive, limits growth",
            ],
        },
        "learns": [
            "Adopt seasonal 'chapter' naming for menu refreshes — turns updates into launch events",
            "Develop 2-3 house-made signature ingredients as modern-technique pillar",
            "Add dedicated zero-proof section (2+ options)",
            "Create explicit cocktail-food pairings",
            "Build Andrew Whibley's personal brand modestly",
            "Post 1 Reel/week exploiting cinematic speakeasy setting",
        ],
        "advantages": [
            "Hidden-door concept is theatrical moat Mother cannot replicate",
            "Classic cocktail accessibility appeals to wider audience",
            "The Esplanade is uncrowded geographic moat",
            "Eloise-to-Bar-Cart dining pipeline is built-in funnel",
            "Walk-in friendliness captures spontaneity market Mother loses",
        ],
        "sources": [
            {"label": "Mother official site", "url": "https://motherdrinks.co/"},
            {"label": "Mother Instagram", "url": "https://www.instagram.com/mothercocktailbar/"},
        ],
    },
    "Cry Baby Gallery": {
        "address": "1468 Dundas Street West, Toronto, ON M6J 1Y6",
        "neighbourhood": "Little Portugal / Dundas West",
        "parent": "Rob Granicolo (The Minister Group), Stephen & Mike Gouzopoulos",
        "founded": "~2018",
        "website": "crybabygallery.ca",
        "positioning": "Art gallery + hidden speakeasy. Canada's 100 Best #11 (climbed from #29 in 4 years). NA 100 Best #69.",
        "screenshot": None,
        "google_rating": 4.6, "google_reviews": 475,
        "yelp_rating": 4.0, "yelp_reviews": 17,
        "ig_handle": "@crybaby.gallery", "ig_followers": 20000, "ig_posts": 379,
        "platforms": "IG, FB", "posts_per_week": "~1.5",
        "menus": ["Cocktails ($13-$19)", "Cold snacks only (oysters, olives, cured meats)"],
        "signature_items": [
            "Cry Baby Zombie (proprietary sorrel syrup)",
            "Sad Boy Summer",
            "Burner Phone",
            "East Coast oysters $18/half dozen",
            "Gallery with rotating local art exhibitions",
            "30-seat hidden bar behind gallery curtain",
        ],
        "review_strengths": [
            "Creative cocktails",
            "Hidden speakeasy discovery factor",
            "Rotating art adds freshness",
            "Knowledgeable bartenders",
            "Strong whisky/amari selection",
            "Great date-night spot",
        ],
        "review_weaknesses": [
            "Very limited food (no kitchen)",
            "Cramped 30-seat space",
            "Walk-in only waits",
            "Steep stairs to washrooms (accessibility)",
        ],
        "swot": {
            "strengths": [
                "Gallery-to-bar dual concept generates press organically",
                "Canada's #11 ranking",
                "20K IG followers",
                "Rob Granicolo's industry network",
                "Cocktails $13-19 (more affordable)",
            ],
            "weaknesses": [
                "No kitchen — cold snacks only",
                "30-seat capacity",
                "Walk-in only",
                "Dundas West saturation",
            ],
            "opportunities": [
                "Develop iconic signature serves with proprietary ingredients",
                "Use rotating visual/art elements to keep room fresh",
                "Pursue Canada's 100 Best — Cry Baby climbed #29 to #11 in 4 years",
            ],
            "threats": [
                "Dundas West competition",
                "Small venue ceiling",
            ],
        },
        "learns": [
            "Develop 1-2 iconic signatures with proprietary ingredients (Cry Baby Zombie model)",
            "Use rotating visual/art elements to keep room fresh and generate content without operational cost",
            "Actively pursue Canada's 100 Best submissions — Cry Baby's climb is the roadmap",
            "Lean into dual-identity branding (Eloise + Bar Cart) like gallery + bar",
        ],
        "advantages": [
            "Real food program enables full-evening visits — Cry Baby has no kitchen",
            "The Esplanade is underserved for cocktails vs saturated Dundas West",
            "Eloise funnel drives foot traffic — Cry Baby stands alone",
            "Reservations accepted vs walk-in gamble",
            "Higher Google rating (4.7 vs 4.6)",
            "Andrew Whibley pedigree is untapped founder story",
        ],
        "sources": [
            {"label": "Cry Baby Gallery official site", "url": "https://crybabygallery.ca/"},
            {"label": "Cry Baby Gallery Instagram", "url": "https://www.instagram.com/crybaby.gallery/"},
        ],
    },
    "Prequel and Co. Apothecary": {
        "address": "844 Queen St W, Toronto",
        "neighbourhood": "Queen West / Trinity Bellwoods",
        "parent": "Frankie Solarik Holdings (also BarChef, Compton Ave.)",
        "founded": "~2023",
        "website": "prequelandco.com",
        "positioning": "Apothecary-themed speakeasy. Hand-ground spices, theatrical presentation. Canada's 100 Best recognized.",
        "screenshot": None,
        "google_rating": 4.6, "google_reviews": 200,
        "yelp_rating": 4.0, "yelp_reviews": 15,
        "ig_handle": "@prequelandco", "ig_followers": 8000, "ig_posts": 300,
        "platforms": "IG, FB", "posts_per_week": "~1.5",
        "menus": ["Apothecary Cocktails", "Theatrical presentation with hand-ground spices"],
        "signature_items": [
            "Hand-ground spices in cocktails",
            "Apothecary-themed entrance and presentation",
            "Part of Frankie Solarik's 3-venue empire",
        ],
        "review_strengths": [
            "Theatrical experience",
            "Unique apothecary concept",
            "Quality cocktails",
            "Instagrammable setting",
        ],
        "review_weaknesses": [
            "Can feel gimmicky to some",
            "Higher prices for theatrical premium",
            "Small venue",
        ],
        "swot": {
            "strengths": [
                "Unique apothecary concept",
                "Solarik celebrity",
                "Canada's 100 Best",
            ],
            "weaknesses": [
                "Solarik attention split",
                "Theatrical concept may not age well",
                "Small venue",
            ],
            "opportunities": [
                "Theatrical presentation elements can elevate the experience",
            ],
            "threats": [
                "If novelty wears off",
            ],
        },
        "learns": [
            "Theatrical presentation elements can elevate the experience",
            "Apothecary/craft ingredient storytelling drives word-of-mouth",
            "Solarik's multi-venue model shows how to build a cocktail brand ecosystem",
        ],
        "advantages": [
            "Bar Cart's hidden entrance is more naturally theatrical than themed decor",
            "Whibley's technique focus vs theatrical spectacle appeals to cocktail purists",
            "Eloise food pipeline vs no substantial food",
        ],
        "sources": [
            {"label": "Prequel and Co. Instagram", "url": "https://www.instagram.com/prequelandco/"},
        ],
    },
}

OSF_TEARDOWNS = {
    "Scaddabush": {
        "address": "200 Front St W Unit G001, Toronto, ON M5V 3J1",
        "neighbourhood": "Front Street / Entertainment District",
        "parent": "SIR Corp. / Service Inspired Restaurants",
        "founded": "Brand launched in 2013; Front Street is an established downtown Toronto location",
        "website": "scaddabush.com",
        "positioning": "Modern casual Italian kitchen-and-bar chain built around made-from-scratch cues, a lively social room, and stronger bar energy than classic family Italian chains.",
        "screenshot": "https://scaddabush.com/wp-content/uploads/2025/07/Event_Venue_Front-Street_Hero.jpg",
        "google_rating": 4.5, "google_reviews": 9900,
        "yelp_rating": 3.6, "yelp_reviews": 514,
        "ig_handle": "@scaddabush", "ig_followers": 24000, "ig_posts": 2046,
        "platforms": "IG, FB", "posts_per_week": "~2.5",
        "menus": ["Lunch / Dinner", "Happy Hour", "Drinks", "Dessert", "Party & Events", "Takeout / Delivery"],
        "signature_items": [
            "Hand-stretched fresh mozzarella and the visible mozzarella-bar craft cue",
            "Fresh-made pasta and modernized Italian classics like Chicken Parmesan with Alfredo mafalde",
            "Wednesday half-priced bottles of wine and a defined happy-hour program",
        ],
        "review_strengths": [
            "Fresh, handcrafted feel is repeatedly mentioned in reviews",
            "Good service and strong fit for groups, celebrations, and pre-theatre dinners",
            "The room feels more social and current than legacy red-sauce competitors",
            "Visible food craft and cocktail positioning make the brand feel more premium",
        ],
        "review_weaknesses": [
            "Noise level is a recurring complaint in the open-concept room",
            "Value perception is less consistent when guests compare price to portion size",
            "Busy layout and table spacing can make the experience feel hectic at peak",
            "The brand risks feeling chain-polished rather than genuinely distinctive",
        ],
        "swot": {
            "strengths": [
                "Modernized Italian brand with clear made-from-scratch positioning",
                "Much larger social reach than OSF online",
                "Promotions are sharper and more visible than OSF's current offer structure",
                "Strong urban group-dining and event-booking story",
                "Cocktail and wine programs help it compete beyond pasta alone",
            ],
            "weaknesses": [
                "Google review volume is lower than OSF despite strong traffic location",
                "Noise and layout complaints work against family comfort",
                "Value story is weaker because the meal is not bundled",
                "Chain aesthetics are polished but less memorable than OSF's heritage room",
            ],
            "opportunities": [
                "Continue turning fresh-made craft into more social and video content",
                "Extend event-booking and corporate-group capture around downtown demand",
                "Use midweek offers to deepen habitual rather than occasional visits",
                "Push cocktail-led and late-evening demand harder than classic family chains can",
            ],
            "threats": [
                "Commodity inflation can squeeze a made-from-scratch positioning",
                "Downtown casual Italian is crowded and promotion-heavy",
                "If service slips, the premium-over-value narrative breaks quickly",
                "Legacy family chains can undercut on perceived value bundles",
            ],
        },
        "learns": [
            "Merchandise craftsmanship more aggressively. Scaddabush sells fresh mozzarella, pasta, and cocktail-making as part of the experience, not just the food.",
            "Build visible weekly offers. Wednesday wine and a clear happy-hour program give guests a reason to choose a specific day.",
            "Package group occasions harder. Scaddabush markets parties and semi-private events more directly than OSF currently does.",
            "Modernize hero-item photography and menu language so classic pasta feels more current online.",
            "Use the bar program as a traffic driver instead of treating drinks as secondary to the meal bundle.",
        ],
        "advantages": [
            "OSF's bundled meal remains the stronger value proposition for family and tourist traffic.",
            "OSF's heritage room and nostalgic artifacts are more ownable than Scaddabush's polished chain atmosphere.",
            "OSF has materially higher Google review volume, which signals longer-standing broad-market trust.",
            "OSF is better set up for very large groups and multi-generational occasions.",
            "OSF's location on The Esplanade is more destination-like for visitors pairing dinner with nearby attractions.",
        ],
        "sources": [
            {"label": "Scaddabush Front Street", "url": "https://scaddabush.com/welcome/sbfront/"},
            {"label": "SIR Corp. brand context", "url": "https://www.sircorp.com/wp-content/uploads/2023/12/SIR-CORP-Q1-2024-MDA_Final.pdf"},
        ],
    },
    "East Side Mario's": {
        "address": "2171 Steeles Ave W, North York, ON M3J 3N2",
        "neighbourhood": "North York / Toronto chain-market benchmark",
        "parent": "Recipe Unlimited Corporation",
        "founded": "1987 in Canada",
        "website": "eastsidemarios.com",
        "positioning": "Family-first Canadian Italian-American casual-dining chain built around abundant portions, all-you-can-eat inclusions, and aggressive weekday promotions.",
        "screenshot": None,
        "google_rating": 4.6, "google_reviews": 4978,
        "yelp_rating": "n/a", "yelp_reviews": 0,
        "ig_handle": "@eastsidemarios", "ig_followers": 17000, "ig_posts": 770,
        "platforms": "IG, FB, YouTube", "posts_per_week": "~1.8",
        "menus": ["Food", "Drinks", "Daily Deals", "Lunch", "Mini Marios", "Group Menus", "Takeout / Delivery"],
        "signature_items": [
            "All-You-Can-Eat soup, salad, and garlic homeloaf with dine-in entrees, pasta, and pizza",
            "Chicken Parmigiana, Spaghetti & Meatballs, and other familiar Italian-American classics",
            "A strong weekly offer spine: Pasta Monday, Kids Eat Free Tuesday, Buy One Take One Wednesday, and Amore for Two Thursday",
        ],
        "review_strengths": [
            "Guests consistently call out value, generous portions, and family friendliness",
            "The chain's promotional cadence gives people a concrete reason to visit midweek",
            "Comfort-food positioning is clear and easy to understand across locations",
            "Group menus and 8+ party booking tools make celebratory dining operationally easy",
        ],
        "review_weaknesses": [
            "The experience can feel generic or chain-standardized rather than memorable",
            "Ingredients and room design do not read as premium compared with stronger Italian concepts",
            "The promotion-heavy posture can train guests to buy on deals instead of brand affinity",
            "The theatricality is mostly in the offer architecture, not in the room itself",
        ],
        "swot": {
            "strengths": [
                "Exceptionally clear value proposition and family positioning",
                "Promotional programming is much more developed than OSF's current cadence",
                "Stronger digital offer architecture with app, emails, and recurring deals",
                "Wide familiarity with Canadian diners and repeatable operating model",
            ],
            "weaknesses": [
                "Chain sameness limits emotional distinctiveness",
                "No ownable heritage environment comparable to OSF's room",
                "Heavy discounting can compress perceived quality",
                "Less useful for tourists seeking a one-of-one Toronto dining experience",
            ],
            "opportunities": [
                "Keep building routine through stronger CRM and app-led repeat behavior",
                "Use promotions to ladder guests into group occasions and family celebrations",
                "Expand signature beverages and social content so the brand is not only deal-led",
                "Tighten lunch and off-premise capture around convenience occasions",
            ],
            "threats": [
                "Discount-driven casual dining is vulnerable to margin pressure",
                "Modern Italian chains can outperform it on freshness and atmosphere",
                "Independent heritage venues can beat it on authenticity and memory value",
                "Consumer fatigue around chain sameness can weaken the offer over time",
            ],
        },
        "learns": [
            "OSF should copy the weekly offer spine. East Side gives guests a very clear reason to choose Monday, Tuesday, Wednesday, and Thursday.",
            "Promotions should be visible and legible on the website, not buried inside the general value story.",
            "OSF can build better family and group demand capture through dedicated group menus, birthday positioning, and 8+ booking messaging.",
            "Email and app capture matter. East Side is using CRM and digital offers more actively than OSF.",
            "A comfort-food brand can still create urgency when weekly specials are routinized and repeated clearly.",
        ],
        "advantages": [
            "OSF has the far more memorable room and heritage narrative.",
            "OSF feels more destination-worthy for visitors and special outings on The Esplanade.",
            "OSF's review volume and long-term trust base are stronger than one representative East Side location.",
            "OSF can win if it adds offer discipline without sacrificing its one-of-one atmosphere.",
            "OSF is less vulnerable to looking interchangeable with every other suburban chain box.",
        ],
        "sources": [
            {"label": "East Side Mario's home", "url": "https://www.eastsidemarios.com/"},
            {"label": "East Side Mario's about", "url": "https://www.eastsidemarios.com/en/aboutus.html"},
            {"label": "East Side Mario's specials", "url": "https://www.eastsidemarios.com/en/specials.html"},
            {"label": "East Side Mario's group events", "url": "https://www.eastsidemarios.com/en/groups.html"},
        ],
    },
    "Olive Garden": {
        "address": "51 Reenders Drive, Winnipeg, MB R2C 5E8",
        "neighbourhood": "Winnipeg - Lagimodiere / active Canadian benchmark",
        "parent": "Recipe Unlimited Corporation in Canada under national development agreement with Darden Restaurants",
        "founded": "1982 in Orlando, Florida; Canadian expansion accelerated under Recipe in January 2026",
        "website": "olivegarden.com",
        "positioning": "Mass-scale Italian-American family chain with active Canadian operations, built around abundance, broad familiarity, and a polished comfort-and-value system anchored by breadsticks, salad, soups, lunch specials, catering, and family bundles.",
        "screenshot": None,
        "google_rating": 4.2, "google_reviews": 2608,
        "yelp_rating": "n/a", "yelp_reviews": 0,
        "ig_handle": "@olivegarden", "ig_followers": 771000, "ig_posts": 2304,
        "platforms": "IG, FB, TikTok, X", "posts_per_week": "~2.8",
        "menus": ["Classic Entrees", "Create Your Own Pasta", "Specials", "Lunch-Sized Favorites", "To Go", "Catering", "Family-Style Meals"],
        "signature_items": [
            "Breadsticks, signature salad, and soup-led abundance as the central value ritual",
            "Family-style meals, $8 take-home entrees in Canada, and catering designed for larger household occasions",
            "Lunch-sized favourites and Italian-inspired cocktails layered onto the core comfort-food promise",
        ],
        "review_strengths": [
            "The promise is extremely easy to understand: comfort, abundance, and familiarity",
            "Canadian locations actively support catering, delivery, reservations, and family bundles",
            "The offer system is broader than most peers because it spans dine-in, lunch, take-home, and group occasions",
            "Ontario openings at Vaughan Mills, Westboro, and Ajax signal brand confidence and renewed Canadian relevance",
        ],
        "review_weaknesses": [
            "It is highly standardized and not culturally or locally distinctive",
            "Food quality is often described as reliable rather than exciting",
            "The brand competes on operational consistency more than memory-making atmosphere",
            "There is still no open Toronto location today, so OSF competes against the brand's value logic more than against an immediate downtown storefront",
        ],
        "swot": {
            "strengths": [
                "Enormous brand recognition and social reach",
                "Crystal-clear abundance and family-comfort value story",
                "Robust Canadian off-premise, catering, and family-bundle infrastructure",
                "Ontario expansion gives the brand fresh momentum in OSF's home province",
            ],
            "weaknesses": [
                "No Toronto location open yet, so relevance here is still partially anticipatory",
                "Chain ubiquity makes it less special or destination-worthy",
                "The room and brand aesthetics are generic compared with heritage-led environments",
                "Product credibility is broad but rarely premium",
            ],
            "opportunities": [
                "Use new Ontario openings to rebuild national awareness quickly",
                "Continue turning convenience and family-scale ordering into a stronger digital moat",
                "Cross-sell lunch, take-home, and catering more aggressively",
                "Keep simplifying value cues in periods of consumer price sensitivity",
            ],
            "threats": [
                "Broad casual dining chains are exposed to changing value expectations",
                "Independent restaurants can outperform on authenticity and local relevance",
                "Consumers can see the category as commoditized if the food feels too standardized",
                "Ontario expansion will raise expectations around execution and value in a more competitive market",
            ],
        },
        "learns": [
            "OSF should sharpen the ritual around what is included in the meal. Olive Garden makes its breadsticks-and-salad promise feel iconic.",
            "Off-premise architecture matters. Family bundles, catering, and take-home offers create multiple revenue occasions from the same kitchen.",
            "The brand sells comfort with ruthless clarity. OSF can make its full-meal promise more explicit at every touchpoint.",
            "OSF should think in occasion systems, not just menu items: dine-in, family bundle, group event, lunch, and next-day take-home.",
            "Ontario growth means this is no longer just a U.S. benchmark. OSF should prepare for Olive Garden's value logic to become familiar again in the province.",
        ],
        "advantages": [
            "OSF has a real Toronto location advantage and a more distinctive heritage environment.",
            "OSF can feel far more memorable and local than Olive Garden's standardized format.",
            "OSF's room, artifacts, and Esplanade setting provide experiential texture Olive Garden cannot easily replicate.",
            "OSF can borrow clarity and occasion design from Olive Garden without becoming generic.",
            "For Toronto diners today, OSF is still the established in-market institution while Ontario Olive Garden sites remain under development.",
        ],
        "sources": [
            {"label": "Olive Garden Canada", "url": "https://www.olivegarden.ca/"},
            {"label": "Olive Garden Winnipeg - Lagimodiere", "url": "https://www.olivegarden.ca/en/locations/mb/winnipeg/51-reenders-drive"},
            {"label": "Recipe expansion announcement", "url": "https://www.newswire.ca/news-releases/recipe-restaurant-group-international-announces-next-phase-of-olive-garden-expansion-in-canada-822147646.html"},
            {"label": "Recipe Ajax announcement", "url": "https://www.newswire.ca/news-releases/recipe-restaurant-group-international-announces-third-new-olive-garden-location-in-canada-802210548.html"},
            {"label": "Review-count proxy for Winnipeg location", "url": "https://www.sluurpy.com/en/winnipeg/restaurant/4757808/olive-garden-italian-restaurant"},
        ],
    },
}

BC_TEARDOWNS = {
    "Track & Field": {
        "address": "582 College St, Toronto, ON M6G 1B3",
        "neighbourhood": "College West / Little Italy",
        "parent": "Independent Toronto nightlife group; sister venue to Bangarang and Hail Mary",
        "founded": "Current Track & Field format established in the early 2020s",
        "website": "trackandfieldbar.com",
        "screenshot": None,
        "google_rating": 4.1, "google_reviews": 740,
        "yelp_rating": "n/a", "yelp_reviews": 0,
        "ig_handle": "@trackandfieldbar", "ig_followers": 8637,
        "platforms": "IG, FB", "posts_per_week": "~3.0",
        "positioning": "Play-first nightlife bar that competes by turning games, social mixers, and large-group energy into the core reason to visit rather than relying on live music or pure clubbing.",
        "menus": ["Drinks", "Games", "Trivia", "Singles Events", "Reservations", "Private Events"],
        "signature_items": [
            "Indoor bocce, shuffleboard, crokinole, and cornhole as the core participatory hook",
            "Dual-space format with the main bar plus Hail Mary upstairs for a more intimate late-night room",
            "Singles nights, trivia, and DJ programming built around social participation rather than passive attendance",
        ],
        "review_strengths": [
            "Fun, interactive atmosphere gives groups a reason to stay longer",
            "Music and late-night energy read as playful rather than intimidating",
            "Staff and event execution are often praised in group-night reviews",
            "The venue sells a full social occasion instead of just drinks and background entertainment",
        ],
        "review_weaknesses": [
            "The concept is broad and games-led, so music identity is less ownable than Bar Cathedral's",
            "The room can feel more like a group-activity bar than a destination cultural venue",
            "Some accessibility limits remain around parts of the gaming experience",
            "Its experiential value depends heavily on turnout and friend-group energy",
        ],
        "swot": {
            "strengths": [
                "Interactive play gives the venue a very clear participation hook",
                "Programming is diversified across trivia, singles, DJs, and private events",
                "Group bookings and party packages are productized far better than Bar Cathedral's",
                "The dual-space setup creates more occasion flexibility than a single-room nightlife concept",
            ],
            "weaknesses": [
                "Music culture is secondary to the participation gimmick",
                "Less distinctive visual world than a strong themed nightlife brand",
                "Relies on group dynamics more than individual-ticketed demand",
                "Brand memory can collapse into 'games bar' if programming isn't promoted well",
            ],
            "opportunities": [
                "Deepen CRM and event-booking monetization for birthdays and team events",
                "Keep packaging social mixers as repeat weekly rituals",
                "Use Hail Mary as a more elevated secondary identity",
                "Turn playable moments into stronger short-form content",
            ],
            "threats": [
                "Experience-first bars are vulnerable if novelty fades",
                "Other activity bars can copy individual game elements",
                "Large-group nightlife demand is sensitive to traffic and seasonality",
                "If event cadence softens, the room loses some of its core reason to visit",
            ],
        },
        "learns": [
            "Bar Cathedral should build clearer participation hooks around specific nights instead of relying only on lineup messaging.",
            "Track & Field productizes group bookings far better. Cathedral can package booths, guest lists, and party formats more explicitly.",
            "A weekly event should promise a social behavior, not just a genre. Singles night and trivia are easier to understand than vague nightlife copy.",
            "The venue sells moments people do together; Cathedral should think harder about what guests are doing, not only what they are hearing.",
            "Programming names and repeated rituals matter more than broad 'come party' positioning.",
        ],
        "advantages": [
            "Bar Cathedral has a stronger music-first identity and a more ownable atmosphere.",
            "Cathedral's stained-glass room and sound-and-light positioning feel more distinctive than a games bar.",
            "Cathedral can be more culturally specific and scene-oriented rather than broad-appeal social recreation.",
            "When its calendar is strong, Cathedral can feel more memorable and less generic than Track & Field.",
            "Cathedral does not need to compete on games if it competes more sharply on recurring night identities.",
        ],
        "sources": [
            {"label": "Track & Field official site", "url": "https://www.trackandfieldbar.com/"},
            {"label": "Track & Field reservations and events", "url": "https://www.trackandfieldbar.com/reservations"},
        ],
    },
    "Dance Cave": {
        "address": "529 Bloor St W, Toronto, ON M5S 1Y5",
        "neighbourhood": "The Annex / Bloor West",
        "parent": "Lee's Palace / Dance Cave venue operation",
        "founded": "Dance Cave operates within the Lee's Palace building, which has run as a venue since 1985",
        "website": "leespalace.com",
        "screenshot": None,
        "google_rating": 3.9, "google_reviews": 338,
        "yelp_rating": "n/a", "yelp_reviews": 0,
        "ig_handle": "@thedancecave", "ig_followers": 3641,
        "platforms": "IG, FB", "posts_per_week": "~3.0",
        "positioning": "Heritage alternative dance venue that wins on subcultural credibility, genre specificity, and recurring indie/retro party identity rather than polish or broad-market nightlife appeal.",
        "menus": ["Dance Nights", "Ticketed Events", "Festival Events", "Private Rentals", "Bar Service"],
        "signature_items": [
            "Strong indie, alternative, mod, retro, and dark-wave night identity",
            "The upstairs-club / downstairs-live-venue relationship with Lee's Palace adds credibility and flexibility",
            "Ticketed niche parties and festival tie-ins reinforce scene ownership more than generic nightclub scale",
        ],
        "review_strengths": [
            "Music selection and alternative vibe are the core draw",
            "Historic venue character gives it authenticity newer bars cannot fake",
            "Crowds often describe the room as friendly and scene-driven rather than purely commercial",
            "Recurring niche nights make the programming feel culturally specific",
        ],
        "review_weaknesses": [
            "Accessibility is a real issue because the room is upstairs with no elevator",
            "The venue can feel physically dated and under-invested visually",
            "Some guest complaints focus on cover, staff interactions, or rough edges in the experience",
            "Its appeal is narrower than a broadly programmed downtown nightlife room",
        ],
        "swot": {
            "strengths": [
                "Very strong genre identity and scene credibility",
                "Historic brand equity through the Lee's Palace association",
                "Ticketed themed nights create clearer demand than generic party messaging",
                "Ownable alternative positioning that avoids direct mainstream-club competition",
            ],
            "weaknesses": [
                "Accessibility limitations are structural and significant",
                "The room can feel rougher and less polished than modern nightlife venues",
                "Appeal is narrower and more taste-dependent than a broad downtown lounge",
                "Lower social scale than newer nightlife brands",
            ],
            "opportunities": [
                "Keep leaning into niche-party credibility and heritage storytelling",
                "Turn sold-out themed nights into stronger social proof online",
                "Cross-program more aggressively with adjacent live-music audiences",
                "Use archival or scene-history storytelling to deepen identity",
            ],
            "threats": [
                "Heritage alone does not protect against quality perception drift",
                "If alternative-night demand fragments, the room's narrow identity can become a constraint",
                "Accessibility issues limit audience expansion and some booking opportunities",
                "Newer venues can outperform it on comfort, polish, and service",
            ],
        },
        "learns": [
            "Bar Cathedral should sharpen its recurring-night identities until they are as culturally legible as Dance Cave's indie and retro parties.",
            "Scene ownership matters. Cathedral can win by owning specific communities and sounds rather than staying too broad.",
            "Ticketed or branded themed nights can make the calendar feel more serious and destination-worthy.",
            "Heritage and subculture create memory. Cathedral should develop lore around its own room and recurring nights.",
            "The strongest programming is easy to describe in one sentence; Cathedral should aim for that level of clarity night by night.",
        ],
        "advantages": [
            "Bar Cathedral is more polished, more accessible, and more visually controlled than Dance Cave.",
            "Cathedral can serve a wider downtown audience than a niche alternative room in the Annex.",
            "The sound-and-light pitch at Cathedral can feel more premium when properly programmed.",
            "Cathedral has more room to blend multiple night identities without being trapped in one subculture.",
            "Its hidden, intimate setting can feel more contemporary and curated than Dance Cave's rougher heritage room.",
        ],
        "sources": [
            {"label": "Lee's Palace / Dance Cave", "url": "https://www.leespalace.com/"},
            {"label": "Dance Cave private rentals", "url": "https://www.leespalace.com/private-events"},
        ],
    },
    "Lula Lounge": {
        "address": "1585 Dundas St W, Toronto, ON M6K 1T9",
        "neighbourhood": "Little Portugal / Dundas West",
        "parent": "Co-founded by Jose Ortega (Artistic Director) and Jose Nieves",
        "founded": "2002 (24 years)",
        "website": "lula.ca",
        "positioning": "Toronto's premier Latin/world/jazz live music cultural landmark. Frommer's compares to pre-Castro Havana nightclub.",
        "screenshot": None,
        "google_rating": 4.0, "google_reviews": 1200,
        "yelp_rating": 3.5, "yelp_reviews": 82,
        "ig_handle": "@lulalounge", "ig_followers": 27000, "ig_posts": 2404,
        "platforms": "IG, FB (34K), Twitter", "posts_per_week": "~2.0",
        "menus": ["A La Carte (apps $8-13, mains $19-26)", "Weekend Prix Fixe Dinner+Show ($69/pp)", "Drinks (Mojito ~$9, Pabst ~$4)", "Cuban Fridays", "Salsa Saturdays"],
        "signature_items": [
            "Cuban Fridays — dinner prix fixe + free salsa lesson + live band + DJ",
            "Salsa Saturdays — same format, $20 cover",
            "Cuban Mojito ~$9.30",
            "Miss Lula cocktail (vodka/lychee/pineapple)",
            "Free salsa dance lesson at 9pm",
            "250-person capacity ballroom",
        ],
        "review_strengths": [
            "Pre-Castro Havana atmosphere",
            "World-class Latin/jazz live music",
            "Free salsa lesson is a huge draw",
            "Professional welcoming service",
            "'Treasure' / 'institution' language in reviews",
            "24-year cultural landmark",
        ],
        "review_weaknesses": [
            "Food quality inconsistent — 'amazing venue but food could be better'",
            "Prix fixe ($69) seen as pricey for food quality",
            "Organization/logistics confusion on cover charges",
            "West-end location requires intentional travel",
            "$20 Saturday cover feels steep for casual visits",
        ],
        "swot": {
            "strengths": [
                "24-year cultural institution (NPR, Frommer's profiled)",
                "Owns Latin/salsa/world music niche — no competitor at scale",
                "Dinner-and-show model drives high per-head ($69 prix fixe)",
                "Free dance lessons create stickiness and community",
                "Larger capacity (250-300)",
                "34K Facebook + 27K IG",
            ],
            "weaknesses": [
                "Location friction — off beaten path",
                "Food is the weak link despite being central to revenue",
                "Weekend-heavy programming — weeknights less consistent",
                "Genre-locked to Latin/world — limits broader nightlife appeal",
                "TripAdvisor 3.8 drags tourist discovery",
            ],
            "opportunities": [
                "BC should brand each night like Lula brands Cuban Fridays / Salsa Saturdays",
                "Add participatory elements (comedy workshop, open jam)",
                "Sell tickets through Eventbrite, Fever, Bandsintown",
                "Build OpenTable-equivalent reservation layer",
            ],
            "threats": [
                "Lula's 24-year heritage creates cultural moat",
                "Genre-specific positioning means different audience than BC",
            ],
        },
        "learns": [
            "Brand anchor nights with searchable names — 'Cuban Fridays' is genius. BC should name each night (Sermon Sundays, Confessional Mondays)",
            "Add participatory elements — free dance lesson creates stickiness. BC could explore comedy workshops or open jam sessions",
            "Leverage dinner-and-show model selectively — curated cocktails+show ticket package for special events",
            "Sell tickets through Eventbrite/Fever/Bandsintown for incremental reach",
            "Facebook still matters for 30+ demographics — Lula's 34K FB shows this",
        ],
        "advantages": [
            "Downtown location — walkable from Union Station, hotels, financial district",
            "Higher Google rating (4.3 vs 4.0)",
            "Programming diversity — comedy+open mic+live music+DJs across 7 nights vs genre-locked",
            "Higher drink margins ($15 cocktails vs $9)",
            "Church aesthetic is more Instagrammable than generic basement/hall",
            "IG parity despite being much younger venue (23.4K vs 27K)",
            "No food quality risk — avoids Lula's #1 complaint",
        ],
        "sources": [
            {"label": "Lula Lounge official site", "url": "https://www.lula.ca/"},
            {"label": "Lula Lounge Google reviews", "url": "https://www.google.com/maps/place/Lula+Lounge/"},
        ],
    },
    "Drake Underground": {
        "address": "1150 Queen St W (basement), Toronto, ON M6J 1J3",
        "neighbourhood": "West Queen West",
        "parent": "Drake Hotel Properties (DHP) — also Drake Hotel, Drake Devonshire, Drake Motor Inn, Drake General Store (~6 retail locations)",
        "founded": "2004 (hotel reopened; original building from 1890)",
        "website": "thedrake.ca/thedrakehotel/drake-underground/",
        "positioning": "Legendary Toronto live music venue. Arts-forward, culturally curated tastemaker brand. Discovery engine for about-to-break artists (Billie Eilish, M.I.A., Broken Social Scene alumni).",
        "screenshot": None,
        "google_rating": 4.3, "google_reviews": 200,
        "yelp_rating": 3.5, "yelp_reviews": 40,
        "ig_handle": "@drakeunderground", "ig_followers": 9441, "ig_posts": 500,
        "platforms": "IG, FB, Ticketmaster, Bandsintown, SeatGeek, Songkick", "posts_per_week": "~2.0",
        "menus": ["Bar menu (cocktails ~$10, draft ~$7)", "Happy Hour: $5 beers daily 3-6pm", "Hotel restaurant food available", "Tuesday: $7 Sapporo, $10 sake cocktails", "Monday: steak night + half-price wine"],
        "signature_items": [
            "Alumni: Billie Eilish, Beck, M.I.A., Chromeo, Metric, Broken Social Scene, BadBadNotGood",
            "Dedicated Music & Culture Programming Manager (Duane Bobbsemple)",
            "Multi-format: live music, comedy, poetry slams, film screenings, drag shows, DJ nights, album launches",
            "150-200 standing capacity",
            "$5 happy hour beers (3-6pm daily)",
            "TIFF and Wax Records partnerships",
        ],
        "review_strengths": [
            "Intimate setting creates memorable shows",
            "Crystal clear sound quality",
            "About-to-break artist caliber in a 150-cap room",
            "Trendy, welcoming, artsy-but-not-pretentious",
            "Friendly staff",
            "Elevator access via hotel lobby",
        ],
        "review_weaknesses": [
            "Bar service speed — only 1 bartender at times",
            "Drink quality described as 'poor quality' relative to price",
            "Limited food options",
            "Noise bleed to hotel rooms constrains late-night programming",
            "Pricing feels overpriced for what you get",
        ],
        "swot": {
            "strengths": [
                "Hotel ecosystem subsidization — doesn't need to be independently profitable",
                "20+ year legacy with world-class alumni stories",
                "Dedicated full-time programming manager",
                "Multi-platform ticketing (Ticketmaster, Bandsintown, etc.) creates massive discovery",
                "Cross-venue traffic from hotel/restaurant/lounge",
                "Press partnerships: Billboard Canada, TIFF",
            ],
            "weaknesses": [
                "Basement venue constraints — 150-200 cap, noise bleed",
                "Slow bar service — top complaint",
                "Sub-brand dilution — only 9.4K IG, absorbed into hotel brand",
                "Not independently discoverable on Google — reviews blend with hotel",
                "West-end location far from Financial District",
            ],
            "opportunities": [
                "Get on every ticketing platform — most are free to list",
                "Happy hour gap — $5 beer is a traffic driver BC should counter",
                "Invest in programming identity — named curator/artistic director",
                "Chase one prestige press partnership (blogTO, NOW, Exclaim!)",
                "Private events as subsidy model",
            ],
            "threats": [
                "Hotel ecosystem gives Drake resilience BC can't match",
                "Dedicated programming manager gives first access to emerging talent",
                "Press/media relationships hard to replicate",
            ],
        },
        "learns": [
            "Get on every ticketing platform — Ticketmaster, Bandsintown, Songkick, SeatGeek are free to list and create passive discovery",
            "The happy hour gap is real — Drake's $5 beer feeds the evening pipeline",
            "Invest in programming identity — named curator elevates credibility",
            "The church aesthetic is your Billie Eilish story — mythologize every notable performer",
            "Chase one prestige press partnership for recurring coverage",
            "Private events with dedicated page and inquiry flow subsidize programming nights",
        ],
        "advantages": [
            "Stronger standalone IG following: 23.4K vs 9.4K (2.5x more)",
            "Church aesthetic is unique and Instagrammable — Drake's basement can't match",
            "Downtown location serves different catchment (Financial District, St. Lawrence)",
            "Independence = agility — can pivot without corporate approval",
            "Own Google review identity — 243 reviews vs Drake blended with hotel",
            "No noise-bleed constraint — can program late freely",
            "Multi-format programming already in place",
        ],
        "sources": [
            {"label": "Drake Underground official site", "url": "https://www.thedrake.ca/thedrakehotel/drake-underground/"},
            {"label": "Drake Underground Google reviews", "url": "https://www.google.com/maps/place/Drake+Underground/"},
        ],
    },
}

ELOISE_TEARDOWNS = {
    "Alo": {
        "address": "163 Spadina Ave 3rd Floor, Toronto, ON M5V 2L6",
        "neighbourhood": "Entertainment District",
        "parent": "Alo Food Group / Chef Patrick Kriss",
        "founded": "2015",
        "website": "alorestaurant.com",
        "screenshot": None,
        "google_rating": 4.6, "google_reviews": 1989,
        "yelp_rating": 4.5, "yelp_reviews": 380,
        "ig_handle": "@alorestaurant", "ig_followers": 50000, "ig_posts": None,
        "platforms": "IG", "posts_per_week": "n/a",
        "positioning": "Toronto's flagship Michelin-starred tasting-menu destination, built around highly disciplined French technique, luxury-level service, and a sense of occasion that makes the meal feel ceremonial.",
        "menus": ["Dining Room Tasting Menu", "Bar Tasting Menu", "Wine Pairings", "Cocktails", "Private Dining"],
        "signature_items": [
            "High-precision tasting-menu experience with classically rooted French technique",
            "Exceptional service choreography and polished hospitality as part of the product",
            "Alo Bar and wine program extend the brand beyond one format while preserving prestige",
        ],
        "review_strengths": [
            "Service quality is consistently described as meticulous and world-class",
            "Presentation and pacing make the meal feel like a full event rather than dinner only",
            "Standout dishes and wine pairings build strong special-occasion memory value",
            "The brand has true category authority in Toronto fine dining",
        ],
        "review_weaknesses": [
            "The price point is prohibitive for many guests and narrows frequency",
            "The formality and tasting-menu structure reduce flexibility compared with Eloise's broader use cases",
            "Expectation levels are so high that even small misses feel amplified",
            "It competes on perfection, which can create pressure but also brittleness",
        ],
        "swot": {
            "strengths": [
                "Michelin-star credibility and citywide prestige",
                "Extremely high service standards and memorable luxury hospitality",
                "Powerful chef-led brand with strong destination pull",
                "Clear special-occasion positioning and category leadership",
            ],
            "weaknesses": [
                "Less flexible than Eloise for casual repeat use",
                "Very high price point limits accessibility and frequency",
                "Tasting-menu format narrows guest entry points",
                "Prestige can create emotional distance for some diners",
            ],
            "opportunities": [
                "Continue monetizing the halo through bars, pairings, and secondary formats",
                "Deepen luxury storytelling and occasion-led packages",
                "Use chef and service authority to reinforce category leadership",
                "Convert destination diners into broader brand loyalists",
            ],
            "threats": [
                "Luxury dining is vulnerable to economic softness",
                "Any execution slip is magnified at this reputation level",
                "New Michelin-level entrants can compete for the same headline diner",
                "Special-occasion-only frequency can flatten repeat demand",
            ],
        },
        "learns": [
            "Eloise should study Alo's service choreography more than its tasting-menu structure. The lesson is not to copy luxury formality, but to raise precision.",
            "Prestige is built through consistency of detail. Every touchpoint at Alo reinforces the perception of serious hospitality.",
            "Chef pedigree matters when it is translated into a coherent guest experience, not just used as marketing copy.",
            "Alo shows how a bar, drinks program, and secondary formats can extend the brand without diluting it.",
            "Eloise can borrow the discipline of Alo while staying warmer, more approachable, and more flexible.",
        ],
        "advantages": [
            "Eloise is more flexible for lunch, pre-show dining, and neighborhood repeat visits.",
            "Eloise can feel more approachable and less intimidating for a broader downtown customer.",
            "Its menu allows more choice and easier sharing than a luxury tasting room.",
            "The Esplanade setting and Bar Cart adjacency create a more layered night-out path.",
            "Eloise does not need to compete head-on with Michelin ritual if it owns polished accessibility.",
        ],
        "sources": [
            {"label": "Alo official site", "url": "https://www.alorestaurant.com/"},
            {"label": "Alo Yelp", "url": "https://www.yelp.ca/biz/alo-restaurant-toronto"},
            {"label": "Alo n49", "url": "https://www.n49.com/biz/5242121/alo-on-toronto-163-spadina-ave/"},
        ],
    },
    "Canoe": {
        "address": "66 Wellington St W 54th Floor, Toronto, ON M5K 1H6",
        "neighbourhood": "Financial District",
        "parent": "Oliver & Bonacini Hospitality",
        "founded": "1995",
        "website": "canoerestaurant.com",
        "screenshot": None,
        "google_rating": 4.1, "google_reviews": 670,
        "yelp_rating": 4.1, "yelp_reviews": 784,
        "ig_handle": "@canoe.toronto", "ig_followers": 47000, "ig_posts": None,
        "platforms": "IG", "posts_per_week": "n/a",
        "positioning": "Iconic high-altitude Canadian fine dining restaurant that pairs skyline views, polished business-dining credibility, and seasonal Canadian ingredients with a classic expense-account and celebration market.",
        "menus": ["Lunch", "Dinner", "Dessert", "Cocktails", "Wine", "Private Dining", "Group Dining"],
        "signature_items": [
            "54th-floor skyline views as a core experiential differentiator",
            "Canadian contemporary menu with corporate-dining polish and occasion flexibility",
            "Strong business-entertainment, celebration, and private-dining utility",
        ],
        "review_strengths": [
            "The view is a major driver of destination demand and memory value",
            "Service and ambience read as polished and reliable for premium business dining",
            "The menu balances special-occasion appeal with broad enough choices for groups",
            "Canoe has enduring Toronto relevance and strong name recognition",
        ],
        "review_weaknesses": [
            "The concept can feel corporate or conventional compared with more chef-personal destinations",
            "The view sometimes dominates the conversation over culinary distinctiveness",
            "Price-to-excitement can be questioned when the food feels less surprising than newer peers",
            "Its brand is powerful but less culturally fresh than newer chef-led openings",
        ],
        "swot": {
            "strengths": [
                "Iconic Toronto vantage point and strong celebration appeal",
                "Highly established premium-dining brand",
                "Useful for business dining, client entertainment, and private events",
                "Broad recognition and polished execution",
            ],
            "weaknesses": [
                "Feels more corporate than intimate",
                "The view can overshadow the food proposition",
                "Less chef-distinctive than Toronto's top tasting-menu names",
                "Can read as predictable in a market chasing novelty",
            ],
            "opportunities": [
                "Refresh culinary storytelling to keep the brand contemporary",
                "Use private dining and event business to deepen premium relevance",
                "Leverage iconic status into more digital storytelling",
                "Own corporate and visitor occasions even harder",
            ],
            "threats": [
                "New upscale Toronto restaurants can outcompete on freshness and buzz",
                "Corporate dining budgets can soften during downturns",
                "A strong view is not enough if the food becomes secondary",
                "Legacy brands can drift if they stop evolving culturally",
            ],
        },
        "learns": [
            "Eloise should think more explicitly about occasion ownership. Canoe is easy to book because guests instantly know when and why to use it.",
            "Private dining and business-dining utility can materially strengthen premium restaurants without changing the core concept.",
            "A memorable room or context matters; Eloise should use its own design and pre-show geography more aggressively as a booking reason.",
            "Canoe succeeds because it is legible: premium, polished, and dependable. Eloise should sharpen its own one-sentence promise the same way.",
            "Celebration and client-entertainment positioning should be made easier to understand online.",
        ],
        "advantages": [
            "Eloise feels more current, more intimate, and less corporate than Canoe.",
            "Its menu can be more flexible and personality-driven than a legacy financial-district institution.",
            "Eloise can create a stronger neighborhood and cultural identity than a view-led classic.",
            "The Esplanade context is warmer and more locally textured than the TD Tower experience.",
            "Eloise has more room to evolve quickly because it is not carrying decades of brand convention.",
        ],
        "sources": [
            {"label": "Canoe official site", "url": "https://www.canoerestaurant.com/"},
            {"label": "Canoe Yelp", "url": "https://www.yelp.com/biz/canoe-toronto-2"},
            {"label": "Canoe Restaurantji", "url": "https://www.restaurantji.com/on/toronto/canoe-/"},
        ],
    },
    "SAMMARCO": {
        "address": "4 Front St E, Toronto, ON M5E 1G4",
        "neighbourhood": "Front Street East / St. Lawrence edge",
        "parent": "Independent by Rob Rossi and David Minicucci",
        "founded": "2025",
        "website": "sammarco.ca",
        "screenshot": None,
        "google_rating": 4.8, "google_reviews": 177,
        "yelp_rating": 4.2, "yelp_reviews": 6,
        "ig_handle": "@sammarcotoronto", "ig_followers": 12000, "ig_posts": None,
        "platforms": "IG", "posts_per_week": "n/a",
        "positioning": "Modern Italian steakhouse that merges Michelin-adjacent culinary credibility with glossy room design, seafood luxury cues, and premium dry-aged beef in a downtown special-occasion format.",
        "menus": ["Dinner", "Raw Bar / Seafood", "Steak", "Pasta", "Cocktails", "Wine", "Private Dining"],
        "signature_items": [
            "Italian steakhouse framing rather than generic North American steakhouse language",
            "Seafood towers, premium cuts, and rich sauces creating an overt luxury cue set",
            "Founder halo from Giulietta and Osteria Giulia carries instant culinary credibility",
        ],
        "review_strengths": [
            "The room feels polished, expensive, and occasion-ready",
            "Service and hospitality are repeatedly praised in early reviews",
            "Steak, seafood, and sauce-forward dishes support a premium splurge narrative",
            "The founders' reputation gives the concept immediate trust and buzz",
        ],
        "review_weaknesses": [
            "Price sensitivity shows up quickly when execution slips",
            "The concept risks feeling more luxe than personal if the hospitality weakens",
            "As a newer restaurant, the long-term consistency story is still unproven",
            "It competes in an expensive steakhouse lane where guests expect near-flawless delivery",
        ],
        "swot": {
            "strengths": [
                "Strong founder credibility and immediate market buzz",
                "Luxury room and product cues are very legible",
                "Italian steakhouse positioning is clearer than many contemporary hybrids",
                "Fits celebration and pre-show splurge occasions well",
            ],
            "weaknesses": [
                "New restaurant with a relatively small long-term review base",
                "Very high price expectations create little room for error",
                "Can feel more polished than emotionally warm",
                "Steakhouse competition in Toronto is intense and quality-sensitive",
            ],
            "opportunities": [
                "Convert launch buzz into repeat loyalty and industry credibility",
                "Build stronger signature-dish memory beyond general luxury cues",
                "Deepen wine and private-dining business",
                "Own the Italian-steakhouse lane more distinctly through storytelling",
            ],
            "threats": [
                "Guests compare every high-ticket meal against Toronto's best restaurants",
                "Price criticism becomes damaging quickly at premium steakhouse check averages",
                "Luxury-room competition is crowded downtown",
                "Early hype can fade if signature memory structures are not established",
            ],
        },
        "learns": [
            "Eloise should notice how clearly SAMMARCO signals premium value before a guest even orders: room, menu language, and product cues all align.",
            "Founder credibility works best when it is visible in the concept story. Eloise can use Akhil Hajare's background more sharply.",
            "Luxury restaurants need a few unmistakable memory anchors. Eloise should keep building dishes and moments guests retell.",
            "SAMMARCO shows that proximity competitors can still feel distinct if their luxury lane is easy to understand.",
            "Eloise can learn from the confidence of SAMMARCO's premium positioning without moving into steakhouse rigidity.",
        ],
        "advantages": [
            "Eloise is more versatile and can serve more occasions than a premium Italian steakhouse.",
            "Its menu has more room for contemporary range and chef personality.",
            "Eloise can feel less transactional than a high-ticket steak-and-seafood splurge.",
            "The Bar Cart adjacency creates a stronger full-evening progression than SAMMARCO currently offers.",
            "Eloise can win on warmth and local repeatability while SAMMARCO leans harder into luxe occasion dining.",
        ],
        "sources": [
            {"label": "SAMMARCO official site", "url": "https://www.sammarco.ca/"},
            {"label": "SAMMARCO Yelp", "url": "https://www.yelp.ca/biz/sammarco-toronto"},
            {"label": "SAMMARCO n49", "url": "https://www.n49.com/biz/6599053/sammarco-on-toronto-4-front-st-e/"},
        ],
    },
    "Giulietta": {
        "address": "972 College St, Toronto, ON M6H 1A5",
        "neighbourhood": "College West / Dufferin Grove",
        "parent": "Independent by Rob Rossi, David Minicucci, and team",
        "founded": "2018",
        "website": "giu.ca",
        "screenshot": None,
        "google_rating": 4.5, "google_reviews": 910,
        "yelp_rating": 4.3, "yelp_reviews": 233,
        "ig_handle": "@giulietta972", "ig_followers": None, "ig_posts": None,
        "platforms": "IG", "posts_per_week": "n/a",
        "positioning": "Polished Michelin-recognized Italian neighbourhood destination that combines serious ingredient quality, warm hospitality, and stylish room design without turning into a formal tasting-menu experience.",
        "menus": ["Dinner", "Cocktails", "Wine", "Dessert", "Private Dining / Group Dining"],
        "signature_items": [
            "Refined Italian cooking anchored by crudo, handmade pasta, and large-format mains",
            "A room that feels premium and design-forward without losing neighbourhood warmth",
            "Strong founder credibility from the Rossi / Osteria Giulia orbit gives the brand culinary authority",
        ],
        "review_strengths": [
            "Hospitality and service are often described as polished but still warm",
            "The room feels contemporary, expensive, and desirable without becoming stiff",
            "Ingredient quality and menu restraint reinforce trust in the kitchen",
            "Giulietta has strong date-night and special-occasion pull while still feeling repeatable",
        ],
        "review_weaknesses": [
            "High expectations mean pricing can feel aggressive if the meal misses even slightly",
            "The concept is more disciplined than exuberant, which can limit obvious memory hooks",
            "Its west-end location makes it less immediate for Esplanade occasion traffic",
            "Some of its edge comes from polish and consistency rather than a loud signature ritual",
        ],
        "swot": {
            "strengths": [
                "Michelin recognition and strong culinary credibility",
                "Balanced brand position: premium but not intimidating",
                "Strong service and room design create broad occasion utility",
                "Italian identity is clear without becoming generic red-sauce dining",
            ],
            "weaknesses": [
                "Fewer overt theatrical or experiential hooks than some competitors",
                "Price sensitivity can appear when value expectations are not met",
                "Less geographically relevant to St. Lawrence pre-show traffic",
                "Brand tone is polished but comparatively quiet",
            ],
            "opportunities": [
                "Deepen private dining and celebration positioning",
                "Build stronger digital storytelling around signature dishes and hospitality",
                "Extend founder halo into more ownable branded rituals",
                "Keep converting neighbourhood loyalty into citywide destination relevance",
            ],
            "threats": [
                "Toronto premium Italian is crowded and review-sensitive",
                "If polish slips, the premium narrative weakens quickly",
                "Newer openings can outcompete on novelty or louder luxury cues",
                "Economic softness can compress frequency for premium casual-fine dining",
            ],
        },
        "learns": [
            "Eloise should pay attention to Giulietta's balance. It feels premium and serious without becoming remote or overly formal.",
            "A highly legible room and hospitality style can do a lot of positioning work before the food arrives.",
            "Giulietta shows that Italian influence can be contemporary, disciplined, and city-relevant without reading as either steakhouse or trattoria.",
            "Eloise can sharpen its premium tone by making service, room, and menu language feel more unified.",
            "Guests remember confidence and restraint. Eloise does not need more menu complexity as much as stronger edit and clearer signatures.",
        ],
        "advantages": [
            "Eloise has a more globally inflected menu and can claim a broader culinary point of view.",
            "Its Esplanade location gives it stronger linkage to arena, theatre, and waterfront occasions.",
            "The Eloise plus Bar Cart pairing creates a fuller evening ecosystem than Giulietta alone.",
            "Eloise has more room to build theatrical service moments and special-event energy.",
            "If Eloise sharpens execution, it can feel more distinct rather than simply more polished.",
        ],
        "sources": [
            {"label": "Giulietta official site", "url": "https://giu.ca/"},
            {"label": "Giulietta menus", "url": "https://giu.ca/pages/menus"},
            {"label": "Giulietta Yelp", "url": "https://www.yelp.ca/biz/giulietta-toronto"},
            {"label": "Giulietta Restaurantji", "url": "https://www.restaurantji.com/on/toronto/giulietta-/"},
        ],
    },
}

DOLLYS_TEARDOWNS = {
    "Rock 'N' Horse Saloon": {
        "address": "250 Adelaide St W, 2nd Floor, Toronto, ON M5H 1X6",
        "neighbourhood": "Entertainment District",
        "parent": "MRG Ventures (Matthew Gibbons, founder); Jeff Hathcock listed as current owner",
        "founded": "December 2013",
        "website": "rocknhorsesaloon.com",
        "positioning": "Toronto's original country bar — mechanical bull, line dancing, DJ-driven nightlife. CCMA Canada's Country Bar of the Year 2019.",
        "screenshot": None,
        "google_rating": 4.1, "google_reviews": 1967,
        "yelp_rating": 3.5, "yelp_reviews": 71,
        "ig_handle": "@rocknhorseto", "ig_followers": 16000, "ig_posts": 800,
        "platforms": "IG, FB, TikTok", "posts_per_week": "~2.0",
        "menus": ["Food Menu (corn dogs $4, bison burger $14, fried chicken $17, ribeye $19)", "Drinks (21 draft beers, Beeritas, bourbon cocktails)", "The Porch Rooftop Patio"],
        "signature_items": [
            "Mechanical bull (centerpiece experience)",
            "Line dancing lessons Wed-Sat from 8pm",
            "Cowgirl Fridays (ladies free before 10:30pm)",
            "Giant 'Beeritas' (beer-margarita hybrids)",
            "The Porch rooftop with CN Tower views",
            "CCMA Country Bar of the Year 2019",
        ],
        "review_strengths": [
            "Overall concept — 'a BLAST', country-bar-in-the-city novelty works",
            "Mechanical bull is #1 draw and talking point",
            "Line dancing lessons accessible for beginners",
            "Good for groups, birthdays, bachelorettes",
            "The Porch rooftop patio with CN Tower views",
        ],
        "review_weaknesses": [
            "Bouncer/door staff issues — rude, aggressive, running cover charge scams on first-timers",
            "Cover charge confusion — varies unpredictably, different amounts than posted",
            "Excessive heat/overcrowding — 150 cap on 2nd floor, poor airflow",
            "Food quality — described as 'subpar', an afterthought",
            "Mechanical bull downtime — when it breaks, value proposition collapses",
            "Communication failures — can't reach venue by email or phone",
            "Safety concerns — unresponsive management during incidents",
        ],
        "swot": {
            "strengths": ["12-year first-mover advantage and brand recognition", "Entertainment District location, high foot traffic", "Mechanical bull — unique, shareable", "The Porch rooftop patio", "CCMA award credential", "Established Cowgirl Fridays programming"],
            "weaknesses": ["Tiny capacity (~150) — Dolly's is 6x larger", "2nd floor, no street presence, hard to find", "Stale programming — same formula for 12 years, no live music", "Hospitality failures — bouncer complaints, communication failures", "Food is an afterthought", "No late-night food", "16K IG after 12 years is weak", "Safety perception issues"],
            "opportunities": ["Could respond with renovation or programming refresh", "CCMA relationships could be leveraged", "The Porch rooftop is an underutilized asset"],
            "threats": ["Dolly's 850 capacity unlocks revenue streams Rock N Horse can't touch", "Dolly's female-safety positioning directly exploits bouncer complaints", "Late-night pizza solves a gap they don't address", "Modern 70s aesthetic vs dated saloon look"],
        },
        "learns": [
            "Mechanical bull is proven — Dolly's should consider one but ensure it's always operational",
            "Line dancing lessons from 8pm is the right timing — Dolly's should adopt",
            "Cowgirl Fridays format works but can be done better with genuine hospitality",
            "The Porch rooftop proves the patio opportunity — Dolly's must maximize theirs",
            "Bachelorette package exists but is generic (cow balloons) — Dolly's can build premium tiered packages",
        ],
        "advantages": [
            "Capacity: 850 vs ~150 — nearly 6x larger, unlocks large groups and events",
            "Hospitality-first vs bouncer complaints — direct positioning contrast",
            "Street-level presence vs hidden 2nd floor",
            "Late-night pizza vs no late-night food",
            "Modern 70s aesthetic vs dated saloon",
            "Live music programming vs DJ-only",
            "Female safety as brand pillar vs safety concerns in reviews",
            "Urban + traditional country programming vs single country format",
        ],
    },
    "Paris Texas": {
        "address": "461 King Street West, Unit A, Toronto, ON M5V 1K4",
        "neighbourhood": "King West",
        "parent": "Joint venture: Municipal Goods (Gurpreet Kailley, Jason Bitton, Rahul Raina) + Liberty Entertainment Group (Nick & Luca Di Donato)",
        "founded": "Mid-2023 (replaced Arcane nightclub)",
        "website": "paristexas.ca",
        "positioning": "Toronto's premier sports and country bar — upscale 'grand saloon' blending Parisian opulence with Texan charm. Chef-driven food, $19-28 cocktails, dress code.",
        "screenshot": None,
        "google_rating": 4.7, "google_reviews": 1675,
        "yelp_rating": 3.5, "yelp_reviews": 14,
        "ig_handle": "@paristexasparistexas", "ig_followers": 14000, "ig_posts": 500,
        "platforms": "IG, TikTok (1.1M+ UGC tag views), Eventbrite", "posts_per_week": "~2.5",
        "menus": ["Chef Eric Phung menu (cornbread $10, fish tacos $21, chicken & waffles $28, ribeye $80)", "Cocktails ($19-28, happy hour $10)", "Happy Hour ($5 domestic beer, $5 rail drinks, $7 apps)", "Sunday Brunch (11:30am)"],
        "signature_items": [
            "'Hold The Line' free line dancing Thursdays (flagship event)",
            "Expansive patio with CN Tower views, cabanas, palm trees",
            "Chef-driven menu by Eric Phung",
            "$5 happy hour domestics",
            "Dress code: fashionable attire, no sneakers",
            "500-person capacity",
            "Liberty Entertainment Group backing",
        ],
        "review_strengths": [
            "Gorgeous space — exposed brick, upscale feel, country aesthetic done well",
            "Patio with CN Tower views, cabanas, outdoor bar",
            "Food quality praised — buffalo cauliflower, chicken & waffles, fajitas",
            "Specific servers called out by name positively",
            "Thursday line dancing — viral, fun, accessible",
            "Happy hour value — $5 beers, $10 cocktails for King West",
        ],
        "review_weaknesses": [
            "Bouncer conduct — racial discrimination allegations, 'xenophobic bullies', TikTok pages dedicated to incidents",
            "Management non-responsiveness — GM dismissed complaints, 'protected the thugs he calls his employees'",
            "Bathroom cleanliness — 'floors STILL covered in piss', multi-year unresolved issue",
            "Watered-down cocktails — 'juice-heavy', 'light on alcohol' at $19-28/drink",
            "Skews young (21-24) — 'bougie Rock N Horse without the bull'",
            "Sneaker ban / dress code friction — excludes casual visitors",
        ],
        "swot": {
            "strengths": ["3-year established brand, 1,675 Google reviews, 4.7 rating", "Liberty Entertainment Group + Municipal Goods — deep pockets", "King West foot traffic and visibility", "Chef-driven food gives culinary credibility", "CN Tower patio", "Thursday line dancing franchise"],
            "weaknesses": ["Bouncer/discrimination complaints — brand cancer, documented across platforms", "Watered-down $22 cocktails — trust betrayal", "Bathroom filth — multi-year unresolved", "500 cap — turns people away by 10:30pm", "Skews 21-24 — loses higher-spending 25-35 demo", "Dress code friction — contradicts 'come have fun' country energy", "Only one real weekly anchor (Thursday)"],
            "opportunities": ["Could expand programming if threatened", "Liberty Group resources enable fast pivots", "TikTok UGC engine could be amplified with paid spend"],
            "threats": ["Dolly's 'not pretentious' positioning directly attacks PT's biggest weakness", "Dolly's 850 cap is 70% larger", "Dolly's older demo (25-35) has higher spending power", "Dolly's female-safety messaging exploits bouncer reputation", "Late-night pizza is differentiated and on-brand vs $80 ribeye", "Urban + traditional country mix broadens appeal"],
        },
        "learns": [
            "Happy hour structure ($5 beer, $10 cocktails) is smart for early-evening funnel — Dolly's should match or beat",
            "Chef-driven food is NOT the model for Dolly's — own the casual/pizza lane instead",
            "Patio with views is non-negotiable — Dolly's must maximize their outdoor space",
            "'Hold The Line' Thursday proves one branded weekly event can drive awareness — Dolly's needs multiple",
            "Dress code is a friction point — Dolly's 'no dress code' is a direct differentiator",
            "TikTok UGC (1.1M tag views) proves the content engine potential of country bars — Dolly's must be TikTok-native from Day 1",
        ],
        "advantages": [
            "'Not pretentious' vs 'bougie' — fundamentally different positioning that's more inclusive",
            "Honest drinks at $14-18 vs watered-down $22 cocktails",
            "Clean washrooms as a brand feature vs years of bathroom complaints",
            "No dress code vs sneaker ban",
            "850 vs 500 capacity — no more getting turned away at 10:30",
            "25-35 demo vs 21-24 — higher LTV, more disposable income",
            "Hospitality-first vs bouncer discrimination allegations",
            "The Esplanade is a fresh canvas vs saturated King West",
            "Multiple weekly programming anchors vs one Thursday event",
        ],
    },
    "Rodeo Dive": {
        "address": "600 King Street West, Toronto, ON M5V 1M3",
        "neighbourhood": "King West / Portland Square",
        "parent": "INK Entertainment / Portland Square",
        "founded": "Late 2025 / emerging concept",
        "website": "portlandsquareto.com",
        "positioning": "Country-sports bar and western-coded nightlife room inside Portland Square. Strong operator backing, but still defining whether it is a real country bar, a sports bar, or a themed downtown hangout.",
        "screenshot": None,
        "google_rating": None, "google_reviews": None,
        "yelp_rating": None, "yelp_reviews": None,
        "ig_handle": "@rodeodiveto", "ig_followers": 3000, "ig_posts": None,
        "platforms": "IG, TikTok", "posts_per_week": "~2.0",
        "menus": [
            "Country-sports-bar positioning with beer, cocktails, and shareable food implied",
            "Portland Square ecosystem suggests strong event and group-booking crossover",
        ],
        "signature_items": [
            "INK-backed launch credibility",
            "Portland Square visibility and cross-traffic",
            "Country-sports crossover angle",
            "Downtown group-night potential",
        ],
        "review_strengths": [
            "Launch buzz and curiosity factor still work in its favour",
            "Operator polish and downtown location give it immediate credibility",
            "Potential to attract both sports groups and country-curious nightlife traffic",
        ],
        "review_weaknesses": [
            "Identity is still blurry — sports bar, country bar, or themed nightlife room",
            "No deeply owned weekly ritual yet in the public-facing brand",
            "Operator-backed polish can read as generic if the concept lacks authenticity",
            "No obvious female-safety or hospitality-first differentiation",
            "Still too new to have the trust and memory structure of a true institution",
        ],
        "swot": {
            "strengths": ["Strong operator backing", "King West visibility", "Group-night and event potential", "Can move quickly with marketing and programming support"],
            "weaknesses": ["Unclear identity", "No meaningful proof of repeat demand yet", "Less obviously female-forward than Dolly's", "No known signature ritual strong enough to own the category"],
            "opportunities": ["Could scale fast if one weekly franchise takes off", "Portland Square ecosystem enables bigger collaboration and event plays", "Can still reposition while the market is learning the brand"],
            "threats": ["Dolly's can claim the 'real' country lane before Rodeo Dive settles its identity", "Dolly's hospitality-first positioning is a clearer emotional offer", "A bigger dedicated room on The Esplanade can make Rodeo feel like a side concept"],
        },
        "learns": [
            "Operator backing matters, but a nightlife concept still needs one-sentence clarity guests can repeat",
            "Country-sports crossover is useful, but Dolly's should stay country-first rather than sports-first",
            "Downtown visibility and event tie-ins are worth stealing where possible",
            "New concepts need a recognizable weekly franchise quickly or they drift into generic nightlife",
        ],
        "advantages": [
            "Dolly's has a much clearer emotional promise: female-forward, safe, hospitality-first country nightlife",
            "Dolly's is not trying to split itself between country and sports-bar identity",
            "The Esplanade gives Dolly's a cleaner opportunity to own destination-country positioning",
            "A larger dedicated room and line-dancing core can make Dolly's feel more authoritative and less experimental",
        ],
        "sources": [
            {"label": "Portland Square", "url": "https://portlandsquareto.com/"},
            {"label": "Rodeo Dive Instagram", "url": "https://www.instagram.com/rodeodiveto/"},
            {"label": "Toronto Life Portland Square coverage", "url": "https://torontolife.com/food/eight-new-bars-restaurants-portland-square/"},
        ],
    },
    "Badlands": {
        "address": "190 Ossington Avenue, Toronto, ON M6J 2Z7",
        "neighbourhood": "Ossington",
        "parent": "Independent single-venue concept",
        "founded": "2025",
        "website": "https://www.instagram.com/badlandsgoodtimes/",
        "positioning": "Smaller, cooler neighbourhood-country room on Ossington. More indie, more local, and less bachelorette-scale than the King West country entries.",
        "screenshot": None,
        "google_rating": None, "google_reviews": None,
        "yelp_rating": None, "yelp_reviews": None,
        "ig_handle": "@badlandsgoodtimes", "ig_followers": 1074, "ig_posts": None,
        "platforms": "IG", "posts_per_week": "~2.0",
        "menus": [
            "Neighbourhood bar menu orientation rather than large-format nightlife food program",
            "Country-coded drinks and casual food support the vibe more than they define it",
        ],
        "signature_items": [
            "Ossington neighbourhood credibility",
            "Smaller-room intimacy",
            "Country aesthetic filtered through a cooler downtown lens",
            "Good-times rather than high-gloss party positioning",
        ],
        "review_strengths": [
            "Feels more local and less corporate than bigger downtown nightlife rooms",
            "Smaller format can feel more authentic and less intimidating",
            "Neighbourhood positioning gives it date-night and casual-repeat relevance",
        ],
        "review_weaknesses": [
            "Scale ceiling is low relative to Dolly's occasion strategy",
            "Does not naturally own bachelorettes or big group celebrations",
            "Smaller room limits revenue streams and the sense of event spectacle",
            "Could get trapped as a 'cool vibe' bar rather than a must-visit destination",
        ],
        "swot": {
            "strengths": ["Ossington cool factor", "Neighbourhood intimacy", "Country personality without obvious cheese", "Can feel more authentic than corporate-backed entries"],
            "weaknesses": ["Low scale", "Weaker group-booking economics", "No obvious category-defining ritual yet", "Less likely to dominate broad GTA country demand"],
            "opportunities": ["Can deepen local loyalty and music credibility", "Could own the indie-country lane if disciplined", "Neighbourhood repeat traffic can outperform hype if nurtured"],
            "threats": ["Dolly's can dominate the large-group and bachelorette lane immediately", "A stronger content engine from Dolly's could make Badlands feel too small to matter citywide", "Country competitors with more scale can out-shout it"],
        },
        "learns": [
            "There is room for a country bar that feels cooler and more local, not only louder and bigger",
            "Ossington proves that aesthetic discipline matters — Dolly's should not feel like generic theme decor",
            "Neighbourhood intimacy is attractive, so Dolly's needs smaller in-room zones that still feel personal inside a big room",
            "Badlands is a reminder that not every country guest wants a mega-party every time",
        ],
        "advantages": [
            "Dolly's can own the citywide destination lane while Badlands stays neighbourhood-scale",
            "Dolly's group packages, live programming, and pizza window create more reasons to choose it for planned occasions",
            "Dolly's safety positioning and hospitality-first service promise are sharper and more commercially legible",
            "A larger room allows Dolly's to create multiple moods instead of one small-room vibe",
        ],
        "sources": [
            {"label": "Badlands Instagram", "url": "https://www.instagram.com/badlandsgoodtimes/"},
            {"label": "The Corner Toronto listing", "url": "https://www.thecorner.io/listings/badlands"},
            {"label": "Apple Maps listing", "url": "https://maps.apple.com/place?auid=2858995336528685910"},
        ],
    },
}

VENUE_TEARDOWNS = {"Scotland Yard": SY_TEARDOWNS, "Bar Cart": BAR_CART_TEARDOWNS, "Bar Cathedral": BC_TEARDOWNS, "Eloise": ELOISE_TEARDOWNS, "Old Spaghetti Factory": OSF_TEARDOWNS, "Dolly's": DOLLYS_TEARDOWNS}
VENUE_SOCIAL_AUDIT = {"Scotland Yard": SY_SOCIAL_AUDIT, "Bar Cart": BAR_CART_COMPETITOR_AUDIT, "Bar Cathedral": BC_SOCIAL_AUDIT, "Eloise": ELOISE_SOCIAL_AUDIT, "Dolly's": DOLLY_SOCIAL_AUDIT, "Old Spaghetti Factory": OSF_SOCIAL_AUDIT}
VENUE_TEARDOWN_BENCHMARKS = {
    "Bar Cathedral": pd.Series(
        {
            "Name": "Bar Cathedral",
            "IG Followers": 23400,
            "Google Rating": 4.3,
            "Google Reviews": 243,
            "Platforms": "IG, FB",
            "Est. Posts/Week": "~4.5",
        }
    ),
    "Eloise": pd.Series(
        {
            "Name": "Eloise",
            "IG Followers": 4311,
            "Total Posts": 93,
            "Google Rating": 4.6,
            "Google Reviews": 121,
            "Platforms": "IG",
            "Est. Posts/Week": "n/a",
        }
    ),
    "Dolly's": pd.Series(
        {
            "Name": "Dolly's",
            "IG Followers": None,
            "Google Rating": None,
            "Google Reviews": None,
            "Platforms": "TBD",
            "Est. Posts/Week": "n/a",
        }
    ),
}

render_brand_header()

primary_sections = ["Portfolio", *VENUES.keys()]
active_page = st.segmented_control(
    "Workspace",
    primary_sections,
    default="Portfolio",
    width="stretch",
    label_visibility="collapsed",
)

sidebar_logo = find_logo("Esplanade Restaurants")
if sidebar_logo:
    st.sidebar.image(str(sidebar_logo), use_container_width=True)
st.sidebar.markdown("**Esplanade Restaurants**")
st.sidebar.caption("Competitive Analysis Dashboard")
st.sidebar.divider()

st.sidebar.title("Filters")
st.sidebar.caption("Contextual filters for the current view")

selected_tiers = list(TIER_LABELS.keys())
search_term = ""
selected_research_categories = list(RESEARCH_CATEGORY_COLUMNS.keys())
selected_teardown = None
selected_teardowns = []

_PRICING_FRAMEWORKS = {
    "Scotland Yard": ("1 cheapest regular draft pint + 1 burger", "No draft beer or no burger on menu — closest equivalent substituted"),
    "Bar Cart": ("1 signature cocktail + 1 cheapest protein appetizer", "Drinks-only venue with no food menu — cocktail only"),
    "Bar Cathedral": ("1 signature cocktail + 1 cheapest regular draft beer", "No cocktails served — most popular drink substituted"),
    "Eloise": ("1 cheapest protein appetizer (shared) + 1 signature main course + 1 cheapest glass of wine", "No wine by the glass — cheapest cocktail substituted"),
    "Dolly's": ("1 domestic beer pint (20oz pref) + 1 vodka soda + 1 tequila shot", "No draft domestic — large can substituted and noted. Shot pricing unavailable — estimated from spirit menu."),
    "Old Spaghetti Factory": ("1 complete bundled meal + 1 cheapest regular draft beer", "Competitor doesn't bundle — entree + side/salad + drink priced separately"),
}

if active_page == "Portfolio":
    # --- Build master competitor lookup ---
    _all_competitors = {}  # name -> {venue, tier, concept, why, teardown data if exists}
    for venue_name in VENUES:
        for tier_key, tier_label in [("Local (1–2 km)", "Local"), ("City-wide (Toronto)", "City-wide"), ("Global", "Global")]:
            if tier_key not in COMPETITORS[venue_name]:
                continue
            for _, row in COMPETITORS[venue_name][tier_key].iterrows():
                cname = row.get("Name", "")
                if not cname:
                    continue
                entry = {
                    "venue": venue_name,
                    "tier": tier_label,
                    "location": row.get("Location", ""),
                    "concept": row.get("Concept", ""),
                    "why": row.get("Why Competitor", ""),
                }
                # Attach teardown data if exists
                if venue_name in VENUE_TEARDOWNS and cname in VENUE_TEARDOWNS[venue_name]:
                    entry["teardown"] = VENUE_TEARDOWNS[venue_name][cname]
                # Attach pricing if exists
                if venue_name in COMPETITOR_PRICING:
                    _pricing_df = COMPETITOR_PRICING[venue_name]
                    _price_match = _pricing_df[_pricing_df["Name"] == cname]
                    if not _price_match.empty:
                        entry["price"] = _price_match.iloc[0].get("Total (CAD)", "")
                        entry["price_breakdown"] = _price_match.iloc[0].get("Breakdown", "")
                if cname not in _all_competitors:
                    _all_competitors[cname] = entry
                # If same name appears under multiple venues, keep first but note

    with st.sidebar.expander("Portfolio Filters", expanded=True):
        search_term = st.text_input("Search competitors", placeholder="Type a name...", key="portfolio_search")
        _portfolio_venue_filter = st.selectbox("Filter by venue", ["All"] + list(VENUES.keys()), key="portfolio_venue")

    st.markdown("## Portfolio Overview")

    # Summary table
    summary_data = []
    for venue_name in VENUES:
        row = {"Venue": venue_name}
        total = 0
        for tier in TIER_LABELS:
            count = len(COMPETITORS[venue_name][tier])
            row[tier] = count
            total += count
        row["Total"] = total
        row["Teardowns"] = len(VENUE_TEARDOWNS.get(venue_name, {}))
        summary_data.append(row)

    summary_df = pd.DataFrame(summary_data)
    show_table(summary_df)

    st.divider()
    st.plotly_chart(portfolio_stacked_bar(VENUES, COMPETITORS, TIER_LABELS), use_container_width=True)

    st.divider()

    # --- Competitors organized by venue ---
    st.markdown("### Competitors by Venue")

    _venues_to_show = [_portfolio_venue_filter] if _portfolio_venue_filter != "All" else list(VENUES.keys())

    # Build social audit lookup for Google/IG data on non-teardown competitors
    # Master lookup: social audit + teardowns + static lookup file
    from data.competitor_google_ig_lookup import COMPETITOR_LOOKUP as _STATIC_LOOKUP

    _social_lookup = {}
    for _sa_venue, _sa_df in VENUE_SOCIAL_AUDIT.items():
        for _, _sa_row in _sa_df.iterrows():
            _sa_name = str(_sa_row.get("Name", ""))
            if _sa_name and _sa_name not in _social_lookup:
                _social_lookup[_sa_name] = _sa_row

    for venue_name in _venues_to_show:
        # Collect all competitors for this venue
        _venue_comps = []
        for tier_key in TIER_LABELS:
            for _, row in COMPETITORS[venue_name][tier_key].iterrows():
                cname = row.get("Name", "")
                _tier_short = "Local" if "Local" in tier_key else ("City-wide" if "City" in tier_key else "Global")
                _has_teardown = venue_name in VENUE_TEARDOWNS and cname in VENUE_TEARDOWNS[venue_name]
                _venue_comps.append({
                    "name": cname,
                    "tier": _tier_short,
                    "location": row.get("Location", ""),
                    "concept": row.get("Concept", ""),
                    "has_teardown": _has_teardown,
                })

        # Apply search filter
        if search_term:
            _venue_comps = [c for c in _venue_comps if search_term.lower() in c["name"].lower() or search_term.lower() in c.get("concept", "").lower()]

        if not _venue_comps:
            continue

        _total_comps = len(_venue_comps)
        _total_teardowns = sum(1 for c in _venue_comps if c["has_teardown"])
        _venue_label = f"{venue_name}  —  {_total_comps} competitors  |  {_total_teardowns} teardowns"

        with st.expander(_venue_label, expanded=False):
            st.caption(f"{VENUES[venue_name]['concept']}")

            # Quick summary table
            _summary_rows = [[c["name"], c["tier"], c["location"], c["concept"], "Yes" if c["has_teardown"] else "—"] for c in _venue_comps]
            _summary_df = pd.DataFrame(_summary_rows, columns=["Name", "Tier", "Location", "Concept", "Teardown"])
            show_table(_summary_df)

            st.divider()

            # Expandable competitor profiles
            for comp in _venue_comps:
                cname = comp["name"]
                _td = VENUE_TEARDOWNS.get(venue_name, {}).get(cname)
                _sa = _social_lookup.get(cname)

                # Get Google rating and IG from teardown > social audit > static lookup
                _google = "—"
                _ig_label = "—"
                if _td:
                    _g_rating = _td.get("google_rating", "")
                    _g_reviews = _td.get("google_reviews", "")
                    if _g_rating:
                        _google = f"{_g_rating}" + (f" / {_g_reviews:,}" if isinstance(_g_reviews, int) else "")
                    _ig_val = _td.get("ig_followers")
                    if _ig_val:
                        _ig_label = f"{_ig_val:,}" if isinstance(_ig_val, int) else str(_ig_val)
                elif _sa is not None:
                    _g_rating = _sa.get("Google Rating", "")
                    _g_reviews = _sa.get("Google Reviews", "")
                    if _g_rating and str(_g_rating) != "nan":
                        _google = f"{_g_rating}" + (f" / {int(_g_reviews):,}" if _g_reviews and str(_g_reviews) != "nan" else "")
                    _ig_val = _sa.get("IG Followers", "")
                    if _ig_val and str(_ig_val) != "nan":
                        _ig_label = _sa.get("IG Followers Display", str(_ig_val)) if "IG Followers Display" in _sa.index else (f"{int(_ig_val):,}" if isinstance(_ig_val, (int, float)) else str(_ig_val))

                # Fallback to static lookup
                if _google == "—" or _ig_label == "—":
                    _static = _STATIC_LOOKUP.get(cname)
                    if _static:
                        _sr, _sv, _sh, _sf = _static
                        if _google == "—" and _sr is not None:
                            _google = f"{_sr}" + (f" / {_sv:,}" if _sv else "")
                        if _ig_label == "—" and _sf is not None:
                            _ig_label = f"{_sf:,}" if isinstance(_sf, int) else str(_sf)

                _comp_label = f"{cname}  |  {comp['tier']}  |  Google {_google}  |  {_ig_label} IG"

                with st.expander(_comp_label):
                    if _td:
                        _prof_col1, _prof_col2 = st.columns(2)
                        with _prof_col1:
                            st.markdown(f"**Address:** {_td.get('address', '—')}")
                            st.markdown(f"**Owner:** {_td.get('parent', '—')}")
                            st.markdown(f"**Founded:** {_td.get('founded', '—')}")
                            st.markdown(f"**Positioning:** {_td.get('positioning', '—')}")
                        with _prof_col2:
                            st.markdown(f"**Google:** {_google} reviews")
                            st.markdown(f"**Yelp:** {_td.get('yelp_rating', '—')}")
                            _ig_handle = _td.get('ig_handle', '—')
                            st.markdown(f"**Instagram:** {_ig_handle} ({_ig_label} followers)")
                            st.markdown(f"**Platforms:** {_td.get('platforms', '—')}")
                            st.markdown(f"**Posts/week:** {_td.get('posts_per_week', '—')}")

                        if venue_name in COMPETITOR_PRICING:
                            _p_df = COMPETITOR_PRICING[venue_name]
                            _p_match = _p_df[_p_df["Name"] == cname]
                            if not _p_match.empty:
                                _p_row = _p_match.iloc[0]
                                st.markdown(f"**Pricing Basket:** {_p_row.get('Total (CAD)', '—')} — {_p_row.get('Breakdown', '')}")

                        _sigs = _td.get("signature_items", [])
                        if _sigs:
                            st.markdown("**Signature Items**")
                            for s in _sigs[:5]:
                                st.markdown(f"- {s}")

                        _weaknesses = _td.get("review_weaknesses", [])
                        if _weaknesses:
                            st.markdown("**Top Complaints**")
                            for _ci, _cw in enumerate(_weaknesses[:3], 1):
                                st.error(f"{_ci}. {_cw}", icon="⚠️")

                        _strengths = _td.get("review_strengths", [])
                        if _strengths:
                            st.markdown("**Top Strengths**")
                            for _si, _sw in enumerate(_strengths[:3], 1):
                                st.success(f"{_si}. {_sw}", icon="💪")

                    else:
                        _prof_col1, _prof_col2 = st.columns(2)
                        with _prof_col1:
                            st.markdown(f"**Location:** {comp.get('location', '—')}")
                            st.markdown(f"**Concept:** {comp.get('concept', '—')}")
                            st.markdown(f"**Why Competitor:** {comp.get('why', '—')}")
                        with _prof_col2:
                            st.markdown(f"**Google:** {_google}")
                            _static_entry = _STATIC_LOOKUP.get(cname)
                            _ig_handle_display = _static_entry[2] if _static_entry and _static_entry[2] else "—"
                            st.markdown(f"**Instagram:** {_ig_handle_display} ({_ig_label} followers)")

                        if venue_name in COMPETITOR_PRICING:
                            _p_df = COMPETITOR_PRICING[venue_name]
                            _p_match = _p_df[_p_df["Name"] == cname]
                            if not _p_match.empty:
                                _p_row = _p_match.iloc[0]
                                st.markdown(f"**Pricing Basket:** {_p_row.get('Total (CAD)', '—')} — {_p_row.get('Breakdown', '')}")

                        st.caption("No teardown available yet.")
                    st.caption("No teardown available yet for this competitor.")

                    if venue_name in COMPETITOR_PRICING:
                        _p_df = COMPETITOR_PRICING[venue_name]
                        _p_match = _p_df[_p_df["Name"] == cname]
                        if not _p_match.empty:
                            _p_row = _p_match.iloc[0]
                            st.markdown(f"**Pricing Basket:** {_p_row.get('Total (CAD)', '—')} — {_p_row.get('Breakdown', '')}")

        st.divider()

    # --- LOCAL SEARCH VISIBILITY ---
    st.divider()
    st.markdown("### Local Search Visibility & Google Maps Audit")
    st.caption("How each venue performs in Google Maps / local pack results for high-intent discovery searches. April 2026.")

    # Scorecard
    def _grade_color(val):
        colors = {"A+": "#166534", "A": "#166534", "B+": "#1a5632", "B": "#1a5632", "B-": "#1a5632",
                  "C+": "#854d0e", "C": "#854d0e", "C-": "#854d0e", "D+": "#991b1b", "D": "#991b1b", "F": "#7f1d1d"}
        bg = colors.get(val, "")
        if bg:
            return f"background-color: {bg}; color: white; font-weight: bold; text-align: center"
        return ""

    def _review_color(val):
        try:
            n = int(val)
        except (ValueError, TypeError):
            return ""
        if n < 200:
            return "background-color: #7f1d1d; color: #fca5a5; font-weight: bold"
        if n < 1000:
            return "background-color: #854d0e; color: #fde68a; font-weight: bold"
        return "background-color: #166534; color: #86efac; font-weight: bold"

    scorecard_display = LOCAL_SEARCH_AUDIT[["Venue", "Google Rating", "Google Reviews", "Keyword Visibility", "Grade", "Strongest Keywords", "Critical Gaps"]].copy()
    styled_scorecard = scorecard_display.style.map(_grade_color, subset=["Grade"]).map(_review_color, subset=["Google Reviews"])
    st.dataframe(styled_scorecard, use_container_width=True, hide_index=True, height=240)

    # Key findings
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        st.error("**Review Volume Crisis** — Bar Cart (<50), Eloise (~121), and Bar Cathedral (~130) have critically low Google reviews. Competitors have 7–40x more. This is the #1 reason they are invisible in Google Maps.", icon="🔴")
        st.warning("**Nobody owns 'St. Lawrence Market'** — All 5 venues are within a 5-min walk but none surface for 'near St. Lawrence Market' queries. HOTHOUSE and Cafe Oro own those searches.", icon="⚠️")
    with col_f2:
        st.error("**Bar Cart is non-existent online** — Zero keyword visibility, no TripAdvisor, no Yelp listing, name collides with furniture results. Not on a single 2026 'best bar' list.", icon="🔴")
        st.info("**OSF + SY are solid on fundamentals** — high review volume and own their branded keywords, but both miss category and proximity searches they should win.", icon="ℹ️")

    # Priority actions
    st.markdown("#### Priority Actions by Venue")
    actions_display = LOCAL_SEARCH_AUDIT[["Venue", "Grade", "Priority Actions"]].copy()
    show_table(actions_display)

    # Keyword detail (expandable)
    with st.expander("Keyword Ranking Detail (all venues, all keywords)"):
        venue_filter = st.multiselect("Filter by venue", options=LOCAL_SEARCH_KEYWORDS["Venue"].unique().tolist(), default=LOCAL_SEARCH_KEYWORDS["Venue"].unique().tolist(), key="lsa_venue_filter")
        filtered_kw = LOCAL_SEARCH_KEYWORDS[LOCAL_SEARCH_KEYWORDS["Venue"].isin(venue_filter)]

        def _rank_color(val):
            if val and val.startswith("#1"):
                return "background-color: #166534; color: #86efac; font-weight: bold"
            if val and val.startswith(("#2", "#3", "~#2", "~#3")):
                return "background-color: #1a5632; color: #bbf7d0"
            if val == "Partial":
                return "background-color: #854d0e; color: #fde68a"
            if val == "Absent":
                return "background-color: #7f1d1d; color: #fca5a5"
            return ""

        styled_kw = filtered_kw.style.map(_rank_color, subset=["Rank"])
        st.dataframe(styled_kw, use_container_width=True, hide_index=True, height=500)
        absent_count = (filtered_kw["Rank"] == "Absent").sum()
        total_count = len(filtered_kw)
        st.caption(f"{absent_count} of {total_count} keyword–venue combinations are absent from search results ({absent_count * 100 // total_count}%)")

elif active_page and active_page in VENUES:
    selected_venue = active_page
    venue = VENUES[selected_venue]

    venue_sections = ["Summary", "Competitors", "Pricing"]
    _has_research = selected_venue in VENUE_RESEARCH_TABLES
    _has_teardown_complaints = selected_venue in VENUE_TEARDOWNS and len(VENUE_TEARDOWNS[selected_venue]) > 0
    if _has_research or _has_teardown_complaints:
        venue_sections.append("Research")
    if selected_venue in VENUE_SOCIAL_AUDIT:
        venue_sections.append("Social")
    if selected_venue in VENUE_TEARDOWNS and len(VENUE_TEARDOWNS[selected_venue]) > 0:
        venue_sections.append("Teardowns")
    if selected_venue == "Eloise":
        venue_sections.append("Fixed Price Menu")
        venue_sections.append("Demand")
        venue_sections.append("Awards")
    if selected_venue == "Dolly's":
        venue_sections.append("Strategy")
    if selected_venue == "Old Spaghetti Factory":
        venue_sections.append("Menu")
    venue_section = st.segmented_control(
        f"{selected_venue} sections",
        venue_sections,
        default=venue_sections[0],
        width="stretch",
        label_visibility="collapsed",
    )

    with st.sidebar.expander("View Filters", expanded=venue_section != "Summary"):
        if venue_section == "Competitors":
            selected_tiers = st.pills(
                "Tiers",
                list(TIER_LABELS.keys()),
                selection_mode="multi",
                default=list(TIER_LABELS.keys()),
                width="stretch",
            )
            selected_tiers = selected_tiers or list(TIER_LABELS.keys())
            search_term = st.text_input("Search competitors", placeholder="Type a name...", key=f"{selected_venue}_search")
        elif venue_section == "Research" and selected_venue in VENUE_RESEARCH_TABLES:
            selected_research_categories = st.pills(
                "Categories",
                list(RESEARCH_CATEGORY_COLUMNS.keys()),
                selection_mode="multi",
                default=list(RESEARCH_CATEGORY_COLUMNS.keys()),
                width="stretch",
            )
            selected_research_categories = selected_research_categories or list(RESEARCH_CATEGORY_COLUMNS.keys())
        elif venue_section == "Teardowns" and selected_venue in VENUE_TEARDOWNS:
            _td_names = list(VENUE_TEARDOWNS[selected_venue].keys())
            selected_teardowns = st.pills(
                "Competitor Teardowns",
                _td_names,
                selection_mode="multi",
                default=_td_names,
                width="stretch",
            )
            selected_teardowns = selected_teardowns or _td_names
        else:
            st.caption("No filters for this section.")

    _has_logo = find_logo(selected_venue) is not None
    if _has_logo:
        left_pad, center_logo, right_pad = st.columns([1, 2, 1])
        with center_logo:
            render_venue_logo(selected_venue)
        st.caption(f"Viewing: {venue_section}")
    else:
        st.markdown(f"## {selected_venue}")
        st.caption(f"Viewing: {venue_section}")

    if venue_section == "Summary":
        st.markdown(f"**Concept:** {venue['concept']}")
        col1, col2 = st.columns(2)
        col1.metric("Price Point", venue["price"])
        total = sum(len(COMPETITORS[selected_venue][t]) for t in TIER_LABELS)
        col2.metric("Total Competitors", total)

        st.markdown("### Available Analysis")
        analysis_rows = [
            ["Competitors", "Yes", "Tiered citywide and local competitor set"],
            ["Pricing", "Yes", "Standardized price basket comparison"],
            ["Research", "Yes" if selected_venue in VENUE_RESEARCH_TABLES else "No", "Spreadsheet-backed structured competitor notes"],
            ["Social", "Yes" if selected_venue in VENUE_SOCIAL_AUDIT else "No", "Social presence, cadence, and review signals"],
            ["Fixed Price Menu", "Yes" if selected_venue == "Eloise" else "No", "Peak-time OpenTable experience proposal, guest copy, and FOH support docs"],
            ["Demand", "Yes" if selected_venue == "Eloise" else "No", "OpenTable demand pattern and reservation velocity snapshot"],
            ["Strategy", "Yes" if selected_venue == "Dolly's" else "No", "Bachelorette benchmark, Sun-Wed off-peak benchmark, and female-safety operating framework"],
            ["Teardowns", "Yes" if selected_venue in VENUE_TEARDOWNS and len(VENUE_TEARDOWNS[selected_venue]) > 0 else "No", "Deep-dive competitor teardowns"],
            ["Menu", "Yes" if selected_venue == "Old Spaghetti Factory" else "No", "Core menu comparison against chain competitors"],
        ]
        analysis_df = pd.DataFrame(analysis_rows, columns=["Section", "Available", "What It Covers"])
        show_table(analysis_df)

        st.divider()
        st.markdown("### Recommended Actions")
        recommendations_df = pd.DataFrame(VENUE_RECOMMENDATIONS[selected_venue]).rename(
            columns={
                "priority": "Priority",
                "action": "Action",
                "borrowed_from": "Borrowed From",
                "type": "Type",
                "what_they_do_right": "What They Do Right",
                "why_it_fits": "Why It Fits",
            }
        )
        show_table(recommendations_df)

    elif venue_section == "Competitors":
        for tier in selected_tiers:
            desc = TIER_LABELS[tier]
            df = COMPETITORS[selected_venue][tier].copy()
            if search_term:
                mask = df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)
                df = df[mask]
            st.markdown(f"### {tier}")
            st.caption(f"{desc} — {len(df)} competitor{'s' if len(df) != 1 else ''}")
            if df.empty:
                st.info("No competitors match your search.")
            else:
                show_table(df)

    elif venue_section == "Pricing":
        st.markdown("### Competitor Pricing")
        basket, asterisk = _PRICING_FRAMEWORKS[selected_venue]
        st.markdown(f"**Pricing basket:** {basket}")
        st.caption("All prices CAD, before tax/tip. Regular menu only — no specials. Global competitors converted at April 2026 rates.")
        pricing_df = COMPETITOR_PRICING[selected_venue]
        pricing_display_df = pricing_df[["Name", "Total (CAD)", "Region", "Breakdown"]].copy()
        show_table(pricing_display_df, highlight_venues=True)
        st.caption(
            f"`*` indicates an incomplete basket comparison because one required basket item is not available for that concept. "
            f"Typical reasons include no appetizer, no draft beer, no cocktail program, or no food offering. {asterisk}."
        )

        st.divider()
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.plotly_chart(pricing_bar_chart(pricing_df, selected_venue), use_container_width=True)
        with chart_col2:
            st.plotly_chart(pricing_scatter(pricing_df, selected_venue), use_container_width=True)

    elif venue_section == "Menu" and selected_venue == "Old Spaghetti Factory":
        st.markdown("### Old Spaghetti Factory — Core Menu Comparison")
        st.caption(
            "Core-menu benchmark against Scaddabush, East Side Mario's, and Olive Garden using current official brand menus. "
            "Olive Garden prices converted from USD at ~1.37 CAD. All prices as of April 2026."
        )
        menu_display_df = build_osf_menu_display_table(OSF_MENU_ANALYSIS)
        show_table(menu_display_df, max_height=620)

        _menu_chart = osf_menu_grouped_bar(OSF_MENU_ANALYSIS)
        if _menu_chart:
            st.divider()
            st.plotly_chart(_menu_chart, use_container_width=True)

        st.divider()
        st.markdown("### Strategic Reads")
        strategic_reads = OSF_MENU_ANALYSIS[["Item", "Read"]].copy()
        show_table(strategic_reads, max_height=420)

        st.divider()
        st.markdown("### Sources")
        sources_df = pd.DataFrame(OSF_MENU_ANALYSIS_SOURCES)
        st.dataframe(
            sources_df,
            width="stretch",
            column_config={"URL": st.column_config.LinkColumn("URL")},
            hide_index=True,
        )

    elif venue_section == "Research":
        # Spreadsheet research tables (if available)
        if selected_venue in VENUE_RESEARCH_TABLES:
            research_df = VENUE_RESEARCH_TABLES[selected_venue]
            st.markdown(f"### {selected_venue} — Spreadsheet Research Tables")
            st.caption("Structured fields pulled from the source competitor-analysis spreadsheet for this venue.")

            for label in selected_research_categories:
                column_name = RESEARCH_CATEGORY_COLUMNS[label]
                if column_name not in research_df.columns:
                    continue
                category_df = research_df[["Name", column_name]].copy()
                category_df = category_df[category_df[column_name].notna()]
                category_df[column_name] = category_df[column_name].astype(str).str.strip()
                category_df = category_df[category_df[column_name] != ""]
                if category_df.empty:
                    continue

                st.markdown(f"### {label}")
                show_table(category_df, max_height=520)

        # Top 3 complaints per competitor (from teardowns)
        if selected_venue in VENUE_TEARDOWNS and VENUE_TEARDOWNS[selected_venue]:
            st.divider()
            st.markdown("### Top 3 Customer Complaints by Competitor")
            st.caption("Extracted from review analysis in competitor teardowns. Ranked by frequency and severity.")
            _complaint_rows = []
            for _cname, _cdata in VENUE_TEARDOWNS[selected_venue].items():
                _weaknesses = _cdata.get("review_weaknesses", [])
                _row = [_cname]
                for _ci in range(3):
                    _row.append(_weaknesses[_ci] if _ci < len(_weaknesses) else "—")
                _complaint_rows.append(_row)
            if _complaint_rows:
                _complaints_df = pd.DataFrame(_complaint_rows, columns=["Competitor", "Complaint #1", "Complaint #2", "Complaint #3"])
                show_table(_complaints_df)

    elif venue_section == "Social" and selected_venue in VENUE_SOCIAL_AUDIT:
        audit_df = VENUE_SOCIAL_AUDIT[selected_venue].copy()
        if "Google Rating" in audit_df.columns:
            audit_df["Google Rating"] = pd.to_numeric(audit_df["Google Rating"], errors="coerce")
            audit_df = audit_df.sort_values(by="Google Rating", ascending=False, na_position="last")
        st.markdown(f"### {selected_venue} — Social & Review Audit")
        if selected_venue == "Bar Cathedral":
            st.caption("First-pass competitive social audit focused on content patterns, cadence, and programming signals from the current Bar Cathedral competitor set.")
        elif selected_venue == "Dolly's":
            st.caption("Pre-opening social and launch-readiness view. Dolly's own row reflects reserved platform infrastructure and the launch strategy documents already in Drive.")
        _display_df = audit_df.copy()
        if "IG Followers Display" in _display_df.columns:
            _display_df["IG Followers"] = _display_df["IG Followers Display"]
            _display_df = _display_df.drop(columns=["IG Followers Display", "IG Note"], errors="ignore")
        show_table(_display_df, max_height=780)
        if "IG Note" in audit_df.columns and audit_df["IG Note"].str.strip().any():
            st.caption("\\* IG follower count is for a chain/multi-location account, not a single venue.")

        if selected_venue != "Bar Cathedral":
            st.divider()
            _scatter = social_scatter(audit_df, selected_venue)
            if _scatter:
                st.plotly_chart(_scatter, use_container_width=True)

            chart_col_a, chart_col_b = st.columns(2)
            with chart_col_a:
                _bar = social_followers_bar(audit_df)
                if _bar:
                    st.plotly_chart(_bar, use_container_width=True)
            with chart_col_b:
                _heatmap = social_platform_heatmap(audit_df)
                if _heatmap:
                    st.plotly_chart(_heatmap, use_container_width=True)
        else:
            st.divider()
            st.markdown("### Key Findings")
            findings_df = pd.DataFrame(
                [
                    ["Bar Cathedral", "Needs a repeatable weekly content spine tied to each programmed night."],
                    ["Comedy / Open Mic", "These nights should be promoted like serialized shows, not one-off posts."],
                    ["Live Music", "Artist/talent clips are the most transferable social asset for Tuesday to Thursday demand."],
                    ["DJ Nights", "Weekend content should emphasize atmosphere, crowd density, and creator-friendly visuals."],
                ],
                columns=["Focus", "Read"],
            )
            show_table(findings_df)

        if selected_venue == "Bar Cart":
            st.divider()
            st.markdown("### Programming Index")
            st.caption("How each competitor programs across daily, weekly, and monthly cadences")
            show_table(BAR_CART_PROGRAMMING, max_height=420)

            st.divider()
            st.markdown("### What Bar Cart Should Do Next")
            show_table(BAR_CART_RECOMMENDATIONS)

            st.divider()
            st.markdown("### Notes")
            for note in BAR_CART_SNAPSHOT["notes"]:
                st.markdown(f"- {note}")

        elif selected_venue == "Scotland Yard":
            st.divider()
            st.markdown("### Key Findings")
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("#### Top 5 by IG Followers")
                if "IG Followers" in audit_df.columns:
                    top5 = audit_df.nlargest(5, "IG Followers")[["Name", "IG Followers", "Est. Posts/Week", "Platforms"]]
                    show_table(top5)
            with col_b:
                st.markdown("#### Platform Gaps")
                platform_df = pd.DataFrame([
                    ["Instagram", "Yes", "All competitors"],
                    ["Facebook", "Yes", "All competitors"],
                    ["TikTok", "No", "Score on King, Fox on John, Flatiron, Madison"],
                    ["Twitter/X", "No", "Fox on John, Flatiron, The Pilot"],
                ], columns=["Platform", "SY", "Competitors With It"])
                show_table(platform_df)
        elif selected_venue == "Dolly's":
            st.divider()
            st.markdown("### Key Findings")
            findings_df = pd.DataFrame(
                [
                    ["Audience", "The source strategy is explicit: Dolly's is female-led, celebration-friendly, and designed for 22-35 nightlife occasions."],
                    ["Biggest Risk", "Off-peak demand is the main business risk, so Sun-Wed cannot be left as generic bar nights."],
                    ["Best Benchmark", "Bub City is the most structurally relevant comp because it combines real food, line-dancing programming, and high-energy nightlife."],
                    ["Best Toronto Signal", "Paris Texas proves that country nightlife can feel current, fashionable, and bachelorette-ready in downtown Toronto."],
                    ["Operational Edge", "Female safety is a sharper point of difference than product alone, but only if it becomes visible operating practice."],
                ],
                columns=["Focus", "Read"],
            )
            show_table(findings_df)

            st.divider()
            st.markdown("### Reserved Social Handles")
            show_table(DOLLY_SOCIAL_HANDLES, max_height=420)

            st.divider()
            st.markdown("### Launch-to-Sustain Framework")
            show_table(DOLLY_LAUNCH_FRAMEWORK, max_height=520)
        elif selected_venue == "Eloise":
            st.divider()
            st.markdown("### Key Findings")
            col_a, col_b = st.columns(2)
            with col_a:
                findings_df = pd.DataFrame(
                    [
                        ["Eloise", "The account is real and growing, but it is still undersized relative to premium Toronto peers."],
                        ["Biggest Gap", "Eloise lacks the follower scale and posting cadence of Toronto's top premium dining brands."],
                        ["Best Opportunity", "Lean harder into room mood, chef perspective, and the Eloise-to-Bar-Cart full-evening journey."],
                        ["Competitive Reality", "Several peers benefit from chain or group-account lift, so raw follower counts need context."],
                    ],
                    columns=["Focus", "Read"],
                )
                show_table(findings_df)
            with col_b:
                caveat_df = pd.DataFrame(
                    [
                        ["Single-location", "Eloise, SAMMARCO, Cluny Bistro, Edulis, Giulietta"],
                        ["Venue-specific group account", "Alo, Canoe, Gusto 101, Byblos"],
                        ["Chain account", "Piano Piano, Terroni"],
                    ],
                    columns=["Account Scope", "Examples"],
                )
                show_table(caveat_df)

    elif venue_section == "Fixed Price Menu" and selected_venue == "Eloise":
        st.markdown("### Taste Eloise Signature — Fixed Price Menu")
        st.caption("Final menu: $110/pp base + wine pairing $45 + striploin supplement $18. Target: $125/pp avg cheque. Thu–Sat, 6:30 / 7:00 / 7:30pm seatings.")
        render_download_buttons(
            [
                ("Download Guest Menu PDF", ELOISE_DOCS_PATH / "taste_eloise_signature_menu.pdf"),
                ("Download Proposal PDF", ELOISE_DOCS_PATH / "fixed_price_menu_proposal.pdf"),
                ("Download OpenTable Copy PDF", ELOISE_DOCS_PATH / "opentable_experience_copy.pdf"),
                ("Download FOH Cheat Sheet PDF", ELOISE_DOCS_PATH / "foh_cheat_sheet.pdf"),
                ("Download Research Notes PDF", ELOISE_DOCS_PATH / "peak_time_pricing_research.pdf"),
            ],
            columns=2,
        )
        st.divider()

        st.markdown("#### The Problem")
        st.warning("6:30–8pm Friday/Saturday fills easily, but not every guest hits the $125/pp target. Some tables order one pasta and water, occupying a prime-time seat that could generate 2–3x the revenue.", icon="⚠️")
        st.divider()

        st.markdown("#### Current Eloise Menu Prices")
        _current_menu = [
            ["Starters", "Scallop Crudo, Tuna Tiradito, Oysters, Potato Pavé, Pain au Lait", "Up to $26"],
            ["Vegetables", "Heirloom Tomatoes, Romaine & Endives, Grilled Caraflex, Rapini, Roasted Carrot", "$14–18"],
            ["Pasta", "Agnolotti, Pappardelle, Lobster Risotto", "Up to $30"],
            ["Big Plates", "12oz Dry Aged Striploin, Rainbow Trout, Half Roasted Chicken, Dover Sole, Iberico Pork Katsu", "Up to $68"],
            ["Sides", "Potato Pavé, Charred Broccolini, Grilled Cabbage", "$16"],
            ["Desserts", "Apple Tarte Tatin, Citrus Parfait, Mango Mille-Feuille", "$20"],
            ["Cocktails", "Signature cocktails", "$23"],
        ]
        show_table(pd.DataFrame(_current_menu, columns=["Category", "Items", "Price (up to)"]))
        st.caption("Internal costs: Starters ~$11, Pasta ~$10, Mains ~$28.80, Sides ~$4.84, Desserts ~$6.65, Cocktails ~$4.14")
        st.divider()

        st.markdown("#### Package 1: Eloise Dinner for Two — $130/pp")
        st.markdown("*Also scales to 4 (quantities doubled). OpenTable configured for 2 or 4 only.*")
        _pkg1 = [
            ["Complimentary Brioche", "Included", "—"],
            ["Starters (choose 2)", "Beet Salad, Scallop Crudo, Mushroom Parfait", "$26 each"],
            ["Pasta (1 to share)", "Ravioli (+ truffle add-on option)", "$30"],
            ["Mains (choose 2)", "Roast Chicken, Salmon, Striploin", "Up to $68"],
            ["Side (1 for table)", "Potato Pavé or Cabbage", "$16"],
            ["Dessert (choose 1)", "Apple Tarte Tatin or Citrus Parfait", "$20"],
            ["2 Cocktails at Bar Cart", "End the evening next door", "$23 each"],
        ]
        show_table(pd.DataFrame(_pkg1, columns=["Course", "Selections", "Menu Price"]))
        c1, c2, c3 = st.columns(3)
        c1.metric("Menu Value (for 2)", "$300")
        c2.metric("Selling Price", "$130/pp")
        c3.metric("Food Cost", "~35%")
        st.divider()

        st.markdown("#### Package 2: Shared Experience Core (6–8 guests) — $120/pp")
        st.markdown("*Family-style for the table. Quantities shown are total dishes served to the group.*")
        _pkg2 = [
            ["Starters (6 scallops + 2 plates + 2 plates)", "1 Seared Scallop pp + 2 plates Hamachi Crudo + 2 plates Beet Salad", "$184"],
            ["Mid Course (3–4 plates)", "Pasta TBD + truffle", "$70"],
            ["Mains (3 plates)", "1 plate Striploin + 1 plate Grilled Chicken + 1 plate Grilled Salmon", "$158"],
            ["Sides (2 plates)", "Potato Pavé + Charred Broccolini", "$56"],
            ["Desserts (3)", "Citrus Parfait + Mango Mille-Feuille + Apple Tarte Tatin", "$54"],
            ["Prosecco (6 glasses)", "Welcome drinks", "Included"],
        ]
        show_table(pd.DataFrame(_pkg2, columns=["Course (qty for table)", "What's Included", "Menu Value (table)"]))
        c1, c2, c3 = st.columns(3)
        c1.metric("Food Value (table of 6)", "$522 ($87/pp)")
        c2.metric("Selling Price", "$120/pp ($720 table)")
        c3.metric("Food Cost", "30.5%")
        st.divider()

        st.markdown("#### Package 3: Shared Experience Premium (6–8 guests) — $140/pp")
        st.markdown("*Family-style for the table. Quantities shown are total dishes served to the group.*")
        _pkg3 = [
            ["Starters (12 oysters + 6 scallops + 2 plates + 2 plates)", "2 Oysters pp + 1 Scallop pp + 2 plates Hamachi Crudo + 2 plates Mushroom Parfait", "$184"],
            ["Mid Course (3 plates)", "Shrimp Pasta", "$120"],
            ["Mains (3 plates)", "Côte de Boeuf (50oz) + Dover Sole + Iberico Pork Chop", "$300"],
            ["Sides (4 plates)", "2 plates Cabbage + 2 plates Charred Broccolini", "$60"],
            ["Desserts (3)", "Citrus Parfait + Mango Mille-Feuille + Apple Tarte Tatin", "$54"],
            ["Champagne (6 glasses)", "Welcome drinks", "Included"],
        ]
        show_table(pd.DataFrame(_pkg3, columns=["Course (qty for table)", "What's Included", "Menu Value (table)"]))
        c1, c2, c3 = st.columns(3)
        c1.metric("Food Value (table of 6)", "$718 ($120/pp)")
        c2.metric("Selling Price", "$140/pp ($840 table)")
        c3.metric("Food Cost", "31.9%")
        st.divider()

        st.markdown("#### Internal Costing Summary")
        _costing = [
            ["Dinner for 2/4 (no drinks)", "$100/pp", "$224 (2pp)", "45.6%"],
            ["Dinner for 2/4 + Bar Cart cocktails", "$130/pp", "$300 (2pp)", "~35%"],
            ["Shared Core (6–8)", "$120/pp", "$522 (6pp)", "30.5%"],
            ["Shared Premium (6–8)", "$140/pp", "$718 (6pp)", "31.9%"],
        ]
        show_table(pd.DataFrame(_costing, columns=["Package", "Selling Price/pp", "Menu Value", "Food Cost %"]))
        st.divider()

        st.markdown("#### Time Slot Structure")
        _slots = [
            ["5:00–6:15pm", "Standard à la carte", "No change"],
            ["6:30–8:00pm Fri/Sat", "★ Eloise Experience ONLY — prepaid package", "Guarantees $125+/pp"],
            ["8:15pm+", "Standard à la carte", "No change"],
        ]
        show_table(pd.DataFrame(_slots, columns=["Time Slot", "Booking Type", "Impact"]))
        st.caption("Party sizes: 2 or 4 (Dinner for Two) or 6–8 (Shared Experience). Odd sizes book outside peak window.")
        st.divider()

        st.markdown("#### Global Benchmarks")
        _benchmarks = [
            ["Suraya", "Philadelphia", "Tasting menu REQUIRED Fri/Sat only", "$78/pp"],
            ["Demi", "Chicago", "Different tiers: $175 Fri/Sat, $125 other nights", "$125–175/pp"],
            ["The Coach House", "Chicago", "Weekends only, 2 seatings, set menu", "$135/pp"],
            ["Eleven Madison Park", "New York", "Tasting menu only, no à la carte", "$385/pp"],
            ["Alo", "Toronto", "Tasting menu only, prepaid via Tock", "$245/pp"],
        ]
        show_table(pd.DataFrame(_benchmarks, columns=["Restaurant", "City", "What They Do", "Price"]))
        st.caption("**Toronto gap:** No restaurant in Eloise's tier uses time-slot-specific prepaid Experiences. First-mover opportunity.")
        st.divider()

        st.markdown("#### Revenue Impact (Fri+Sat 6:30–8pm)")
        _scenarios = [
            ["Current (no minimum)", "Varies", "~40 covers", "~$3,200", "—"],
            ["At $120/pp", "$120 guaranteed", "~38 covers", "$4,560", "+43%"],
            ["At $125/pp ★", "$125 guaranteed", "~38 covers", "$4,750", "+48%"],
            ["At $130/pp", "$130 guaranteed", "~36 covers", "$4,680", "+46%"],
        ]
        show_table(pd.DataFrame(_scenarios, columns=["Scenario", "Per Person", "Covers", "Weekend Revenue", "vs Current"]))
        st.divider()

        st.markdown("#### Marketing Language")
        st.markdown("**OpenTable:**")
        st.markdown("> *The Eloise Experience — a curated multi-course dinner by Chef Akhil Hajare. Starters, mains, dessert, and a cocktail at Bar Cart. Friday & Saturday, 6:30–8pm. From $120/pp. Prepaid at booking.*")
        st.markdown("**For regulars:**")
        st.markdown("> *Prefer à la carte? Tables available before 6:30pm and after 8:15pm — same menu, same kitchen, same Eloise.*")
        st.divider()

        st.markdown("#### Risks & Mitigations")
        _risks = [
            ["Guests feel restricted", "Frame as 'Experience' — Bar Cart cocktail makes it a journey, not a restriction"],
            ["Demand drops", "Slots fill easily now. Even 5% attrition lifts revenue significantly."],
            ["Regulars penalized", "Priority at 5pm and 8:15pm+. Full à la carte preserved."],
            ["Party size friction", "OpenTable: 2, 4, 6, 8 only. Odd sizes book outside peak."],
            ["Kitchen load", "Same menu, same execution. May simplify service."],
        ]
        show_table(pd.DataFrame(_risks, columns=["Risk", "Mitigation"]))
        st.divider()

        st.markdown("#### Implementation")
        _steps = [
            ["1", "Confirm final items per tier with Chef Hajare"],
            ["2", "Set selling prices ($120 / $130 / $140 per tier)"],
            ["3", "Configure OpenTable Experiences — prepaid, 6:30–8pm Fri/Sat"],
            ["4", "Configure party sizes: 2/4 and 6/8"],
            ["5", "Remove standard reservations for peak window"],
            ["6", "Brief FOH + Bar Cart team"],
            ["7", "Social + email announcement"],
            ["8", "4-weekend pilot — track cheque, covers, no-shows, feedback"],
            ["9", "Expand to Thursday if successful"],
        ]
        show_table(pd.DataFrame(_steps, columns=["Step", "Action"]))
        st.caption("Source: ECC Fixed Price Menu spreadsheet, Eloise Menu doc, Eloise Menu Packages doc (Google Drive)")

    elif venue_section == "Demand" and selected_venue == "Eloise":
        st.markdown("### Eloise — Demand Pattern & Reservation Velocity")
        st.caption("OpenTable snapshot. `Booked Today` changes throughout the day, so read it as a live demand signal rather than a fixed ranking.")

        demand_df = ELOISE_DEMAND_AUDIT.copy()
        demand_df = demand_df.sort_values(by="Booked Today", ascending=False, na_position="last")
        show_table(demand_df, max_height=720)

        st.divider()
        col_a, col_b = st.columns(2)
        with col_a:
            findings_df = pd.DataFrame(
                [
                    ["Eloise", "Current booking velocity is credible, but it sits well below the strongest Toronto premium-demand engines."],
                    ["Best Single-Location Benchmark", "Giulietta is the clearest proof that a premium but approachable restaurant can sustain very high reservation demand."],
                    ["Most Relevant Nearby Threat", "Piano Piano Colborne matters because it layers lunch, happy hour, and dinner into one high-velocity downtown address."],
                    ["Strategic Read", "Eloise likely needs sharper occasion ownership and stronger daypart legibility before it needs more menu complexity."],
                ],
                columns=["Focus", "Read"],
            )
            show_table(findings_df)
        with col_b:
            tier_df = pd.DataFrame(
                [
                    ["Very High", "50+ booked today"],
                    ["High", "20-49 booked today"],
                    ["Moderate", "10-19 booked today"],
                    ["Low", "Under 10 booked today"],
                ],
                columns=["Velocity Tier", "Rule of Thumb"],
            )
            show_table(tier_df)

        st.divider()
        st.markdown("### Sources")
        st.dataframe(
            ELOISE_DEMAND_SOURCES,
            width="stretch",
            column_config={"URL": st.column_config.LinkColumn("URL")},
            hide_index=True,
        )

    elif venue_section == "Strategy" and selected_venue == "Dolly's":
        st.markdown("### Dolly's — Commercial Strategy")
        st.caption("Working commercial framework built from the Dolly's launch docs, current country-bar benchmarks, and Toronto nightlife competition.")

        st.markdown("### Bachelorette Benchmark")
        show_table(DOLLY_BACHELORETTE_BENCHMARK, max_height=420)

        st.divider()
        st.markdown("### Bachelorette Package Design")
        show_table(DOLLY_BACHELORETTE_PACKAGES, max_height=420)

        st.divider()
        st.markdown("### Bachelorette Marketing Plan")
        show_table(DOLLY_BACHELORETTE_MARKETING, max_height=420)

        st.divider()
        st.markdown("### Off-Peak Benchmark")
        show_table(DOLLY_OFF_PEAK_BENCHMARK, max_height=420)

        st.divider()
        st.markdown("### Sun-Wed Off-Peak Programming")
        show_table(DOLLY_OFF_PEAK_FRAMEWORK, max_height=420)

        st.divider()
        st.markdown("### Night-by-Night KPIs")
        show_table(DOLLY_OFF_PEAK_KPIS, max_height=320)

        st.divider()
        st.markdown("### Female-Safety Operating Framework")
        show_table(DOLLY_FEMALE_SAFETY_FRAMEWORK, max_height=520)

    elif venue_section == "Teardowns" and selected_venue in VENUE_TEARDOWNS:
        st.markdown("### Competitor Teardowns")

        # Get bench row for comparison charts
        if selected_venue in VENUE_TEARDOWN_BENCHMARKS:
            bench = VENUE_TEARDOWN_BENCHMARKS[selected_venue]
        elif selected_venue in VENUE_SOCIAL_AUDIT:
            bench = VENUE_SOCIAL_AUDIT[selected_venue].iloc[0]
        else:
            bench = SY_SOCIAL_AUDIT.iloc[0]

        _active_teardowns = {k: v for k, v in VENUE_TEARDOWNS[selected_venue].items() if k in selected_teardowns}
        if not _active_teardowns:
            st.info("Select at least one competitor from the sidebar to view teardowns.")

        for td_name, t in _active_teardowns.items():
            _ig_header = _format_optional_metric(t.get("ig_followers"))
            _google_header = _format_optional_metric(t.get("google_rating"))
            with st.expander(f"{td_name}  —  {t['neighbourhood']}  |  Google {_google_header}  |  {_ig_header} IG followers"):

                st.markdown(f"#### Company Overview")
                col1, col2 = st.columns(2)
                with col1:
                    overview_df = pd.DataFrame([
                        ["Address", t["address"]],
                        ["Neighbourhood", t["neighbourhood"]],
                        ["Parent / Owner", t["parent"]],
                        ["Founded", t["founded"]],
                        ["Website", t["website"]],
                        ["Positioning", t["positioning"]],
                    ], columns=["Field", "Detail"])
                    show_table(overview_df)
                with col2:
                    if t.get("screenshot"):
                        st.image(t["screenshot"], caption=f"{td_name} — Homepage", use_container_width=True)
                    else:
                        st.info("No hero image captured for this teardown yet.")
                        st.markdown(f"Official website: {t['website']}")

                st.divider()
                st.markdown("#### Reviews & Digital Presence")
                c1, c2, c3, c4, c5, c6 = st.columns(6)
                c1.metric("Google", _format_optional_metric(t.get("google_rating")))
                c2.metric("Google Reviews", _format_optional_metric(t.get("google_reviews")))
                c3.metric("Yelp", _format_optional_metric(t.get("yelp_rating")))
                c4.metric("IG Followers", _format_optional_metric(t.get("ig_followers")))
                c5.metric("IG Posts", _format_optional_metric(t.get("ig_posts")))
                c6.metric("Posts/Week", t["posts_per_week"])

                compare_rows = [
                    ["Google Rating", _format_optional_metric(t.get("google_rating")), _format_optional_metric(bench.get("Google Rating"))],
                    ["Google Reviews", _format_optional_metric(t.get("google_reviews")), _format_optional_metric(bench.get("Google Reviews"))],
                    ["IG Followers", _format_optional_metric(t.get("ig_followers")), _format_optional_metric(bench.get("IG Followers"))],
                ]
                if t.get("ig_posts") is not None or bench.get("Total Posts") is not None:
                    compare_rows.append(
                        ["Total IG Posts", _format_optional_metric(t.get("ig_posts")), _format_optional_metric(bench.get("Total Posts"))]
                    )
                compare_rows.extend([
                    ["Est. Posts/Week", t["posts_per_week"], bench.get("Est. Posts/Week", "n/a")],
                    ["Platforms", t["platforms"], bench.get("Platforms", "n/a")],
                ])
                compare_df = pd.DataFrame(compare_rows, columns=["Metric", td_name, selected_venue])
                show_table(compare_df)

                st.divider()
                _td_charts = teardown_sidebyside_bar(t, selected_venue, td_name, bench)
                td_col1, td_col2, td_col3 = st.columns(3)
                with td_col1:
                    st.plotly_chart(_td_charts["rating"], use_container_width=True, key=f"rating_{td_name}")
                with td_col2:
                    st.plotly_chart(_td_charts["reviews"], use_container_width=True, key=f"reviews_{td_name}")
                with td_col3:
                    st.plotly_chart(_td_charts["social"], use_container_width=True, key=f"social_{td_name}")

                st.divider()
                st.plotly_chart(teardown_radar(t, selected_venue, td_name, bench), use_container_width=True, key=f"radar_{td_name}")

                st.divider()
                st.markdown("#### Menu & Product")
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.markdown(f"**Menu Structure** ({len(t['menus'])} menus)")
                    for m in t["menus"]:
                        st.markdown(f"- {m}")
                with col_m2:
                    st.markdown("**Signature Items**")
                    for item in t["signature_items"]:
                        st.markdown(f"- {item}")

                st.divider()
                st.markdown("#### Review Analysis")
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    st.markdown("**Strengths**")
                    for s in t["review_strengths"]:
                        st.markdown(f"- {s}")
                with col_r2:
                    st.markdown("**Weaknesses**")
                    for w in t["review_weaknesses"]:
                        st.markdown(f"- {w}")

                st.divider()
                st.markdown("#### SWOT Analysis")
                swot = t["swot"]
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    st.markdown("**Strengths**")
                    for s in swot["strengths"]:
                        st.success(s, icon="💪")
                    st.markdown("**Opportunities**")
                    for o in swot["opportunities"]:
                        st.info(o, icon="🎯")
                with col_s2:
                    st.markdown("**Weaknesses**")
                    for w in swot["weaknesses"]:
                        st.warning(w, icon="⚠️")
                    st.markdown("**Threats**")
                    for th in swot["threats"]:
                        st.error(th, icon="🔴")

                st.divider()
                st.markdown(f"#### Implications for {selected_venue}")
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    st.markdown(f"**What to learn from {td_name}**")
                    for i, l in enumerate(t["learns"], 1):
                        st.markdown(f"{i}. {l}")
                with col_p2:
                    st.markdown(f"**Where {selected_venue} has the advantage**")
                    for i, a in enumerate(t["advantages"], 1):
                        st.markdown(f"{i}. {a}")

                if t.get("sources"):
                    st.divider()
                    st.markdown("#### Sources")
                    sources_df = pd.DataFrame(t["sources"]).rename(columns={"label": "Source", "url": "URL"})
                    st.dataframe(
                        sources_df,
                        width="stretch",
                        column_config={"URL": st.column_config.LinkColumn("URL")},
                        hide_index=True,
                    )

    elif venue_section == "Awards" and selected_venue == "Eloise":
        st.markdown("### Award-Winning Competition")
        st.caption("Concept-similar restaurants (contemporary Canadian, Italian, French, Mediterranean, steakhouse/seafood) that hold major awards. Excludes Japanese, Indian, Chinese, Middle Eastern, and other distinctly different concepts.")

        st.markdown("""
**Award key:**
- **Michelin** — ★ = Star, BG = Bib Gourmand, R = Recommended
- **C100B** — Canada's 100 Best Restaurants (2025)
- **La Liste** — Global ranking (score /100)
- **50 Top Italy** — Best Italian Restaurants Worldwide (2025)
- **OT100** — OpenTable Top 100 Canada (2025)
- **Foodism** — Foodism Toronto (2026)
- **Wine Spec** — Wine Spectator Award (2024–25)
- **CAA** — CAA/AAA Diamond Rating
- **NA 50 Best** — North America's 50 Best (2025)
""")

        def _highlight_awards(val):
            if val and val != "—":
                return "background-color: #1a3a1a; color: #4ade80; font-weight: bold"
            return ""

        styled = ELOISE_AWARD_COMPETITION.style.map(_highlight_awards, subset=[c for c in ELOISE_AWARD_COMPETITION.columns if c != "Name"])
        st.dataframe(styled, use_container_width=True, hide_index=True, height=620)

        st.divider()
        st.markdown("#### Key Observations")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
- **Alo** and **Edulis** dominate cross-platform (Michelin + C100B top 5 + La Liste 94–95)
- **DaNico** punches above its weight on the Italian stage (#3 worldwide, 50 Top Italy)
- **Don Alfonso 1890** is the most broadly awarded restaurant (5 different recognitions)
""")
        with col2:
            st.markdown("""
- **Osteria Giulia** holds Michelin ★ + 3 other awards — worth monitoring as an Italian benchmark
- The gap between Michelin-starred and non-starred competitors is stark
- Most of Eloise's Tier 1 and Tier 2 competitors hold **zero awards**
""")

        st.info("**enRoute Best New (2025), Toronto Life Best New (2025), and blogTO** did not feature any concept-relevant restaurants in recent lists — those lists skewed toward newer openings in other cuisines.")

st.sidebar.divider()
st.sidebar.caption("Draft — April 2026")
st.sidebar.caption("Data: Google Drive + web research + Codex deep dives")
