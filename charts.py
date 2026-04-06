"""Reusable chart builders for the competitive analysis dashboard."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

_OUR_VENUES = {"Scotland Yard", "Bar Cart", "Bar Cathedral", "Eloise", "Old Spaghetti Factory"}
_VENUE_COLOR = "#1E8449"
_COMPETITOR_COLOR = "#5D6D7E"
_TIER_COLORS = {"Local": "#2980B9", "City-wide": "#E67E22", "Global": "#8E44AD"}


def _parse_posts_per_week(value):
    if value is None:
        return None
    match = pd.Series([str(value)]).str.extract(r"(\d+\.?\d*)")[0].iloc[0]
    if pd.isna(match):
        return None
    return float(match)


# ── 1. Pricing: Horizontal bar chart ──────────────────────────────────

def pricing_bar_chart(pricing_df: pd.DataFrame, venue_name: str) -> go.Figure:
    df = pricing_df.copy()
    df = df[df["Total (CAD)"] != "N/A"].copy()
    if "_is_incomplete" in df.columns:
        df = df[~df["_is_incomplete"]].copy()
    df["_total"] = df["Total (CAD)"].str.replace(r"[^\d.]", "", regex=True).astype(float)
    if "_is_incomplete" in df.columns:
        df = df.sort_values(["_is_incomplete", "_total", "Name"], ascending=[True, True, True])
    else:
        df = df.sort_values("_total", ascending=True)
    df["Color"] = df["Name"].apply(lambda n: _VENUE_COLOR if n in _OUR_VENUES else _COMPETITOR_COLOR)

    fig = px.bar(
        df, y="Name", x="_total", color="Color",
        color_discrete_map="identity", orientation="h",
        text=df["_total"].apply(lambda v: f"${v:.0f}"),
        labels={"_total": "Basket Total (CAD)", "Name": ""},
    )
    fig.update_traces(textposition="outside", textfont_size=11)
    fig.update_layout(
        showlegend=False, height=max(350, len(df) * 28),
        margin=dict(l=10, r=40, t=30, b=30),
        title=dict(text=f"{venue_name} — Pricing Basket Comparison", font_size=15),
        xaxis_title="CAD", yaxis=dict(autorange="reversed"),
    )
    return fig


# ── 2. Pricing: Scatter by region ─────────────────────────────────────

def pricing_scatter(pricing_df: pd.DataFrame, venue_name: str) -> go.Figure:
    df = pricing_df.copy()
    df = df[df["Total (CAD)"] != "N/A"].copy()
    if "_is_incomplete" in df.columns:
        df = df[~df["_is_incomplete"]].copy()
    df["_total"] = df["Total (CAD)"].str.replace(r"[^\d.]", "", regex=True).astype(float)
    df["Is Ours"] = df["Name"].apply(lambda n: venue_name if n in _OUR_VENUES else "Competitor")

    fig = px.strip(
        df, x="_total", y="Region", color="Region",
        color_discrete_map=_TIER_COLORS, hover_name="Name",
        hover_data={"_total": ":.0f", "Region": True},
        labels={"_total": "Basket Total (CAD)", "Region": ""},
        category_orders={"Region": ["Local", "City-wide", "Global"]},
    )
    # Highlight our venue
    ours = df[df["Name"].isin(_OUR_VENUES)]
    if not ours.empty:
        fig.add_trace(go.Scatter(
            x=ours["_total"], y=ours["Region"], mode="markers+text",
            marker=dict(size=16, color=_VENUE_COLOR, symbol="diamond", line=dict(width=2, color="white")),
            text=ours["Name"], textposition="top center", textfont=dict(size=11, color=_VENUE_COLOR),
            name=venue_name, showlegend=True,
        ))
    fig.update_layout(
        height=300, margin=dict(l=10, r=10, t=40, b=30),
        title=dict(text="Price Distribution by Region", font_size=15),
    )
    return fig


# ── 3. Social: Scatter (followers vs posts/week) ─────────────────────

def social_scatter(audit_df: pd.DataFrame, venue_name: str) -> go.Figure:
    df = audit_df.copy()
    if "IG Followers" not in df.columns or "Est. Posts/Week" not in df.columns:
        return None

    df["_posts"] = df["Est. Posts/Week"].str.extract(r"(\d+\.?\d*)")[0].astype(float)
    df["Is Ours"] = df["Name"].apply(lambda n: "Our Venue" if n in _OUR_VENUES else "Competitor")

    # Use Google Reviews for bubble size if available
    size_col = None
    if "Google Reviews" in df.columns:
        df["_reviews"] = pd.to_numeric(df["Google Reviews"], errors="coerce").fillna(500)
        size_col = "_reviews"

    fig = px.scatter(
        df, x="_posts", y="IG Followers", color="Is Ours",
        color_discrete_map={"Our Venue": _VENUE_COLOR, "Competitor": _COMPETITOR_COLOR},
        size=size_col if size_col else None, size_max=30,
        hover_name="Name", text="Name",
        hover_data={"_posts": ":.1f", "IG Followers": ":,"},
        labels={"_posts": "Est. Posts per Week", "IG Followers": "Instagram Followers"},
    )
    fig.update_traces(textposition="top center", textfont_size=9)
    fig.update_layout(
        height=480, margin=dict(l=10, r=10, t=40, b=30),
        title=dict(text="Posting Frequency vs. Instagram Followers", font_size=15),
        showlegend=True,
    )
    return fig


# ── 4. Social: Horizontal bar (IG followers) ─────────────────────────

def social_followers_bar(audit_df: pd.DataFrame) -> go.Figure:
    df = audit_df.copy()
    if "IG Followers" not in df.columns:
        return None
    df["IG Followers"] = pd.to_numeric(df["IG Followers"], errors="coerce")
    df = df[df["IG Followers"].notna()].copy()
    if df.empty:
        return None
    df = df.sort_values("IG Followers", ascending=True)
    df["Color"] = df["Name"].apply(lambda n: _VENUE_COLOR if n in _OUR_VENUES else _COMPETITOR_COLOR)

    fig = px.bar(
        df, y="Name", x="IG Followers", color="Color",
        color_discrete_map="identity", orientation="h",
        text=df["IG Followers"].apply(lambda v: f"{int(v):,}" if pd.notna(v) else ""),
        labels={"IG Followers": "Instagram Followers", "Name": ""},
    )
    fig.update_traces(textposition="outside", textfont_size=10)
    fig.update_layout(
        showlegend=False, height=max(350, len(df) * 26),
        margin=dict(l=10, r=60, t=30, b=30),
        title=dict(text="Instagram Followers Ranking", font_size=15),
    )
    return fig


# ── 5. Social: Heatmap (platform coverage) ───────────────────────────

def social_platform_heatmap(audit_df: pd.DataFrame) -> go.Figure:
    df = audit_df.copy()
    if "Platforms" not in df.columns:
        return None

    platforms = ["IG", "FB", "TikTok", "Twitter"]
    matrix = []
    for _, row in df.iterrows():
        p = str(row["Platforms"])
        matrix.append([1 if plat.lower() in p.lower() else 0 for plat in platforms])

    z = np.array(matrix)
    fig = go.Figure(data=go.Heatmap(
        z=z, x=platforms, y=df["Name"].tolist(),
        colorscale=[[0, "#F2F3F4"], [1, "#2980B9"]],
        showscale=False, text=np.where(z == 1, "✓", ""), texttemplate="%{text}",
        textfont=dict(size=14),
    ))
    fig.update_layout(
        height=max(350, len(df) * 26),
        margin=dict(l=10, r=10, t=40, b=30),
        title=dict(text="Platform Coverage", font_size=15),
        yaxis=dict(autorange="reversed"),
        xaxis=dict(side="top"),
    )
    return fig


# ── 6. Portfolio: Stacked bar (competitors by tier) ──────────────────

def portfolio_stacked_bar(venues: dict, competitors: dict, tier_labels: dict) -> go.Figure:
    data = []
    for venue_name in venues:
        for tier in tier_labels:
            count = len(competitors[venue_name][tier])
            data.append({"Venue": venue_name, "Tier": tier, "Count": count})
    df = pd.DataFrame(data)

    fig = px.bar(
        df, x="Venue", y="Count", color="Tier",
        color_discrete_map=_TIER_COLORS,
        text="Count", barmode="stack",
        labels={"Count": "Number of Competitors", "Venue": ""},
    )
    fig.update_traces(textposition="inside", textfont_size=12)
    fig.update_layout(
        height=400, margin=dict(l=10, r=10, t=40, b=30),
        title=dict(text="Competitors Tracked per Venue", font_size=15),
        legend_title_text="Tier",
    )
    return fig


# ── 7. Teardowns: Radar chart ────────────────────────────────────────
# Google Reviews excluded (different magnitude). Google Rating uses
# a zoomed 3.5–5.0 scale so small differences are visually pronounced.

def teardown_radar(teardown: dict, venue_name: str, competitor_name: str, bench_row: pd.Series) -> go.Figure:
    metric_specs = [
        ("Google Rating", teardown.get("google_rating"), bench_row.get("Google Rating")),
        ("IG Followers", teardown.get("ig_followers"), bench_row.get("IG Followers")),
        ("IG Posts", teardown.get("ig_posts"), bench_row.get("Total Posts")),
        ("Posts/Week", _parse_posts_per_week(teardown.get("posts_per_week")), _parse_posts_per_week(bench_row.get("Est. Posts/Week"))),
    ]
    available_specs = [
        (label, float(comp), float(bench))
        for label, comp, bench in metric_specs
        if comp is not None and bench is not None and not pd.isna(comp) and not pd.isna(bench)
    ]
    if not available_specs:
        return go.Figure()

    categories = [label for label, _, _ in available_specs]
    comp_raw = [comp for _, comp, _ in available_specs]
    venue_raw = [bench for _, _, bench in available_specs]

    # Normalize: Google Rating uses zoomed 3.5–5.0 range; others use max-of-two
    norm_comp = []
    norm_venue = []
    for i, (c, v) in enumerate(zip(comp_raw, venue_raw)):
        if categories[i] == "Google Rating":
            # Map 3.5–5.0 to 0–1 to make differences pronounced
            norm_comp.append((c - 3.5) / 1.5)
            norm_venue.append((v - 3.5) / 1.5)
        else:
            mx = max(c, v, 1)
            norm_comp.append(c / mx)
            norm_venue.append(v / mx)

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=norm_comp + [norm_comp[0]], theta=categories + [categories[0]],
        fill="toself", name=competitor_name, fillcolor="rgba(93, 109, 126, 0.2)",
        line=dict(color=_COMPETITOR_COLOR, width=2),
    ))
    fig.add_trace(go.Scatterpolar(
        r=norm_venue + [norm_venue[0]], theta=categories + [categories[0]],
        fill="toself", name=venue_name, fillcolor="rgba(30, 132, 73, 0.2)",
        line=dict(color=_VENUE_COLOR, width=2),
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=False, range=[0, 1.15])),
        showlegend=True, height=400,
        margin=dict(l=60, r=60, t=40, b=30),
        title=dict(text=f"{competitor_name} vs. {venue_name}", font_size=15),
    )
    return fig


# ── 8. Teardowns: Side-by-side bars (split into 3 charts) ────────────
# Returns a dict of figures so caller can lay them out.

def teardown_sidebyside_bar(teardown: dict, venue_name: str, competitor_name: str, bench_row: pd.Series) -> dict:
    comp_rating = teardown["google_rating"]
    venue_rating = float(bench_row["Google Rating"])
    comp_reviews = teardown["google_reviews"]
    venue_reviews = int(bench_row["Google Reviews"])

    volume_specs = [
        ("IG Followers", teardown.get("ig_followers"), bench_row.get("IG Followers")),
        ("IG Posts", teardown.get("ig_posts"), bench_row.get("Total Posts")),
        ("Posts/Week", _parse_posts_per_week(teardown.get("posts_per_week")), _parse_posts_per_week(bench_row.get("Est. Posts/Week"))),
    ]
    volume_specs = [
        (label, float(comp), float(bench))
        for label, comp, bench in volume_specs
        if comp is not None and bench is not None and not pd.isna(comp) and not pd.isna(bench)
    ]
    volume_metrics = [label for label, _, _ in volume_specs]
    comp_volume = [comp for _, comp, _ in volume_specs]
    venue_volume = [bench for _, _, bench in volume_specs]

    # Chart A: Google Rating — zoomed y-axis 3.5–5.0
    fig_rating = go.Figure()
    fig_rating.add_trace(go.Bar(
        name=competitor_name, x=[competitor_name], y=[comp_rating],
        marker_color=_COMPETITOR_COLOR,
        text=[f"{comp_rating}"], textposition="outside", textfont=dict(size=16),
    ))
    fig_rating.add_trace(go.Bar(
        name=venue_name, x=[venue_name], y=[venue_rating],
        marker_color=_VENUE_COLOR,
        text=[f"{venue_rating}"], textposition="outside", textfont=dict(size=16),
    ))
    fig_rating.update_layout(
        barmode="group", height=350,
        margin=dict(l=10, r=10, t=40, b=30),
        title=dict(text="Google Rating", font_size=14),
        yaxis=dict(range=[3.5, 5.1], title="Rating", dtick=0.25),
        showlegend=False,
    )

    # Chart B: Google Reviews — separate scale
    fig_reviews = go.Figure()
    fig_reviews.add_trace(go.Bar(
        name=competitor_name, x=[competitor_name], y=[comp_reviews],
        marker_color=_COMPETITOR_COLOR,
        text=[f"{comp_reviews:,}"], textposition="outside", textfont=dict(size=14),
    ))
    fig_reviews.add_trace(go.Bar(
        name=venue_name, x=[venue_name], y=[venue_reviews],
        marker_color=_VENUE_COLOR,
        text=[f"{venue_reviews:,}"], textposition="outside", textfont=dict(size=14),
    ))
    fig_reviews.update_layout(
        barmode="group", height=350,
        margin=dict(l=10, r=10, t=40, b=30),
        title=dict(text="Google Reviews", font_size=14),
        yaxis_title="Reviews", showlegend=False,
    )

    # Chart C: Social metrics
    fig_social = go.Figure()
    fig_social.add_trace(go.Bar(
        name=competitor_name, x=volume_metrics, y=comp_volume,
        marker_color=_COMPETITOR_COLOR,
        text=[f"{int(v):,}" if float(v).is_integer() else f"{v:.1f}" for v in comp_volume], textposition="outside",
    ))
    fig_social.add_trace(go.Bar(
        name=venue_name, x=volume_metrics, y=venue_volume,
        marker_color=_VENUE_COLOR,
        text=[f"{int(v):,}" if float(v).is_integer() else f"{v:.1f}" for v in venue_volume], textposition="outside",
    ))
    fig_social.update_layout(
        barmode="group", height=350,
        margin=dict(l=10, r=10, t=40, b=30),
        title=dict(text="Social Presence", font_size=14),
        yaxis_title="Count", showlegend=True,
    )

    return {"rating": fig_rating, "reviews": fig_reviews, "social": fig_social}


# ── 9. OSF Menu: Grouped bar ─────────────────────────────────────────

def osf_menu_grouped_bar(menu_df: pd.DataFrame) -> go.Figure:
    """Build a grouped bar chart from the OSF menu comparison DataFrame.
    Expects columns like 'Item', 'OSF', 'Scaddabush', 'East Side Mario's', 'Olive Garden'.
    Only includes rows where at least 2 venues have numeric prices.
    """
    df = menu_df.copy()
    # Find price columns (all except Item, Category, Read, Notes)
    skip = {"Item", "Category", "Read", "Notes", "item", "category", "read", "notes"}
    price_cols = [c for c in df.columns if c not in skip]

    if len(price_cols) < 2 or "Item" not in df.columns:
        return None

    # Extract numeric prices
    for col in price_cols:
        extracted = df[col].astype(str).str.extract(r"\$?(\d+\.?\d*)")[0]
        df[f"_{col}"] = pd.to_numeric(extracted, errors="coerce")

    # Filter to rows with at least 2 non-null prices
    numeric_cols = [f"_{c}" for c in price_cols]
    df["_count"] = df[numeric_cols].notna().sum(axis=1)
    df = df[df["_count"] >= 2]

    if df.empty:
        return None

    fig = go.Figure()
    colors = [_VENUE_COLOR, "#2980B9", "#E67E22", "#8E44AD", "#C0392B"]
    for i, col in enumerate(price_cols):
        fig.add_trace(go.Bar(
            name=col, x=df["Item"], y=df[f"_{col}"],
            marker_color=colors[i % len(colors)],
            text=df[f"_{col}"].apply(lambda v: f"${v:.0f}" if pd.notna(v) else ""),
            textposition="outside",
        ))

    fig.update_layout(
        barmode="group", height=450,
        margin=dict(l=10, r=10, t=40, b=80),
        title=dict(text="Menu Price Comparison by Item", font_size=15),
        yaxis_title="Price (CAD)", xaxis_tickangle=-30,
    )
    return fig
