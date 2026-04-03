import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Esplanade Restaurants — Competitive Analysis",
    page_icon="🍽️",
    layout="wide",
)

# --- DATA ---

VENUES = {
    "Bar Cart": {
        "address": "42 The Esplanade, Toronto",
        "concept": "Speakeasy-inspired cocktail bar hidden behind Eloise. Elevated cocktails (fat washing, clarification, rapid infusing). Bold bar snacks.",
        "price": "$$–$$$ (cocktails ~$18–22)",
        "color": "#6C3483",
    },
    "Bar Cathedral": {
        "address": "54 The Esplanade, Toronto",
        "concept": "Intimate bar & nightclub / live music venue. Church-stained glass aesthetic. Comedy (Sun), open mic (Mon), live music (Tue–Thu), DJs (Fri–Sat).",
        "price": "$$",
        "color": "#1A5276",
    },
    "Eloise": {
        "address": "42 The Esplanade, Toronto",
        "concept": "85-seat Canadian contemporary dining. Chef Akhil Hajare. Enoteca comfort meets steakhouse swagger — pastas, crudos, dry-aged beef, Dover sole, tableside theatrics.",
        "price": "$$$",
        "color": "#B7950B",
    },
    "Scotland Yard": {
        "address": "56 The Esplanade, Toronto",
        "concept": "English pub, Toronto institution since 1978. Traditional pub menu: Guinness stew in Yorkshire pudding, fish & chips, burgers. Sports / football destination.",
        "price": "$$",
        "color": "#1E8449",
    },
    "Old Spaghetti Factory": {
        "address": "The Esplanade, Toronto (+ Edmonton locations)",
        "concept": "Casual family Italian dining. Classic pasta dishes, family-friendly pricing, nostalgic decor (antiques, trolley car). Complete meal value proposition.",
        "price": "$–$$",
        "color": "#C0392B",
    },
}

TIER_LABELS = {
    "Local (1–2 km)": "Venues in the same general category within walking distance",
    "City-wide (Toronto)": "Same or closely aligned concept across the city",
    "Global": "Similar concepts worldwide — aspirational and benchmark comps",
}

COMPETITORS = {
    "Bar Cart": {
        "Local (1–2 km)": pd.DataFrame([
            ["CC Lounge & Whisky Bar", "142 Front St E", "Cocktail lounge in historic Beardmore building, whisky-focused", "Upscale cocktail bar in same neighbourhood, similar occasion"],
            ["LIBRARY BAR", "Fairmont Royal York, 100 Front St W", "Hotel cocktail bar, classic cocktails, refined setting", "Premium cocktail destination, similar price point"],
            ["Bar Notte", "75 The Esplanade", "Wine bar / cocktail spot on the same street", "Direct neighbour, competing for same walk-in traffic"],
            ["Clockwork Champagne & Cocktails", "100 Front St E", "Champagne and cocktail focused bar", "Elevated drinks occasion in same corridor"],
            ["Taberna Social", "Front St area", "Latin-inspired cocktail bar", "Craft cocktail bar competing for same evening-out dollar"],
            ["The Reservoir Lounge", "52 Wellington St E", "Jazz/blues bar with speakeasy vibe, cocktails since 1998", "Intimate atmosphere, cocktail-forward, live entertainment"],
        ], columns=["Name", "Location", "Concept", "Why Competitor"]),
        "City-wide (Toronto)": pd.DataFrame([
            ["Midnight Market", "West Queen West", "Speakeasy, innovative cocktails, intimate vibe", "Top-rated Toronto speakeasy"],
            ["After Seven", "Dundas West", "Japanese-inspired hidden whisky bar behind fake yogurt shop", "Speakeasy format, craft cocktails, similar audience"],
            ["Prequel and Co. Apothecary", "Kensington", "Apothecary-themed speakeasy, hand-ground spices", "Speakeasy concept, theatrical cocktail experience"],
            ["Suite 115", "College St", "Passcode/vault entry speakeasy, distinctive cocktails", "Hidden bar concept, similar occasion"],
            ["Bar 404", "Dundas West", "Intimate cocktail bar, innovative program", "Craft cocktail bar competing for cocktail enthusiasts"],
            ["Lonely Diner", "Queen West", "New speakeasy by Midnight Market team, 1970s vibe", "Direct concept competitor — new, buzzy, craft cocktails"],
            ["Secrette", "King West", "Speakeasy behind GEORGE Restaurant, handcrafted cocktails + small plates", "Hidden bar behind restaurant — identical format to Bar Cart/Eloise"],
            ["À Toi", "Bloor-Yorkville", "Intimate cocktail bar", "Premium cocktail experience, similar demographic"],
            ["The Little Jerry", "West End", "Hi-fi listening bar, vinyl DJs, strong cocktail menu", "Vibe-driven cocktail bar with curated atmosphere"],
        ], columns=["Name", "Location", "Concept", "Why Competitor"]),
        "Global": pd.DataFrame([
            ["Handshake Speakeasy", "Mexico City", "World's 50 Best Bars #2, Gatsby-style speakeasy", "Gold-standard speakeasy concept globally"],
            ["Tayēr + Elementary", "London", "World's Best Bars #5, innovative cocktail techniques", "Modern cocktail bar pushing technique boundaries"],
            ["Connaught Bar", "London", "World's Best Bars #6, classic elegance, hotel speakeasy", "Refined cocktail bar, classic foundation with modern twist"],
            ["Attaboy", "New York", "Legendary speakeasy, no menu — bartender-led", "Speakeasy format, bespoke cocktail experience"],
            ["Please Don't Tell (PDT)", "New York", "Original modern speakeasy, hidden behind hot dog shop", "Restaurant-concealed speakeasy — same format as Bar Cart"],
            ["Cloakroom Bar", "Montreal", "Intimate speakeasy behind suit shop (same consultant Andrew Whibley)", "Direct connection — Whibley consulted on Bar Cart's program"],
            ["Bar Dominion", "Montreal", "Also by Andrew Whibley", "Same beverage consultant lineage"],
            ["Paradiso", "Barcelona", "World's Best Bars #4, hidden entrance through pastrami bar", "Hidden bar concept, theatrical entry"],
        ], columns=["Name", "Location", "Concept", "Why Competitor"]),
    },
    "Bar Cathedral": {
        "Local (1–2 km)": pd.DataFrame([
            ["Sneaky Dee's", "College & Bathurst", "Alternative/punk dive-bar hybrid with food + music", "Alt bar with live music + food, similar vibe"],
            ["The Reservoir Lounge", "52 Wellington St E", "Jazz/blues bar, nightly live music, speakeasy vibe", "Live music venue in same neighbourhood"],
            ["C'est What", "67 Front St E", "Brewpub with live music and comedy nights", "Entertainment-driven bar in same corridor"],
            ["HOTHOUSE", "35 Church St", "Live music and events venue", "Entertainment venue nearby"],
            ["The Berczy", "Front & Church", "Bar/restaurant with event programming", "Nearby nightlife option"],
            ["The Rivoli", "Queen St W", "Live music/performance venue", "Iconic Toronto live music/bar venue"],
            ["El Mocambo", "Spadina Ave", "Iconic live music venue", "Legendary Toronto live music venue"],
            ["The Cameron House", "Queen St W", "Live music bar, singer-songwriter focus", "Intimate live music bar"],
            ["Bovine Sex Club", "Queen St W", "Alt/punk bar", "Alternative bar scene competitor"],
            ["The Painted Lady", "Dundas St W", "Cocktail bar with live music", "Cocktail bar with live entertainment"],
        ], columns=["Name", "Location", "Concept", "Why Competitor"]),
        "City-wide (Toronto)": pd.DataFrame([
            ["Drake Underground", "Queen West", "Intimate live music venue, rising talent", "Small venue, live music, similar capacity and vibe"],
            ["The Handlebar", "Kensington", "Nightly live music, indie/electronic, intimate", "Intimate live music venue with bar"],
            ["Bambi's", "Dundas West", "Basement venue, adventurous bookings, intimate gritty vibe", "Underground music bar, similar programming mix"],
            ["BSMT 254", "Various", "Small venue, rotating promoters, DJ-heavy", "Intimate club nights with changing programming"],
            ["Lula Lounge", "Dundas West", "Latin/world/jazz live music, cultural landmark", "Live music venue with cocktails, curated programming"],
            ["The Comedy Bar", "Various locations", "Dedicated comedy venue with bar", "Competes directly for comedy night audience"],
            ["Yuk Yuk's", "Downtown", "Comedy club, bar service", "Competes for Sunday comedy audience"],
            ["Ada Slaight Hall", "Distillery", "310-seat intimate performance space", "Intimate live performance venue"],
            ["Bangarang", "Downtown", "Games-first social bar", "Social bar with entertainment programming"],
            ["Track & Field", "Downtown", "Experiential bar with lawn games", "Experiential bar competing for same social occasion"],
            ["Dance Cave", "Downtown", "Alt/indie club environment", "Alt/indie nightlife competitor"],
            ["Madison Avenue Pub", "Bloor St", "Large multi-room bar", "Large-format bar, similar social occasion"],
        ], columns=["Name", "Location", "Concept", "Why Competitor"]),
        "Global": pd.DataFrame([
            ["Ronnie Scott's", "London", "Iconic intimate jazz club, 60+ years", "Gold standard for intimate live music bar"],
            ["Blue Note Jazz Club", "New York / Tokyo", "Legendary intimate music venue + cocktails", "Multi-city intimate music venue brand"],
            ["The Troubadour", "London", "Historic intimate live music bar since 1954", "Iconic small live music/bar combo"],
            ["Rockwood Music Hall", "New York", "Multi-stage intimate live music venue, nightly shows", "Diverse programming in small format"],
            ["Union Chapel", "London", "Church-converted music venue", "Church aesthetic + live music — same vibe concept"],
            ["The Commune", "Brooklyn", "Intimate bar/music venue, rotating events", "Similar format: bar + live + DJ programming"],
        ], columns=["Name", "Location", "Concept", "Why Competitor"]),
    },
    "Eloise": {
        "Local (1–2 km)": pd.DataFrame([
            ["Amano Trattoria", "St Lawrence District", "Acclaimed Italian by Chef Angeloni, full bar", "Upscale Italian in same area, competing for dinner occasion"],
            ["The Keg Steakhouse", "The Esplanade", "Steakhouse, dry-aged steaks", "Steak component overlap, same street"],
            ["Cluny Bistro", "Distillery District", "Modern French-Moroccan bistro, heritage building", "Contemporary dining nearby, similar price point"],
            ["SAMMARCO", "Distillery District", "Michelin-recognized, seafood + prime dry-aged beef", "Upscale chef-driven dining, overlapping steak/seafood"],
            ["The Rosebud", "Distillery District", "Chef-owned contemporary fusion, seasonal/local", "Chef-driven contemporary in adjacent neighbourhood"],
            ["Archeo", "Distillery District", "Italian cuisine, rustic-contemporary", "Italian component overlap, nearby"],
            ["Bindia Indian Bistro", "St Lawrence area", "Acclaimed Indian cuisine", "Shares Indian flavour influence, nearby"],
        ], columns=["Name", "Location", "Concept", "Why Competitor"]),
        "City-wide (Toronto)": pd.DataFrame([
            ["Alo", "Entertainment District", "Michelin-starred, French tasting menu", "Toronto's top chef-driven contemporary dining"],
            ["Canoe", "Financial District", "Canadian contemporary, seasonal, iconic views", "Contemporary Canadian with steakhouse elements"],
            ["Marben", "King West", "Contemporary Canadian, local ingredients, no-tipping", "Canadian contemporary with global influences"],
            ["Edulis", "King West", "Michelin-starred, seasonal/foraged, intimate", "Chef-driven intimate dining, similar scale"],
            ["Piano Piano", "Various", "Italian-forward contemporary, lively atmosphere", "Italian-contemporary crossover, similar energy"],
            ["Gusto 101", "Portland St", "Modern Italian, buzzy atmosphere", "Italian-contemporary, similar demographic"],
            ["Terroni", "Various", "Contemporary Italian, quality ingredients", "Italian dining across Toronto, brand recognition"],
            ["Byblos", "Entertainment District", "Eastern Mediterranean, global flavours", "Chef-driven, global influence, similar price point"],
        ], columns=["Name", "Location", "Concept", "Why Competitor"]),
        "Global": pd.DataFrame([
            ["Lyle's", "London", "Modern British, seasonal, intimate, global influence", "Contemporary dining with steakhouse swagger"],
            ["Le Coucou", "New York", "French-inspired contemporary, elegant but accessible", "Refined dining that doesn't take itself too seriously"],
            ["Estela", "New York", "Contemporary with global flavours, crudos + proteins", "Menu philosophy overlap — global, unfussy, ingredient-led"],
            ["Bavel", "Los Angeles", "Middle Eastern-influenced contemporary, bold flavours", "Chef-driven, global flavours, similar energy"],
            ["Candide", "Montreal", "Hyper-seasonal, farm-driven, contemporary Québec", "Canadian contemporary fine dining benchmark"],
            ["Le Violon", "Montreal", "Contemporary blending Irish/Italian/Egyptian + local", "Multi-cultural influence, similar to Eloise approach"],
            ["Alma", "Montreal", "North America's 50 Best, Mexican tasting + Québec local", "Global influence + local sourcing philosophy"],
            ["Momofuku Ko", "New York", "Chef-driven, Asian-influenced contemporary", "Global flavour integration in contemporary format"],
        ], columns=["Name", "Location", "Concept", "Why Competitor"]),
    },
    "Scotland Yard": {
        "Local (1–2 km)": pd.DataFrame([
            ["Score on King", "107 King St E", "High-energy sports pub, Caesar towers", "Sports pub competing for same game-day crowd"],
            ["Duke's Refresher St Lawrence", "73 Front St E", "Retro bar & grill, games", "Casual bar in same corridor, pub food + games"],
            ["The Flatiron: A Firkin Pub", "49 Wellington St E", "British pub in Gooderham Building", "British pub in same block"],
            ["The Jason George", "100 Front St E", "Neighbourhood pub", "Neighbourhood pub competing for same regulars"],
            ["P.J. O'Brien Irish Pub & Restaurant", "39 Colborne St", "Upscale Irish pub", "Upscale pub nearby, different tradition but same occasion"],
            ["C'est What? Inc.", "67 Front St E", "Craft beer brewpub", "Craft beer pub in same corridor"],
            ["The WORKS Craft Burgers & Beer", "60 Wellington St E", "Gastropub, burgers + craft beer", "Gastropub in same block"],
            ["Berkeley Bistro", "262 The Esplanade", "Casual bistro/bar on same street", "Same street, casual pub-style dining"],
            ["Bier Markt", "The Esplanade area", "Belgian-style beer hall, large beer selection", "Beer-focused venue competing for same pint occasion"],
            ["The Keg Steakhouse", "The Esplanade", "Chain steakhouse + bar", "Competing for bar/dinner traffic on same street"],
            ["St. Lawrence Cafe", "248 The Esplanade", "Casual neighbourhood spot", "Competing for local/neighbourhood regular traffic"],
        ], columns=["Name", "Location", "Concept", "Why Competitor"]),
        "City-wide (Toronto)": pd.DataFrame([
            ["The Queen & Beaver Public House", "Elm St", "Best British pub in Toronto, classic comfort food", "Top-rated direct concept competitor"],
            ["Saint John's Tavern", "Entertainment District", "English gastropub, comfort food + hospitality", "English pub, gastropub positioning"],
            ["Bramble Gastropub", "College/Ossington", "British-inspired, beyond typical pub fare, creative cocktails", "British gastropub, elevated positioning"],
            ["House on Parliament", "Cabbagetown", "Family-owned pub, 20+ year institution", "Long-running independent pub, community institution"],
            ["The Fortunate Fox", "Kimpton St George", "Gastropub in hotel, familiar but refreshing", "Gastropub competing for elevated pub dining"],
            ["The Pilot", "Bloor-Yorkville", "Operating since 1944, pub + live music", "Long-running Toronto pub institution"],
            ["The Dog & Bear", "Various", "British pub concept", "English pub concept competitor"],
            ["The Auld Spot Pub", "Danforth", "Traditional pub, sports, comfort food", "Long-running neighbourhood pub with sports focus"],
            ["The Loose Moose", "146 Front St W", "Beer hall, burgers, since 1989", "Long-running Toronto beer hall, similar pub dining"],
            ["The Pint Public House", "277 Front St W", "Large sports pub", "Sports pub competing for same game-day crowd"],
            ["Duke of Cornwall", "400 University Ave", "Traditional British pub", "British pub concept competitor"],
            ["The Fox on John", "106 John St", "Pub", "Pub competing for same casual occasion"],
            ["Madison Avenue Pub", "Bloor St", "Large multi-room bar", "Large-format pub/bar, similar social occasion"],
        ], columns=["Name", "Location", "Concept", "Why Competitor"]),
        "Global": pd.DataFrame([
            ["The Hand & Flowers", "Marlow, UK", "Only 2-Michelin-star pub in UK (Tom Kerridge)", "Gold standard for elevated pub dining"],
            ["The Unruly Pig", "Bromeswell, UK", "#1 Estrella Damm Top 50 Gastropubs", "Top-rated gastropub globally"],
            ["The Eagle", "London", "Originated the 'gastropub' concept in 1991", "Birthplace of the gastropub movement"],
            ["The Sportsman", "Seasalter, UK", "Michelin-starred, locally sourced, pub setting", "Pub that transcends the category"],
            ["The Devonshire", "London, Soho", "Top-ranked urban gastropub", "Urban gastropub benchmark"],
            ["The Star Inn", "Harome, UK", "14th-century inn, innovative British cuisine", "Historic pub with culinary excellence"],
            ["Ye Olde Cheshire Cheese", "London", "Historic pub since 1667", "Iconic long-running English pub institution"],
            ["The Churchill Arms", "London", "Famous traditional pub, 40+ years", "Iconic British pub comparable to Scotland Yard's heritage"],
        ], columns=["Name", "Location", "Concept", "Why Competitor"]),
    },
    "Old Spaghetti Factory": {
        "Local (1–2 km)": pd.DataFrame([
            ["Scaddabush Italian Kitchen & Bar", "200 Front St W", "Modern Italian, mozzarella bar, family portions", "Direct casual Italian competitor nearby"],
            ["Bellissimo Pizzeria & Ristorante", "164 The Esplanade", "Local pizzeria", "Italian on same street, competing for casual Italian dollar"],
            ["Amano Italian Kitchen", "65 Front St W", "Upscale casual Italian", "Italian in same area (different tier)"],
            ["Cantina Mercatto", "20 Wellington St E", "Trendy downtown Italian", "Italian restaurant competing for same dinner occasion"],
            ["Jack Astor's", "Front St area", "Casual family dining, bar", "Family dining occasion competitor"],
            ["Boston Pizza", "Various nearby", "Casual family dining, Italian-inspired", "Family Italian-ish dining at similar price"],
            ["Terroni", "Various nearby", "Quality Italian, multiple locations", "Italian brand in proximity"],
        ], columns=["Name", "Location", "Concept", "Why Competitor"]),
        "City-wide (Toronto)": pd.DataFrame([
            ["East Side Mario's", "Various (2171 Steeles Ave W etc.)", "Casual Italian chain, family-style, similar price", "Direct chain competitor — same segment"],
            ["Il Fornello", "576 Danforth Ave etc.", "Mid-priced casual Italian", "Direct mid-priced Italian chain competitor"],
            ["Mangiare", "2840 Dundas St W", "Local family Italian", "Family-style Italian, similar occasion"],
            ["The Good Son Restaurant", "1096 Queen St W", "Restaurant/bar", "Casual dining competitor"],
            ["Piano Piano Restaurant", "55 Colborne St", "Upscale casual Italian", "Italian-forward, aspirational comp within city"],
            ["Paisano's", "116 Willowdale Ave", "Local Italian", "Family Italian dining in Toronto"],
            ["Moxie's", "Various", "Casual dining chain, family-friendly", "Casual family dining competitor"],
            ["The Pickle Barrel", "Various", "Casual family dining, large menu", "Family dining chain, similar occasion"],
            ["Montana's", "Various", "Casual family dining chain", "Family dining price point and occasion"],
            ["Joey Restaurants", "Various", "Casual-upscale chain, Italian elements", "Casual chain with Italian elements"],
            ["Gusto 101 / Gusto 54", "Various", "Modern casual Italian", "Italian dining, broader appeal"],
            ["Uncle Tony's", "Various", "Italian dining, family-style", "Italian family dining in Toronto"],
            ["Café Diplomatico", "College St", "Iconic casual Italian, neighbourhood institution", "Long-running Italian institution in Toronto"],
        ], columns=["Name", "Location", "Concept", "Why Competitor"]),
        "Global": pd.DataFrame([
            ["Olive Garden", "North America-wide", "Largest casual Italian chain, family dining", "Most direct global comp — same segment and occasion"],
            ["Maggiano's Little Italy", "USA", "Family-style Italian, 50+ locations", "Family-style Italian chain, upscale casual"],
            ["Buca di Beppo", "USA", "Family-style Italian, large portions, kitschy decor", "Nostalgic/kitschy Italian dining — decor similarity"],
            ["Carrabba's Italian Grill", "USA", "Casual Italian, slightly elevated", "Casual Italian chain, step up in quality"],
            ["Romano's Macaroni Grill", "USA", "Casual Italian chain", "Direct segment competitor"],
            ["Frankie & Benny's", "UK", "Casual Italian-American, family-friendly", "Family Italian chain in another market"],
            ["ASK Italian", "UK", "Casual Italian chain, family dining", "European casual Italian chain benchmark"],
            ["Spaghetti Warehouse", "USA (Ohio/TX)", "Nostalgic Italian chain, antique decor", "Closest global concept twin — even the name mirrors it"],
            ["Prezzo", "UK", "Casual Italian chain", "Casual Italian in another market"],
        ], columns=["Name", "Location", "Concept", "Why Competitor"]),
    },
}

# --- SIDEBAR ---

st.sidebar.title("Esplanade Restaurants")
st.sidebar.markdown("Competitive Analysis Dashboard")
st.sidebar.divider()

view_mode = st.sidebar.radio("View", ["By Venue", "Portfolio Overview"], index=0)

if view_mode == "By Venue":
    selected_venue = st.sidebar.selectbox("Select Venue", list(VENUES.keys()))
    selected_tiers = st.sidebar.multiselect(
        "Filter Tiers",
        list(TIER_LABELS.keys()),
        default=list(TIER_LABELS.keys()),
    )
    search_term = st.sidebar.text_input("Search competitors", placeholder="Type a name...")
else:
    selected_venue = None
    selected_tiers = list(TIER_LABELS.keys())
    search_term = st.sidebar.text_input("Search across all venues", placeholder="Type a name...")

# --- MAIN CONTENT ---

st.title("Competitive Analysis")
st.caption("Esplanade Restaurants Group — The Esplanade, Toronto")
st.caption("Source: Google Drive competitor research + web research (April 2026)")

if view_mode == "By Venue" and selected_venue:
    venue = VENUES[selected_venue]

    # Venue header
    st.markdown(f"## {selected_venue}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Price Point", venue["price"])
    col2.metric("Address", venue["address"].replace(", Toronto", ""))

    total = sum(len(COMPETITORS[selected_venue][t]) for t in TIER_LABELS)
    col3.metric("Total Competitors", total)

    st.markdown(f"**Concept:** {venue['concept']}")
    st.divider()

    # Competitor tables by tier
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
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Name": st.column_config.TextColumn("Name", width="medium"),
                    "Location": st.column_config.TextColumn("Location", width="medium"),
                    "Concept": st.column_config.TextColumn("Concept", width="large"),
                    "Why Competitor": st.column_config.TextColumn("Why Competitor", width="large"),
                },
            )

elif view_mode == "Portfolio Overview":
    st.markdown("## Portfolio Overview")
    st.markdown("Competitor counts across all venues and tiers.")

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
        summary_data.append(row)

    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    st.divider()

    # All competitors in one searchable view
    st.markdown("### All Competitors")
    if search_term:
        st.caption(f'Filtered by: "{search_term}"')

    all_rows = []
    for venue_name in VENUES:
        for tier in TIER_LABELS:
            df = COMPETITORS[venue_name][tier].copy()
            df.insert(0, "Venue", venue_name)
            df.insert(1, "Tier", tier)
            all_rows.append(df)

    all_df = pd.concat(all_rows, ignore_index=True)

    if search_term:
        mask = all_df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)
        all_df = all_df[mask]

    st.dataframe(
        all_df,
        use_container_width=True,
        hide_index=True,
        height=600,
        column_config={
            "Venue": st.column_config.TextColumn("Venue", width="small"),
            "Tier": st.column_config.TextColumn("Tier", width="small"),
            "Name": st.column_config.TextColumn("Name", width="medium"),
            "Location": st.column_config.TextColumn("Location", width="medium"),
            "Concept": st.column_config.TextColumn("Concept", width="large"),
            "Why Competitor": st.column_config.TextColumn("Why Competitor", width="large"),
        },
    )

    st.caption(f"{len(all_df)} competitors total")

# --- FOOTER ---
st.sidebar.divider()
st.sidebar.caption("Draft — April 2026")
st.sidebar.caption("Data: Google Drive competitor research + web research (April 2026)")
