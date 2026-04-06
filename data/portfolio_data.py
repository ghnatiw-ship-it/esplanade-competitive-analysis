import json
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

from data.pricing_data import COMPETITOR_PRICING  # noqa: F401 — re-exported

import pandas as pd

VENUES = {
    "Bar Cart": {
        "address": "42 The Esplanade, Toronto",
        "concept": "Speakeasy-inspired cocktail bar hidden behind Eloise. Elevated cocktails (fat washing, clarification, rapid infusing). Bold bar snacks.",
        "price": "$30–55/pp",
        "color": "#6C3483",
    },
    "Bar Cathedral": {
        "address": "54 The Esplanade, Toronto",
        "concept": "Intimate bar & nightclub / live music venue. Church-stained glass aesthetic. Comedy (Sun), open mic (Mon), live music (Tue–Thu), DJs (Fri–Sat).",
        "price": "$15–30/pp",
        "color": "#1A5276",
    },
    "Eloise": {
        "address": "42 The Esplanade, Toronto",
        "concept": "85-seat Canadian contemporary dining. Chef Akhil Hajare. Enoteca comfort meets steakhouse swagger — pastas, crudos, dry-aged beef, Dover sole, tableside theatrics.",
        "price": "$50–85/pp",
        "color": "#B7950B",
    },
    "Scotland Yard": {
        "address": "56 The Esplanade, Toronto",
        "concept": "English pub, Toronto institution since 1978. Traditional pub menu: Guinness stew in Yorkshire pudding, fish & chips, burgers. Sports / football destination.",
        "price": "$20–35/pp",
        "color": "#1E8449",
    },
    "Old Spaghetti Factory": {
        "address": "The Esplanade, Toronto (+ Edmonton locations)",
        "concept": "Casual family Italian dining. Classic pasta dishes, family-friendly pricing, nostalgic decor (antiques, trolley car). Complete meal value proposition.",
        "price": "$15–25/pp",
        "color": "#C0392B",
    },
}

TIER_LABELS = {
    "Local (1–2 km)": "Venues in the same general category within walking distance",
    "City-wide (Toronto)": "Same or closely aligned concept across the city",
    "Global": "Similar concepts worldwide — aspirational and benchmark comps",
}

RESEARCH_CATEGORY_COLUMNS = {
    "Brand Positioning": "Brand Positioning",
    "Direct Or Indirect Competitor": "Direct or Indirect Competitor",
    "Target Audience": "Target Audience",
    "Atmosphere & Experience": "Atmosphere & Experience",
    "Website Quality": "Website Quality",
    "Common Google Review Themes": "Common google review themes",
    "USP": "USP",
    "Guarantee": "Guarantee",
    "Merch / Extensions": "Merch / Extensions",
    "Event Programming / Regular Events": "Event Programming / Regular Events",
    "Private / Group Booking Capabilities": "Private / Group Booking Capabilities",
    "Accessibility Features": "Accessibility Features",
    "Delivery / Takeout / Online Ordering": "Delivery / Takeout / Online Ordering",
    "Loyalty / Rewards Program": "Loyalty / Rewards Program",
    "Promotions & Specials Schedule": "Promotions & Specials Schedule",
    "Collaborations / Partnerships": "Collaborations / Partnerships",
    "Community / Local Engagement": "Community / Local Engagement",
    "Email / Newsletter Presence": "Email / Newsletter Presence",
    "Capacity (Seated / Standing)": "Capacity (Seated / Standing)",
    "Peak Hours / Visit Times": "Peak Hours / Visit Times",
    "Visual Style / Branding Aesthetic": "Visual Style / Branding Aesthetic",
}

VENUE_RESEARCH_FILES = {
    "Bar Cathedral": "bc_competitors.xlsx",
    "Scotland Yard": "sy_competitors.csv",
    "Old Spaghetti Factory": "osf_competitors.csv",
}

OSF_MENU_ANALYSIS = pd.DataFrame([
    {
        "Item": "Spaghetti with Meatballs",
        "Old Spaghetti Factory": "$28 — includes soup/salad, bread, ice cream, coffee/tea",
        "Scaddabush": "$24.99",
        "East Side Mario's": "$22.49 — includes AYCE soup/salad + garlic homeloaf",
        "Olive Garden": "~$21 — includes unlimited soup/salad + breadsticks",
        "Read": "OSF highest but bundled meal makes value story stronger. OG cheapest but lunch-sized.",
    },
    {
        "Item": "Chicken Parmigiana",
        "Old Spaghetti Factory": "$29 — full meal included",
        "Scaddabush": "$28.97",
        "East Side Mario's": "$25.49 — includes AYCE soup/salad + garlic homeloaf",
        "Olive Garden": "~$21 — includes unlimited soup/salad + breadsticks",
        "Read": "Scadd most expensive a la carte. ESM and OG bundle inclusions. OSF bundles most.",
    },
    {
        "Item": "Fettuccine Alfredo with Chicken",
        "Old Spaghetti Factory": "$30 — full meal included",
        "Scaddabush": "$26.05 (Pesto Pollo Penne — closest equivalent)",
        "East Side Mario's": "$23.29 — includes AYCE soup/salad + garlic homeloaf",
        "Olive Garden": "~$20",
        "Read": "OSF highest. ESM competes hardest on price-plus-inclusions.",
    },
    {
        "Item": "Lasagna",
        "Old Spaghetti Factory": "$29 — full meal included",
        "Scaddabush": "Not on menu",
        "East Side Mario's": "$23.99 (12 Layer Lasagna)",
        "Olive Garden": "~$21 — includes unlimited soup/salad + breadsticks",
        "Read": "OSF owns the classic lane. ESM more oversized. OG cheapest. Scadd doesn't compete here.",
    },
    {
        "Item": "Spaghetti Marinara",
        "Old Spaghetti Factory": "$23 — full meal included",
        "Scaddabush": "$19.97 (San Marzano Spaghetti)",
        "East Side Mario's": "$21.79 (Build Your Own Pasta)",
        "Olive Garden": "~$21 — includes unlimited soup/salad + breadsticks",
        "Read": "Scadd cheapest a la carte. OSF bundled value is strongest.",
    },
    {
        "Item": "Seafood Pasta",
        "Old Spaghetti Factory": "$36 — full meal included",
        "Scaddabush": "$27.92 (Lemon Garlic Shrimp Spaghetti — closest)",
        "East Side Mario's": "$24.99",
        "Olive Garden": "~$39 (Seafood Alfredo)",
        "Read": "OSF and OG both premium. ESM significantly cheaper. Scadd doesn't do mixed seafood.",
    },
    {
        "Item": "Tiramisu",
        "Old Spaghetti Factory": "Not on menu",
        "Scaddabush": "$12.22",
        "East Side Mario's": "Not on menu",
        "Olive Garden": "~$16",
        "Read": "OSF and ESM have a gap here. OG and Scadd both offer it.",
    },
    {
        "Item": "Domestic Beer",
        "Old Spaghetti Factory": "$8 (Molson Canadian draft)",
        "Scaddabush": "$7.50 (domestic tall cans — no draft)",
        "East Side Mario's": "~$7.40 (domestic bottles — no draft confirmed)",
        "Olive Garden": "~$8 (Bud Light draft)",
        "Read": "All four competitive at $7-8. ESM and Scadd are bottle/can only.",
    },
    {
        "Item": "House Wine (5 oz)",
        "Old Spaghetti Factory": "$12",
        "Scaddabush": "$8.75",
        "East Side Mario's": "Price not published online",
        "Olive Garden": "~$10",
        "Read": "Scadd most aggressive on first-glass price. OSF highest.",
    },
    {
        "Item": "Signature Cocktail",
        "Old Spaghetti Factory": "$13 (OSF Caesar)",
        "Scaddabush": "$13.95 (Black Cherry Bellini)",
        "East Side Mario's": "$3.99 (Cotton Candy Cosmo Spritz promo)",
        "Olive Garden": "~$14 (Italian Margarita)",
        "Read": "ESM aggressively promotional at $3.99. Others similar at $13-14.",
    },
])

OSF_MENU_ANALYSIS_SOURCES = [
    {
        "Brand": "Old Spaghetti Factory",
        "Source": "Toronto location menu",
        "URL": "https://oldspaghettifactory.ca/locations/toronto/",
    },
    {
        "Brand": "Scaddabush",
        "Source": "Official menu",
        "URL": "https://webdev.scaddabush.com/menu/",
    },
    {
        "Brand": "East Side Mario's",
        "Source": "London food menu",
        "URL": "https://www.eastsidemarios.com/en/menus/food/store-8702/on/london/94-fanshawe-park-rd-east.html",
    },
    {
        "Brand": "East Side Mario's",
        "Source": "Barrie drinks menu and specials pages",
        "URL": "https://www.eastsidemarios.com/en/menus/drinks/store-8795/on/barrie/451-bryne-drive.html",
    },
    {
        "Brand": "Olive Garden",
        "Source": "Official specials and menu pages",
        "URL": "https://www.olivegarden.com/",
    },
]

VENUE_RECOMMENDATIONS = {
    "Bar Cart": [
        {
            "priority": 1,
            "action": "Submit for Canada's 100 Best Bars 2026 now and begin building press relationships with blogTO, Toronto Life, and Canada's 100 Best judges.",
            "borrowed_from": "Cry Baby Gallery, Bar Pompette, Civil Liberties",
            "type": "Brand",
            "what_they_do_right": "Cry Baby climbed from #29 to #11 in 4 years. Bar Pompette went from new to #1 in 3 years. Awards create a compounding credibility moat.",
            "why_it_fits": "Bar Cart has a 4.7 Google rating, a Cloakroom Bar pedigree (Andrew Whibley), and a speakeasy concept that is editorial-ready. The story is there — it just hasn't been pitched."
        },
        {
            "priority": 2,
            "action": "Launch TikTok and post the hidden-door entrance as the first piece of content. Aim for 1 Reel/TikTok per week exploiting the speakeasy setting.",
            "borrowed_from": "Mother (39.6K TikTok followers), Prequel & Co. (40K IG from UGC)",
            "type": "Marketing",
            "what_they_do_right": "Mother's TikTok (39.6K followers) and Prequel's mortar-and-pestle UGC prove that theatrical bar content goes viral. Neither Bar Cart's closest competitors are on TikTok yet.",
            "why_it_fits": "The Eloise-to-Bar-Cart hidden entrance is inherently more filmable than any competitor's storefront. First-mover advantage is available."
        },
        {
            "priority": 3,
            "action": "Turn Thursday jazz into a larger branded ritual with a fixed cocktail menu, named performers, and consistent promotion — make it feel like a destination, not an add-on.",
            "borrowed_from": "Bar Pompette (Sunday jazz is brand identity), Cry Baby Gallery",
            "type": "Programming",
            "what_they_do_right": "Bar Pompette's Sunday jazz is inseparable from the brand — guests plan around it. It's not a side event, it's the reason people come that night.",
            "why_it_fits": "Bar Cart already has Thursday jazz; the missing piece is making it feel ownable and worth planning around. Thursday is better than Sunday (start of weekend vs work-tomorrow)."
        },
        {
            "priority": 4,
            "action": "Create a named happy hour (e.g. 'Martini Hour') at a gateway price ($12-14) to fill 5-7pm and drive first-time trial.",
            "borrowed_from": "Compton Ave. (Martini Hour: all martinis $12, Tue-Sun to 8pm)",
            "type": "Pricing",
            "what_they_do_right": "Compton Ave's Martini Hour is their #1 traffic driver — it creates a low-risk entry point that converts newcomers into regulars.",
            "why_it_fits": "Bar Cart's $20 cocktails are justified but can be a barrier for first visits. A gateway hour builds the funnel."
        },
        {
            "priority": 5,
            "action": "Add a 'Bartender's Choice / Surprise Me' option to the menu and launch cocktail masterclass nights on slow nights (Mon/Tue, $60-80/person).",
            "borrowed_from": "Civil Liberties (no-menu bespoke model + Bar School programming)",
            "type": "Product + Programming",
            "what_they_do_right": "Civil Liberties' bespoke model is their entire identity. Their Bar School creates revenue, community, and content from education. NA 50 Best #21.",
            "why_it_fits": "A menu line item captures bespoke appeal without abandoning the menu. Masterclasses monetize slow nights and build brand authority."
        },
        {
            "priority": 6,
            "action": "Create 2-3 named signature cocktails with house-made ingredients and a visual presentation moment worth filming.",
            "borrowed_from": "Mother (fermentation ingredients), Prequel (mortar-and-pestle prep), Cry Baby (proprietary sorrel syrup)",
            "type": "Product",
            "what_they_do_right": "Every top bar has signature serves with proprietary ingredients that become ordering rituals and social content. Prequel's tableside prep alone drives 40K IG followers.",
            "why_it_fits": "Bar Cart has the Whibley technique foundation. The next step is making 2-3 drinks visually iconic and socially shareable."
        },
        {
            "priority": 7,
            "action": "Adopt seasonal 'chapter' naming for menu refreshes to turn updates into launchable events, and add a dedicated zero-proof section (2+ options).",
            "borrowed_from": "Mother (narrative menu chapters, best-in-class zero-proof)",
            "type": "Product",
            "what_they_do_right": "Mother's menu chapters create press cycles and return visits. Their zero-proof options capture the growing non-drinking market at full margin.",
            "why_it_fits": "Seasonal refreshes already happen — naming them turns a kitchen decision into a marketing event. Zero-proof is table stakes at this tier."
        },
        {
            "priority": 8,
            "action": "Build Andrew Whibley's personal brand modestly — get his name on the website, in press pitches, and on 1-2 industry panels per year.",
            "borrowed_from": "Massimo Zitti (Mother), Frankie Solarik (Prequel/BarChef/Compton), Nick Kennedy (Civil Liberties)",
            "type": "Brand",
            "what_they_do_right": "Every top cocktail bar in the set has a named founder whose personal credibility drives press, awards, and audience. Whibley's Cloakroom Bar pedigree is untapped.",
            "why_it_fits": "Bar Cart's consultant story (Whibley designed the program) is a ready-made press angle that hasn't been used."
        },
        {
            "priority": 9,
            "action": "Add a monthly guest shift or collaboration night tied to a bartender, chef, or adjacent cultural partner.",
            "borrowed_from": "Library Bar, Bar Mordecai, Compton Ave.",
            "type": "Programming",
            "what_they_do_right": "They create fresh reasons to visit without changing the whole concept. Guest shifts borrow relevance and generate content.",
            "why_it_fits": "Bar Cart needs periodic spikes in relevance and content beyond opening buzz."
        },
    ],
    "Bar Cathedral": [
        {
            "priority": 1,
            "action": "Name and brand each night with a searchable, hashtagable identity — e.g. 'Sermon Sundays' (comedy), 'Confessional Mondays' (open mic), 'Hymnal Sessions' (live music Tue-Thu).",
            "borrowed_from": "Lula Lounge (Cuban Fridays, Salsa Saturdays)",
            "type": "Programming",
            "what_they_do_right": "Lula's branded nights are searchable, hashtagable, and drive repeat visits. 'Cuban Fridays' is inseparable from the brand — guests plan around it.",
            "why_it_fits": "BC has 7 nights of programming but none are named or branded. Naming them creates recurring rituals and makes each night discoverable."
        },
        {
            "priority": 2,
            "action": "List all ticketed events on Eventbrite, Bandsintown, Ticketmaster, SeatGeek, and Songkick for passive discovery. Most are free to list.",
            "borrowed_from": "Drake Underground (on all major ticketing platforms), Lula Lounge (Eventbrite, Fever)",
            "type": "Marketing",
            "what_they_do_right": "Drake's multi-platform ticketing creates massive organic discoverability for out-of-town visitors and music tourists that social media alone can't reach.",
            "why_it_fits": "BC's comedy and live music nights are ticketable events. Each platform listing is a free discovery channel."
        },
        {
            "priority": 3,
            "action": "Package one signature live format that becomes synonymous with the room — use the church aesthetic as the story (e.g. 'The Cathedral Sessions').",
            "borrowed_from": "Ronnie Scott's, The Comedy Bar, Drake Underground ('Billie Eilish played our basement')",
            "type": "Brand",
            "what_they_do_right": "Ronnie Scott's = jazz. Comedy Bar = comedy. The venue and format become linked. Drake mythologizes every notable performer who played the room.",
            "why_it_fits": "The church stained-glass aesthetic is BC's most distinctive asset. Every performer photo taken in this room is inherently more shareable than a generic stage."
        },
        {
            "priority": 4,
            "action": "Add a participatory element to at least one night — comedy workshop, open jam session, interactive DJ set, or audience-vote format.",
            "borrowed_from": "Lula Lounge (free salsa dance lesson turns observers into participants)",
            "type": "Programming",
            "what_they_do_right": "Lula's free dance lesson is the hook that creates stickiness — people come back because they're part of the experience, not just watching it.",
            "why_it_fits": "BC's open mic Monday already has this DNA. Expanding participatory elements to other nights builds community and repeat visits."
        },
        {
            "priority": 5,
            "action": "Build a private events offering with a dedicated webpage, inquiry flow, capacity specs, and AV details. Price from $40-50/guest for cocktail receptions.",
            "borrowed_from": "Drake Underground (private events subsidize programming), Duke of Cornwall (dedicated party planner page)",
            "type": "Revenue",
            "what_they_do_right": "Drake uses the Underground for corporate events with two bars, full AV, and custom menus. This revenue stream subsidizes programming nights.",
            "why_it_fits": "BC has the room, the aesthetic, and the AV infrastructure. A private events page converts corporate/birthday inquiries that currently go elsewhere."
        },
        {
            "priority": 6,
            "action": "Introduce a competitive happy hour ($5-6 beer, 4-7pm) to build an early-evening pipeline that feeds into the night's programming.",
            "borrowed_from": "Drake Underground ($5 beer happy hour daily 3-6pm)",
            "type": "Pricing",
            "what_they_do_right": "Drake's $5 happy hour is a significant traffic driver that converts after-work visitors into evening stayers.",
            "why_it_fits": "BC's downtown location near offices and hotels can capture the 5-7pm after-work crowd if there's a reason to start the evening there."
        },
        {
            "priority": 7,
            "action": "Tighten the visual system — poster art, performer promos, and weekly recaps should compound. Mythologize every notable performer who plays the church space.",
            "borrowed_from": "Drake Underground, Bambi's, Lula Lounge",
            "type": "Marketing",
            "what_they_do_right": "They make nightlife programming feel like a world, not a list of dates. Drake dines out on 'Billie Eilish played our basement' for years.",
            "why_it_fits": "The church aesthetic makes every show photo inherently distinctive. Document and mythologize — this content compounds over time."
        },
        {
            "priority": 8,
            "action": "Chase one prestige press partnership — blogTO, NOW Toronto, Exclaim!, or a podcast network — for recurring coverage or a named series.",
            "borrowed_from": "Drake Underground (Billboard Canada partnership, TIFF collaboration)",
            "type": "Brand",
            "what_they_do_right": "Drake's press partnerships create ongoing earned media. One recurring media relationship > many one-off pitches.",
            "why_it_fits": "BC's church aesthetic + comedy/music programming is editorial-ready. A named partnership turns one ask into ongoing coverage."
        },
    ],
    "Eloise": [
        {
            "priority": 1,
            "action": "Introduce one recurring chef-led signature moment such as a weekly feature, seasonal tasting sidebar, or tableside finish ritual.",
            "borrowed_from": "Alo, Canoe, Edulis",
            "type": "Experience",
            "what_they_do_right": "They turn culinary credibility into talkable occasion-making, not just menu quality.",
            "why_it_fits": "Eloise has product depth already; it needs one sharper ritual people specifically come for."
        },
        {
            "priority": 2,
            "action": "Develop a clearer flagship dish-and-drink pairing that becomes the most easily recommended way to experience Eloise.",
            "borrowed_from": "Byblos, Piano Piano",
            "type": "Product",
            "what_they_do_right": "They simplify discovery by making one or two pairings feel like the obvious first order.",
            "why_it_fits": "Eloise's menu ambition is a strength, but guests still need an easy entry point."
        },
        {
            "priority": 3,
            "action": "Run limited seasonal dinner formats or collaboration nights that showcase the restaurant's global influences more explicitly.",
            "borrowed_from": "Alo, Marben",
            "type": "Programming",
            "what_they_do_right": "They use chef credibility and seasonality to create urgency around return visits.",
            "why_it_fits": "Eloise can deepen its positioning by making its point of view more eventized and easier to market."
        },
    ],
    "Scotland Yard": [
        {
            "priority": 1,
            "action": "Create one social-first hero food or drink item and tie it to a recurring game-day or weekly pub ritual.",
            "borrowed_from": "Score on King, Fox on John",
            "type": "Product",
            "what_they_do_right": "They pair sports energy with highly shareable items that keep group bookings and social posting moving.",
            "why_it_fits": "Scotland Yard already has traffic and heritage; it needs a more visual reason for people to plan and post."
        },
        {
            "priority": 2,
            "action": "Move from occasional promos to a consistent weekly content rhythm built around match hype, specials, and atmosphere.",
            "borrowed_from": "The Pint Public House, Fox on John",
            "type": "Marketing",
            "what_they_do_right": "They make the venue feel active every week, not only on major sports moments.",
            "why_it_fits": "Scotland Yard's low social cadence is leaving brand awareness and repeat traffic on the table."
        },
        {
            "priority": 3,
            "action": "Add one recurring non-sports weekly draw that broadens the audience without diluting the pub identity.",
            "borrowed_from": "House on Parliament, Loose Moose",
            "type": "Programming",
            "what_they_do_right": "They stay relevant beyond pure game-day traffic by giving locals another reason to return.",
            "why_it_fits": "The pub has institutional strength, but it can smooth demand with one more dependable off-peak ritual."
        },
    ],
    "Old Spaghetti Factory": [
        {
            "priority": 1,
            "action": "Package a nostalgia-led family event series with fixed-value bundles and clearer celebratory positioning.",
            "borrowed_from": "Olive Garden, Maggiano's",
            "type": "Programming",
            "what_they_do_right": "They convert familiar comfort food into planned family occasions instead of relying only on general traffic.",
            "why_it_fits": "Old Spaghetti Factory already has heritage and atmosphere; it should use them more actively."
        },
        {
            "priority": 2,
            "action": "Create one theatrical in-room signature moment that families expect and kids remember.",
            "borrowed_from": "Piano Piano, Buca di Beppo",
            "type": "Experience",
            "what_they_do_right": "They build memory through one distinctive presentation touch, not only portion size or decor.",
            "why_it_fits": "The brand is already visual and nostalgic; a stronger table moment would make it more recommendable."
        },
        {
            "priority": 3,
            "action": "Refresh the value story into easier-to-understand bundles for groups, birthdays, and multigenerational dining.",
            "borrowed_from": "Olive Garden, East Side Mario's",
            "type": "Pricing",
            "what_they_do_right": "They simplify the purchase decision for families and larger parties.",
            "why_it_fits": "Old Spaghetti Factory competes on comfort and value, so the offer structure should be doing more of the selling."
        },
    ],
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
            ["Bar Pompette", "Little Italy", "Award-winning cocktail bar with French bistro energy and Sunday jazz", "Automatically included: Canada's 100 Best / North America's 50 Best benchmark for Toronto cocktail bars"],
            ["Civil Liberties", "Bloor West", "No-menu bartender-led cocktail institution", "Automatically included: top-ranked Toronto cocktail benchmark and custom-drinks reference point"],
            ["Library Bar", "Financial District", "Luxury hotel cocktail bar with theatrical martini ritual", "Automatically included: top-ranked Toronto downtown cocktail benchmark"],
            ["Cocktail Bar", "Dundas West", "Hoof's cocktail-focused bar with bold flavour combinations", "Automatically included: Canada's 100 Best 2025 Toronto cocktail bar"],
            ["Mother", "Queen West", "Fermentation-forward cocktail bar with narrative drinks program", "Automatically included: Canada's 100 Best / North America's 50 Best benchmark"],
            ["Bar Mordecai", "Dundas West", "Design-led cocktail bar with nightlife and karaoke programming", "Automatically included: Canada's 100 Best / North America's 50 Best benchmark"],
            ["Bar Raval", "Little Italy", "Iconic design-led Spanish bar with serious cocktail credibility", "Automatically included: Canada's 100 Best benchmark and major citywide destination"],
            ["Civil Works", "King West", "Narrative-driven cocktail bar by the Civil Liberties team", "Automatically included: Canada's 100 Best 2025 Toronto cocktail bar"],
            ["Slice of Life Bar", "College St", "Modern speakeasy with lab-driven cocktail program", "Automatically included: Canada's 100 Best 2025 Toronto cocktail bar"],
            ["Simpl Things", "Roncesvalles / Parkdale West", "All-day cocktail, wine and snack bar", "Automatically included: Canada's 100 Best 2025 Toronto cocktail-adjacent bar"],
            ["Doc's Green Door Lounge", "Little Italy", "Intimate lounge and cocktail destination above Osteria Giulia", "Automatically included: Canada's 100 Best 2025 Toronto cocktail bar"],
            ["Prequel and Co. Apothecary", "Kensington", "Apothecary-themed speakeasy, hand-ground spices", "Canada's 100 Best-recognized theatrical speakeasy competitor"],
            ["Bar Banane", "Ossington", "Refined cocktail and dessert bar with strong date-night appeal", "OpenTable cross-check surfaced it as part of the same high-intent cocktail-booking set as Bar Pompette"],
            ["BarChef", "Queen West", "Long-running theatrical modernist cocktail bar", "Explicit cocktail-bar benchmark operating well beyond 2 years"],
            ["Gift Shop", "Ossington", "Hidden-room cocktail bar with strong bartender-bar credibility", "OpenTable reviewer-orbit overlap suggests it belongs in Bar Cart's citywide cocktail set"],
            ["Compton Ave.", "Dundas West", "British-inspired cocktail bar by BarChef/Frankie Solarik. Canada's 100 Best 2025.", "UK-inspired cocktail bar with food — direct concept overlap with Bar Cart's speakeasy positioning"],
            ["Project Gigglewater", "Cabbagetown", "Friendly neighbourhood cocktail bar", "Explicit cocktail-bar comp operating for more than 2 years"],
            ["À Toi", "Bloor-Yorkville", "Speakeasy and cocktail bar with entertainment programming", "Explicit cocktail-bar comp with premium Yorkville audience"],
            ["C Suite", "Yorkville", "Luxury cocktail lounge with premium booking demand", "OpenTable cross-check surfaced it as a premium special-occasion cocktail benchmark"],
            ["In Good Spirits", "Financial District", "Cocktail bar and restaurant focused on elevated after-work drinks", "Explicit cocktail-bar comp operating since 2019"],
            ["No Vacancy", "Ossington", "Mood-led cocktail bar and restaurant with date-night pull", "OpenTable cross-check surfaced it as a direct special-occasion cocktail competitor"],
            ["CKTL & Co.", "Financial District", "After-work cocktail lounge with strong happy-hour and group relevance", "OpenTable cross-check surfaced it as a downtown cocktail-occasion competitor"],
            ["Powder Room", "Yorkville", "New Yorkville cocktail bar and supper-club style room", "Requested Yorkville addition despite being newer than 2 years"],
            ["Midnight Market", "West Queen West", "Speakeasy, innovative cocktails, intimate vibe", "Top-rated Toronto speakeasy competitor for hidden-room demand"],
            ["After Seven", "Dundas West", "Japanese-inspired hidden whisky bar behind fake yogurt shop", "Speakeasy format, craft cocktails, similar audience"],
            ["Suite 115", "College St", "Passcode/vault entry speakeasy, distinctive cocktails", "Hidden bar concept, similar occasion"],
            ["Bar 404", "Dundas West", "Intimate cocktail bar, innovative program", "Craft cocktail bar competing for cocktail enthusiasts"],
            ["Lonely Diner", "Queen West", "New speakeasy by Midnight Market team, 1970s vibe", "Direct concept competitor — new, buzzy, craft cocktails"],
            ["Secrette", "King West", "Speakeasy behind GEORGE Restaurant, handcrafted cocktails + small plates", "Hidden bar behind restaurant — identical format to Bar Cart/Eloise"],
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
            ["The Berczy Tavern", "69 Front St E (Old Town)", "Contemporary global-influenced dining, live piano, same team as Amano (Angeloni/Teolis/Bigourdan)", "Blocks from Eloise, global influences + tableside energy, same chef group as Tier 1 #1"],
        ], columns=["Name", "Location", "Concept", "Why Competitor"]),
        "City-wide (Toronto)": pd.DataFrame([
            ["Alo", "Entertainment District", "Michelin-starred, French tasting menu", "Toronto's top chef-driven contemporary dining"],
            ["Canoe", "Financial District", "Canadian contemporary, seasonal, iconic views", "Contemporary Canadian with steakhouse elements"],
            ["Marben", "King West", "Contemporary Canadian, local ingredients, no-tipping", "Canadian contemporary with global influences"],
            ["Edulis", "King West", "Michelin-starred, seasonal/foraged, intimate", "Chef-driven intimate dining, similar scale"],
            ["Giulietta", "College St / Dufferin Grove", "Michelin-recognized Italian, polished neighbourhood destination", "Italian-contemporary competitor with strong room, service, and ingredient credibility"],
            ["Piano Piano", "Various", "Italian-forward contemporary, lively atmosphere", "Italian-contemporary crossover, similar energy"],
            ["Gusto 101", "Portland St", "Modern Italian, buzzy atmosphere", "Italian-contemporary, similar demographic"],
            ["Terroni", "Various", "Contemporary Italian, quality ingredients", "Italian dining across Toronto, brand recognition"],
            ["Byblos", "Entertainment District", "Eastern Mediterranean, global flavours", "Chef-driven, global influence, similar price point"],
            ["The Chase", "Financial District (rooftop)", "Contemporary North American, crudos, seafood, chef Nick Bentley (ex-Alo)", "Direct crudo/protein overlap, 4.8★ OpenTable, same diner profile"],
            ["The Frederick", "Financial District", "Contemporary comfort food by Cory Vitiello, 95-seat, steakhouse-adjacent", "Steakhouse swagger overlap, same upscale-casual positioning"],
            ["DaNico", "Little Italy (College St)", "Michelin-starred Italian tasting menu with Asian influences, #1 Foodism 2026", "Italian fine dining benchmark, global influence overlap"],
            ["Don Alfonso 1890", "Harbour Square (38th floor)", "Michelin-starred contemporary Italian, waterfront views", "Italian fine dining benchmark, tasting menu competitor"],
            ["Grey Gardens", "Kensington Market", "Michelin Bib Gourmand, seafood/vegetable-forward, outstanding wine", "Same food-forward diner crowd, wine-driven"],
            ["Jacobs & Co. Steakhouse", "Financial District (CIBC Square)", "Michelin-recognized premium steakhouse, live pianist", "Direct steakhouse-swagger competitor, premium positioning"],
            ["Akin", "Financial District (Colborne St)", "Michelin-starred, Asian-influenced blind tasting menu ($225)", "Global flavour integration, same Alo/Edulis diner circle"],
            ["Wynona", "East Chinatown", "Contemporary Canadian, seasonal, all-Ontario wine program", "Contemporary Canadian overlap, repeatedly appears alongside Canoe/Edulis"],
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
            ["King Taps", "100 King St W", "Large-format sports bar with 40+ taps, pizza and burgers", "Downtown sports and after-work bar competing for the same group and game-day occasions"],
            ["Walrus Pub & Beer Hall", "187 Bay St", "Financial-district pub and beer hall with cocktails, happy hour and event space", "Downtown pub/bar competing for after-work, sports, and group-booking occasions"],
            ["Duke's Refresher St Lawrence", "73 Front St E", "Retro bar & grill, games", "Casual bar in same corridor, pub food + games"],
            ["The Flatiron: A Firkin Pub", "49 Wellington St E", "British pub in Gooderham Building", "British pub in same block"],
            ["The Jason George", "100 Front St E", "Neighbourhood pub", "Neighbourhood pub competing for same regulars"],
            ["P.J. O'Brien Irish Pub & Restaurant", "39 Colborne St", "Upscale Irish pub", "Upscale pub nearby, different tradition but same occasion"],
            ["C'est What? Inc.", "67 Front St E", "Craft beer brewpub", "Craft beer pub in same corridor"],
            ["The WORKS Craft Burgers & Beer", "60 Wellington St E", "Gastropub, burgers + craft beer", "Gastropub in same block"],
            ["Berkeley Bistro", "262 The Esplanade", "Casual bistro/bar on same street", "Same street, casual pub-style dining"],
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
            ["The Dog & Bear", "Queen St W / Parkdale", "British pub, sports bar", "English pub concept competitor"],
            ["The Auld Spot Pub", "Danforth", "Traditional pub, sports, comfort food", "Long-running neighbourhood pub with sports focus"],
            ["The Loose Moose", "146 Front St W", "Beer hall, burgers, since 1989", "Long-running Toronto beer hall, similar pub dining"],
            ["The Pint Public House", "277 Front St W", "Large sports pub", "Sports pub competing for same game-day crowd"],
            ["Duke of Cornwall", "400 University Ave", "Traditional British pub", "British pub concept competitor"],
            ["The Fox on John", "106 John St", "Modern English restaurant & pub", "Pub competing for same casual occasion"],
            ["Madison Avenue Pub", "Bloor St", "Large multi-room bar", "Large-format pub/bar, similar social occasion"],
            ["The Commoner Roncy", "Roncesvalles", "Elevated neighbourhood gastro-pub with craft beer, cocktails, brunch and strong burger traffic", "Useful benchmark for a polished, food-forward Toronto pub that still feels approachable and repeatable"],
            ["The Caledonian", "856 College St (Ossington)", "Toronto's only Scottish pub & whisky bar, 200+ whiskies", "British Isles pub — Scottish vs SY's English. Whisky program benchmark."],
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

# COMPETITOR_PRICING is now imported from data.pricing_data (top of file)
# Old inline pricing block removed — see data/pricing_data.py
# _make_pricing_df and COMPETITOR_PRICING dict were here — now in pricing_data.py


# --- SY SOCIAL AUDIT DATA ---

SY_SOCIAL_AUDIT = pd.DataFrame([
    ["Scotland Yard", "@scotlandyardtoronto", 1903, 127, 4.7, 4109, "IG, FB", "~0.4"],
    ["Score on King", "@scoreonking", 10000, 572, 4.4, 1621, "IG, FB, TikTok", "~1.6"],
    ["King Taps", "@kingtaps", None, None, 4.3, 4500, "IG, FB", "~2.5"],
    ["Walrus Pub & Beer Hall", "@walrus.fc", None, None, 4.3, 2422, "IG, FB", "~2.0"],
    ["Duke's Refresher", "@dukesrefresherslm", 2997, 350, 4.0, 2200, "IG, FB", "~1.0"],
    ["The Flatiron (Firkin)", "@theflatironandfirkin", 866, 200, 4.1, 1138, "IG, FB, TikTok, Twitter", "~0.5"],
    ["The Jason George", "@the_jason_george", 657, 150, 4.2, 839, "IG, FB", "~0.4"],
    ["P.J. O'Brien", "@pjobrienpub", 3273, 400, 4.3, 1800, "IG, FB", "~1.0"],
    ["C'est What?", "@cestwhatto", 4006, 500, 4.5, 3400, "IG, FB", "~1.1"],
    ["The WORKS", "@works_burger", 50000, 1580, 4.2, 1500, "IG, FB", "~3.0"],
    ["The Keg", "@thekegsteakhouse", 117000, 1580, 4.3, 3000, "IG, FB, Twitter", "~3.0"],
    ["The Queen & Beaver", "@qbpub", 2772, 600, 4.3, 5200, "IG, FB", "~1.2"],
    ["Saint John's Tavern", "@saintjohnstavern", 2000, 300, 4.5, 700, "IG, FB", "~1.0"],
    ["Bramble Gastropub", "@bramble.toronto", 3415, 400, 4.5, 800, "IG, FB", "~1.2"],
    ["House on Parliament", "@hop_to", 5185, 897, 4.7, 2000, "IG, FB", "~1.7"],
    ["The Fortunate Fox", "@thefortunatefox", 3000, 400, 4.1, 1200, "IG, FB", "~1.0"],
    ["The Pilot", "@thepilot_to", 4000, 500, 4.0, 3900, "IG, FB, Twitter", "~1.0"],
    ["The Dog & Bear", "@thedogandbear", 2000, 300, 4.1, 1393, "IG, FB", "~0.8"],
    ["The Auld Spot Pub", "@theauldspot", 3000, 400, 4.5, 1000, "IG, FB", "~1.0"],
    ["The Loose Moose", "@loosemooseto", 4120, 942, 4.3, 7400, "IG, FB", "~1.8"],
    ["The Pint Public House", "@thepinttoronto", 9865, 800, 4.1, 2960, "IG, FB", "~1.7"],
    ["Duke of Cornwall", "@duke_pubs", 11000, 430, 4.5, 1049, "IG, FB", "~1.0"],
    ["The Fox on John", "@foxonjohn", 19000, 1685, 4.6, 5500, "IG, FB, TikTok, Twitter", "~3.6"],
    ["Madison Avenue Pub", "@madisonavenuepub", 14000, 2151, 4.0, 2000, "IG, FB", "~3.8"],
    ["The Commoner Roncy", "@thecommonerrestaurant", None, None, 4.4, 882, "IG, FB", "~2.0"],
    ["The Caledonian", "@thecaledonian", 5102, 2280, 4.7, 1195, "IG, FB, Twitter", "~2.7"],
], columns=["Name", "Instagram", "IG Followers", "Total Posts", "Google Rating", "Google Reviews", "Platforms", "Est. Posts/Week"])

# Flag chain/multi-location IG accounts with asterisk on follower count
# Keep numeric column for charts, add display column for tables
_CHAIN_IG_NOTES = {"The Keg": "* (100+ locations)", "The WORKS": "* (27+ locations)", "Duke of Cornwall": "* (3 locations)"}
SY_SOCIAL_AUDIT["IG Note"] = SY_SOCIAL_AUDIT["Name"].map(_CHAIN_IG_NOTES).fillna("")
SY_SOCIAL_AUDIT["IG Followers Display"] = SY_SOCIAL_AUDIT.apply(
    lambda r: (f"{int(r['IG Followers']):,}" if pd.notna(r["IG Followers"]) else "n/a") + r["IG Note"], axis=1,
)

BC_SOCIAL_AUDIT = pd.DataFrame([
    ["Bar Cathedral", "@barcathedral", "IG", "~4-5", "Moody interiors, nightlife energy, DJ/live performance promos, creator-friendly party shots", "Comedy Sun, open mic Mon, live music Tue-Thu, DJs Fri-Sat", "Moderate", "The core opportunity is consistency: turn the weekly calendar into recognizable recurring content franchises."],
    ["The Reservoir Lounge", "@reservoirlounge", "IG, FB", "~2-3", "Vintage jazz identity, live-band clips, room atmosphere, date-night tone", "Nightly jazz/blues programming", "Moderate", "A clear entertainment identity can outweigh a smaller footprint if the venue owns one music lane."],
    ["C'est What", "@cestwhatto", "IG, FB", "~1-2", "Beer culture, cellar credibility, casual community moments, event flyers", "Live music and comedy nights layered into a pub format", "Moderate", "Longstanding venues use familiarity and community proof more than polished nightlife imagery."],
    ["HOTHOUSE", "@hothouserestaurant", "IG, FB", "~1-2", "Brunch, live music, event moments, broad-appeal food content", "Live music and special-event dining occasions", "Low to Moderate", "Programming attached to established meal occasions broadens audience beyond nightlife-only demand."],
    ["The Rivoli", "@rivolitoronto", "IG, FB", "~2-4", "Poster-style show promos, artist announcements, legacy venue cues", "Live music, comedy, club-style nights", "Moderate", "Strong programming brands are often communicated through lineup authority more than polished visuals."],
    ["El Mocambo", "@elmocambotoronto", "IG, FB, TikTok", "~3-5", "Artist-led promotion, marquee shots, concert crowd energy", "Ticketed live music and branded event nights", "High", "When talent is the draw, the venue can let bookings drive content and urgency."],
    ["The Cameron House", "@thecameronhouse", "IG, FB", "~2-3", "Singer-songwriter intimacy, listings-heavy promotion, heritage venue voice", "Dense live-music calendar", "Moderate", "A compact room can win by foregrounding authenticity and scene credibility."],
    ["The Painted Lady", "@thepaintedladytoronto", "IG, FB", "~2-3", "Cabaret visuals, cocktails, performance glamour, nightlife portraits", "Burlesque, live music, themed entertainment", "Moderate to High", "Distinct visual world-building makes recurring entertainment feel like a branded experience."],
    ["Drake Underground", "@thedrakehotel", "IG, FB, TikTok", "~5-7", "Editorial nightlife imagery, artist/talent content, culture-forward design", "Concerts, DJ nights, culture programming", "High", "Institutional nightlife brands win by making every event feel part of a larger cultural platform."],
    ["The Handlebar", "@thehandlebarto", "IG, FB", "~2-4", "Flyer-driven promos, party photos, local-scene familiarity", "Live music, DJ nights, club programming", "Moderate", "Low-fi but frequent event promotion can still be effective if the calendar is strong."],
    ["Bambi's", "@bambis_to", "IG, FB", "~3-5", "Underground dance identity, poster graphics, artist-led club messaging", "DJ-led nightlife programming", "Moderate to High", "Subcultural venues often lean on taste and community signaling over broad hospitality messaging."],
    ["Lula Lounge", "@lulalounge", "IG, FB, YouTube", "~2-4", "Dance-floor energy, Latin music, cultural storytelling, class/event promos", "Live music, dance classes, cultural nights", "Moderate", "Programming depth is strongest when it spans multiple participation modes, not just passive attendance."],
    ["The Comedy Bar", "@thecomedybar", "IG, FB, TikTok", "~4-6", "Lineup cards, comedian clips, ticket pushes, crowd reaction moments", "Stand-up, showcases, themed comedy nights", "High", "Comedy venues create repeat behavior by making the weekly lineup itself the product."],
    ["Yuk Yuk's Toronto", "@yukyukstoronto", "IG, FB", "~2-4", "Comedian promos, host announcements, touring talent", "Stand-up comedy nights", "Moderate", "Talent-led promotion keeps content clear even when venue aesthetics are secondary."],
    ["Track & Field", "@trackandfieldbar", "IG, FB", "~2-4", "Game-play clips, group-night energy, party snapshots, social-occasion promotion", "Recreational bar nights, private parties, group-driven bookings", "Moderate to High", "Experience-first bars sell the participation and group atmosphere more than product detail."],
    ["Dance Cave", "@dancecavetoronto", "IG, FB", "~2-4", "Alt-night posters, dance-floor shots, DJ/event flyers, nostalgia-party energy", "Weekend dance parties, themed indie/alt nights", "Moderate to High", "A strong recurring nightlife identity works when the same party promise is reinforced every week."],
    ["Madison Avenue Pub", "@madisonavenuepub", "IG, FB, TikTok", "~3-4", "High-volume nightlife shots, student/social energy, event promos", "Multi-room party nights and themed socials", "High", "Large-format venues compete on scale and social proof rather than intimacy."],
], columns=["Name", "Instagram", "Platforms", "Est. Posts/Week", "Content Themes", "Programming Signals", "Engagement Read", "Why It Matters"])

ELOISE_SOCIAL_AUDIT = pd.DataFrame([
    ["Eloise", "@eloisetoronto", 4311, 93, 4.6, 121, "IG", "~2.0", "Single location", "Creative plating, room mood, service moments, Bar Cart crossover", "Moderate", "Strong local momentum, but still small relative to Toronto premium-dining leaders."],
    ["Alo", "@alorestaurant", 50000, None, 4.6, 1989, "IG", "~2.5", "Venue-specific group account", "Luxury food shots, tasting-menu storytelling, hospitality polish", "High", "Sets the prestige-service benchmark for Toronto fine dining."],
    ["Canoe", "@canoe.toronto", 47000, None, 4.1, 670, "IG", "~2.5", "Venue-specific group account", "Skyline views, premium plating, business-dining polish", "High", "Owns the polished occasion-dining lane with a very legible use case."],
    ["SAMMARCO", "@sammarcotoronto", 12000, None, 4.8, 177, "IG", "~3.0", "Single location", "Luxury room shots, steak-and-seafood glamour, founder halo", "Moderate to High", "Competes directly on premium energy and visual desirability."],
    ["Giulietta", "@giulietta972", None, None, 4.5, 910, "IG", "~2.0", "Single location", "Refined Italian plates, warm room details, polished neighbourhood luxury", "Moderate", "Represents the premium-but-approachable Italian benchmark Eloise overlaps with."],
    ["Cluny Bistro", "@clunybistro", 21000, None, None, None, "IG", "~2.5", "Single location", "Design-forward dining room, polished French-bistro plates, celebration moments", "Moderate", "Shows how room design can drive destination dining interest."],
    ["Edulis", "@edulisrestaurant", 24000, None, None, None, "IG", "~1.5", "Single location", "Chef-led food storytelling, ingredient authority, intimate luxury", "Moderate", "Wins through scarcity, intimacy, and culinary seriousness rather than volume."],
    ["Piano Piano", "@pianopianotherestaurant", 49000, None, None, None, "IG", "~4.0", "Chain account", "Playful interiors, high-frequency food content, broad celebration appeal", "High", "Very strong scale and visual friendliness, but follower count is chain-inflated."],
    ["Gusto 101", "@gusto101to", 25000, None, None, None, "IG", "~3.0", "Venue-specific group account", "Buzzy room, modern Italian plates, rooftop and social-table energy", "Moderate to High", "A strong benchmark for urban, high-volume Italian-contemporary relevance."],
    ["Terroni", "@terronito", 36000, None, None, None, "IG", "~3.0", "Chain account", "Classic Italian brand cues, high-volume food content, broad familiarity", "High", "Brand scale is real, but follower count reflects multiple locations."],
    ["Byblos", "@byblostoronto", 13000, None, None, None, "IG", "~2.0", "Venue-specific group account", "Moody luxury, global-flavour dishes, fashionable dining-room imagery", "Moderate", "Useful benchmark for how a premium restaurant turns flavour point of view into brand identity."],
], columns=["Name", "Instagram", "IG Followers", "Total Posts", "Google Rating", "Google Reviews", "Platforms", "Est. Posts/Week", "Account Scope", "Content Themes", "Engagement Read", "Why It Matters"])

ELOISE_DEMAND_AUDIT = pd.DataFrame([
    ["Eloise", 4.6, 121, 12, "2026-04-04", "Moderate", "Fri-Sat dinner; Bar Cart spillover; special-occasion and date-night demand", "Tue-Thu lunch and early dinner", "Reservations are recommended on weekends; lunch prix-fixe and quieter midweek windows are the clearest demand-building opportunities."],
    ["Alo", 4.8, 629, 11, "2026-04-05", "Moderate", "Tue-Sat tasting-menu dinner; occasion-led fine dining", "No true low-friction period; earlier seatings are calmer", "Despite elite positioning, Alo's booked-today count is lower because the format is narrower and higher commitment than Eloise's."],
    ["Canoe", 4.6, 6708, 84, "2026-04-05", "Very High", "Weekday lunch, sunset dinner, business dining, scenic special occasions", "Early-week lunches are the calmest", "One of the clearest examples of a restaurant owning multiple demand peaks: business lunch, bar, and special-occasion dinner."],
    ["SAMMARCO", 4.7, 241, 24, "2026-04-04", "High", "Fri-Sat celebratory dinner; luxury night-out demand", "Early weekday evenings / first seating", "Stronger current reservation velocity than Eloise, with a more legible celebratory use case and heavier premium signalling."],
    ["Giulietta", 4.8, 2617, 54, "2026-04-04", "Very High", "Fri-Sat dinner and peak evening seatings; special-occasion Italian demand", "Mon-Thu and earlier seatings", "Extremely strong booking velocity for a single-location neighbourhood restaurant; this is a major benchmark for Eloise's reservation ceiling."],
    ["Cluny", 4.4, 5841, 40, "2026-04-05", "High", "Weekend brunch, Fri-Sat dinner, Distillery tourism and holiday traffic", "Midweek evenings and earlier dinners", "Cluny shows how district-based destination traffic and brunch can materially deepen demand beyond dinner only."],
    ["Piano Piano Colborne", 4.7, 459, 73, "2026-04-05", "Very High", "Daily dinner, weekend nights, lunch, happy hour, celebration dining", "Weekday lunch and early weeknight reservations", "This is the strongest nearby St. Lawrence demand benchmark because it layers lunch, happy hour, and dinner into one address."],
    ["Byblos Downtown", 4.7, 4275, 56, "2026-03-19", "Very High", "Thu-Sat dinner, group dining, pre-theatre and special occasions", "Weekday or Sunday early dinner", "Byblos combines destination appeal with a clear group-sharing proposition; that makes its booking velocity consistently strong."],
], columns=["Name", "OpenTable Rating", "OpenTable Reviews", "Booked Today", "Snapshot Date", "Velocity Tier", "Peak Demand", "Quiet Window", "Reservation Read"])

ELOISE_DEMAND_SOURCES = pd.DataFrame([
    ["Eloise", "https://www.opentable.ca/r/eloise-toronto"],
    ["Alo", "https://www.opentable.ca/r/alo-restaurant"],
    ["Canoe", "https://www.opentable.ca/canoe-restaurant-and-bar"],
    ["SAMMARCO", "https://www.opentable.ca/r/sammarco-toronto"],
    ["Giulietta", "https://www.opentable.ca/r/giulietta-toronto"],
    ["Cluny", "https://www.opentable.ca/cluny"],
    ["Piano Piano Colborne", "https://www.opentable.ca/r/piano-piano-colborne-toronto"],
    ["Byblos Downtown", "https://www.opentable.ca/r/byblos-toronto"],
], columns=["Name", "URL"])

LOCAL_SEARCH_AUDIT = pd.DataFrame([
    ["Scotland Yard", 4.6, 4600, "4 / 10", "B", "#1 'pub near esplanade'", "Invisible for 'english pub toronto', 'british pub toronto', 'pub with patio toronto'", "Add GBP categories: British Restaurant, English Pub, Sports Bar; rewrite description with St. Lawrence Market + patio keywords; seed 5–10 Google Q&As"],
    ["Bar Cart", None, 50, "0 / 10", "F", "None — zero keyword visibility", "No TripAdvisor listing, no Yelp listing, name collides with furniture results, not on any 2026 'best bar' list", "Create TripAdvisor + Yelp listings; claim/optimise GBP with 50+ photos; launch review campaign (QR codes); pitch Foodism, BlogTO, Destination Toronto"],
    ["Bar Cathedral", 4.5, 130, "4 / 10", "C-", "#1 'nightclub esplanade toronto', #3 'DJ bar toronto'", "Review count 7–30x behind competitors (Reservoir Lounge: 900, Horseshoe: 2,000+); invisible for 'live music bar toronto'", "Review generation campaign (target 50+/quarter); correct GBP categories to Night Club + Live Music Venue; upload 50+ photos"],
    ["Eloise", 4.6, 121, "1 / 10", "D", "Partial via blogTO for 'fine dining esplanade'", "Invisible for 9/10 high-intent queries; <150 reviews vs Cluny 5,035, The Keg 2,000+, Canoe 3,666", "Review campaign (target 50/month); upload 100+ professional photos; add GBP categories: Fine Dining, Canadian, Italian"],
    ["Old Spaghetti Factory", 4.4, 12793, "5 / 10", "B-", "#1 'spaghetti restaurant toronto', #1 'family restaurant toronto downtown'", "Missing from 'large group' searches (despite 600 seats), 'St Lawrence Market' proximity, 'casual italian'; no online booking", "Add online booking (OpenTable/Resy); add GBP categories: Family Restaurant, Pasta, Event Venue; add 'Good for groups' attribute"],
], columns=["Venue", "Google Rating", "Google Reviews", "Keyword Visibility", "Grade", "Strongest Keywords", "Critical Gaps", "Priority Actions"])

LOCAL_SEARCH_KEYWORDS = pd.DataFrame([
    ["Scotland Yard", "pub near the esplanade toronto", "#1", "Owns home turf"],
    ["Scotland Yard", "english pub toronto", "Absent", "Queen & Beaver dominates"],
    ["Scotland Yard", "british pub toronto", "Absent", "Same gap — SY not in results"],
    ["Scotland Yard", "best pub toronto", "Absent", "Dominated by listicles"],
    ["Scotland Yard", "sports bar esplanade toronto", "Partial", "Appears in some results"],
    ["Scotland Yard", "bar near st lawrence market", "Absent", "CC Lounge, Paddington's, The Keg win"],
    ["Scotland Yard", "pub with patio toronto downtown", "Absent", "Rabbit Hole, Elephant & Castle win"],
    ["Scotland Yard", "happy hour esplanade toronto", "Absent", "The Keg and Bar Cathedral appear instead"],
    ["Bar Cart", "cocktail bar esplanade toronto", "Absent", ""],
    ["Bar Cart", "speakeasy toronto", "Absent", "Cry Baby Gallery, BarChef dominate"],
    ["Bar Cart", "best cocktail bar toronto", "Absent", "Bar Raval, Civil Liberties, Pretty Ugly dominate"],
    ["Bar Cart", "hidden bar toronto", "Absent", "Cry Baby Gallery, Shameful Tiki Room win"],
    ["Bar Cart", "date night bar toronto", "Absent", ""],
    ["Bar Cart", "cocktail lounge toronto", "Absent", ""],
    ["Bar Cathedral", "nightclub esplanade toronto", "#1", "Owns this niche"],
    ["Bar Cathedral", "DJ bar toronto downtown", "~#3", ""],
    ["Bar Cathedral", "dance bar toronto", "~#6", ""],
    ["Bar Cathedral", "bar with live music toronto downtown", "~#9", "Low position"],
    ["Bar Cathedral", "live music bar toronto", "Absent", "Horseshoe, Cameron House, Rex dominate"],
    ["Bar Cathedral", "intimate music venue toronto", "Absent", ""],
    ["Bar Cathedral", "late night bar toronto", "Absent", ""],
    ["Eloise", "fine dining esplanade toronto", "Partial", "Via blogTO listing, not direct"],
    ["Eloise", "contemporary restaurant toronto downtown", "Absent", "Canoe, Alo, Byblos dominate"],
    ["Eloise", "date night restaurant toronto downtown", "Absent", ""],
    ["Eloise", "special occasion restaurant toronto", "Absent", ""],
    ["Eloise", "chef driven restaurant toronto", "Absent", "Alo, Canoe, Edulis dominate"],
    ["Eloise", "steak restaurant esplanade toronto", "Absent", "The Keg dominates"],
    ["Eloise", "canadian contemporary dining toronto", "Absent", "Canoe, Marben appear"],
    ["Old Spaghetti Factory", "spaghetti restaurant toronto", "#1", "Brand name = keyword; dominant"],
    ["Old Spaghetti Factory", "family restaurant toronto downtown", "#1", "Strong listicle coverage"],
    ["Old Spaghetti Factory", "pasta restaurant toronto", "#1", "Brand name advantage"],
    ["Old Spaghetti Factory", "kid friendly restaurant toronto downtown", "~#2", "On most family dining listicles"],
    ["Old Spaghetti Factory", "italian restaurant esplanade toronto", "~#2", "Bellissimo beats it"],
    ["Old Spaghetti Factory", "casual italian restaurant toronto", "Absent", "NODO, Sugo, Gusto 101 dominate"],
    ["Old Spaghetti Factory", "large group restaurant toronto downtown", "Absent", "Despite 600 seats"],
    ["Old Spaghetti Factory", "family dinner near st lawrence market", "Absent", "HOTHOUSE, Cafe Oro win"],
], columns=["Venue", "Keyword", "Rank", "Notes"])

ELOISE_AWARD_COMPETITION = pd.DataFrame([
    ["Alo", "★ (2022–)", "#3", "95", "—", "✓", "—", "—", "—", "—"],
    ["Edulis", "★ (2022–)", "#4", "94", "—", "—", "—", "—", "—", "—"],
    ["DaNico", "★ (2024–)", "#59", "—", "#3 worldwide", "—", "—", "✓", "—", "—"],
    ["Don Alfonso 1890", "★ (2022–)", "#70", "78.5", "#13 worldwide", "✓", "#3", "✓", "—", "—"],
    ["Osteria Giulia", "★ (2022–)", "#72", "76", "Lunch of the Year", "✓", "—", "—", "—", "—"],
    ["Grey Gardens", "Bib Gourmand", "—", "—", "—", "✓", "—", "—", "—", "—"],
    ["Canoe", "Recommended", "#50", "—", "—", "—", "—", "—", "4 Diamond", "—"],
    ["Giulietta", "Recommended", "#96", "—", "—", "✓", "—", "—", "—", "—"],
    ["Jacobs & Co. Steakhouse", "Recommended", "—", "—", "—", "—", "—", "—", "—", "—"],
    ["SAMMARCO", "Recommended (new 2025)", "—", "—", "—", "—", "—", "—", "—", "—"],
    ["Scaramouche", "Recommended", "—", "—", "—", "✓", "—", "—", "—", "—"],
    ["The Chase", "—", "—", "—", "—", "✓", "#8", "—", "—", "—"],
    ["The Berczy Tavern", "—", "—", "—", "—", "—", "#13", "—", "—", "—"],
    ["Dreyfus", "Recommended", "#42", "—", "—", "—", "—", "—", "—", "—"],
    ["Bar Prima", "—", "#57", "—", "—", "✓", "#9", "—", "—", "—"],
    ["Bernhardt's", "—", "#45", "—", "—", "—", "#20", "—", "—", "—"],
], columns=["Name", "Michelin (2025)", "Canada's 100 Best", "La Liste", "50 Top Italy", "OpenTable Top 100", "Foodism (2026)", "Wine Spectator", "CAA Diamond", "NA 50 Best"])

OSF_SOCIAL_AUDIT = pd.DataFrame([
    ["Old Spaghetti Factory", "@oldspaghettifactoryto", 6157, 624, 4.4, 12793, "IG, FB", "~1.2"],
    ["Scaddabush", "@scaddabush", 24000, 2046, 4.5, 9900, "IG, FB", "~2.5"],
    ["East Side Mario's", "@eastsidemarios", 17000, 770, 4.6, 4978, "IG, FB, YouTube", "~1.8"],
    ["Olive Garden", "@olivegarden", 771000, 2304, 4.3, 5000, "IG, FB, TikTok, X", "~2.8"],
], columns=["Name", "Instagram", "IG Followers", "Total Posts", "Google Rating", "Google Reviews", "Platforms", "Est. Posts/Week"])

# --- BAR CART DEEP DIVE DATA ---

def load_bar_cart_deep_dive(base_path: Path):
    data_path = base_path / "data" / "bar_cart_deep_dive.json"
    with data_path.open() as f:
        data = json.load(f)
    snapshot = data["snapshot"]
    competitor_audit = pd.DataFrame(data["competitors"]).rename(
        columns={
            "name": "Name",
            "neighbourhood": "Neighbourhood",
            "google_rating": "Google Rating",
            "google_reviews": "Google Reviews",
            "review_quality": "Review Quality",
            "recognition": "Recognition",
            "primary_handle": "Primary Handle",
            "platforms": "Platforms",
            "cadence": "Cadence",
            "engagement": "Engagement",
            "hooks": "Hooks",
        }
    )
    programming = pd.DataFrame(data["programming"]).rename(
        columns={
            "bar": "Bar",
            "cadence_window": "Cadence Window",
            "programming": "Programming",
        }
    )
    recommendations = pd.DataFrame(data["recommendations"]).rename(
        columns={
            "priority": "Priority",
            "move": "Move",
            "why": "Why",
        }
    )
    return data, snapshot, competitor_audit, programming, recommendations


def _read_simple_xlsx(path: Path) -> pd.DataFrame:
    ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

    def col_to_idx(ref: str) -> int:
        letters = "".join(ch for ch in ref if ch.isalpha())
        idx = 0
        for ch in letters:
            idx = idx * 26 + (ord(ch.upper()) - 64)
        return idx - 1

    with ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall("main:si", ns):
                text = "".join(t.text or "" for t in si.iterfind(".//main:t", ns))
                shared.append(text)

        def cell_value(cell) -> str:
            cell_type = cell.attrib.get("t")
            value = cell.find("main:v", ns)
            if value is None:
                return ""
            raw = value.text or ""
            if cell_type == "s":
                return shared[int(raw)]
            return raw

        sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
        rows = sheet.find("main:sheetData", ns)
        parsed_rows = []
        max_idx = 0
        for row in rows.findall("main:row", ns):
            values = {}
            for cell in row.findall("main:c", ns):
                idx = col_to_idx(cell.attrib["r"])
                values[idx] = cell_value(cell)
                max_idx = max(max_idx, idx)
            parsed_rows.append(values)

    header = [parsed_rows[0].get(i, "") for i in range(max_idx + 1)]
    records = []
    for row in parsed_rows[1:]:
        record = {header[i]: row.get(i, "") for i in range(len(header)) if header[i]}
        if any(str(v).strip() for v in record.values()):
            records.append(record)
    return pd.DataFrame(records)


def _clean_research_df(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned = cleaned.loc[:, [col for col in cleaned.columns if str(col).strip()]]
    cleaned = cleaned.apply(lambda col: col.map(lambda value: value.strip() if isinstance(value, str) else value))
    if "Name" in cleaned.columns:
        cleaned = cleaned[cleaned["Name"].astype(str).str.strip() != ""]
        cleaned = cleaned[~cleaned["Name"].astype(str).str.lower().eq("nan")]
    return cleaned.reset_index(drop=True)


def load_venue_research_tables(base_path: Path) -> dict:
    research_root = base_path.parent / "Esplanade Restaurants" / "_general" / "competitor_research"
    tables = {}
    for venue, filename in VENUE_RESEARCH_FILES.items():
        path = research_root / filename
        if not path.exists():
            continue
        if path.suffix.lower() == ".csv":
            df = pd.read_csv(path)
        else:
            df = _read_simple_xlsx(path)
        tables[venue] = _clean_research_df(df)
    return tables
