"""Master lookup table for Google ratings, review counts, and IG data.
Used to fill gaps in the Portfolio view. Updated April 2026.
Sources: WebSearch, RestaurantGuru, Yelp, TripAdvisor, Instagram profiles.
"""

# Format: "Name": (google_rating, google_reviews, ig_handle, ig_followers)
# None = not found / not applicable

COMPETITOR_LOOKUP = {
    # === SCOTLAND YARD LOCAL ===
    "C'est What? Inc.": (4.5, 3400, "@cestwhatto", 4006),
    "P.J. O'Brien Irish Pub & Restaurant": (4.3, 1800, "@pjobrienpub", 3273),
    "Berkeley Bistro": (4.7, 298, "@berkeleycafeto", 740),  # now Berkeley Cafe
    "Duke's Refresher St Lawrence": (4.0, 2200, "@dukesrefresherslm", 2997),
    "The Flatiron: A Firkin Pub": (4.1, 1138, "@theflatironandfirkin", 866),
    "The Keg Steakhouse": (4.3, 3000, "@thekegsteakhouse*", 117000),  # chain
    "The WORKS Craft Burgers & Beer": (4.2, 1500, "@works_burger*", 50000),  # chain
    "St. Lawrence Cafe": (4.4, 500, None, None),
    "The Jason George": (4.2, 839, "@the_jason_george", 657),
    "Score on King": (4.4, 1621, "@scoreonking", 10000),
    # === SCOTLAND YARD CITY-WIDE ===
    "The Queen & Beaver Public House": (4.3, 5200, "@qbpub", 2772),
    "Saint John's Tavern": (4.5, 700, "@saintjohnstavern", 2000),
    "Bramble Gastropub": (4.5, 800, "@bramble.toronto", 3415),
    "House on Parliament": (4.7, 2000, "@hop_to", 5185),
    "The Fortunate Fox": (4.1, 1200, "@thefortunatefox", 3000),
    "The Pilot": (4.0, 3900, "@thepilot_to", 4000),
    "The Dog & Bear": (4.1, 1393, "@thedogandbear", 2000),
    "The Auld Spot Pub": (4.5, 1245, "@theauldspotpub", 3157),
    "The Loose Moose": (4.3, 7400, "@loosemooseto", 4120),
    "The Pint Public House": (4.1, 2960, "@thepinttoronto", 9865),
    "Duke of Cornwall": (4.2, 791, "@duke_pubs*", 11000),  # 3 locations
    "The Fox on John": (4.6, 5500, "@foxonjohn", 19000),
    "Madison Avenue Pub": (4.0, 2000, "@madisonavenuepub", 14000),
    "The Caledonian": (4.7, 1195, "@thecaledonian", 5102),
    # === SCOTLAND YARD GLOBAL ===
    "The Hand & Flowers": (4.6, 3500, "@handfmarlow", 132000),
    "The Unruly Pig": (4.5, 2200, "@unrulypig", 37000),
    "The Eagle": (4.3, 1800, "@eaglefarringdon", 12000),
    "The Sportsman": (4.5, 1800, "@sportsmankent", 31000),
    "The Devonshire": (4.4, 1500, "@devonshiresoho", 174000),
    "The Star Inn": (4.7, 914, "@thestarinnatharome", 22000),
    "Ye Olde Cheshire Cheese": (4.3, 10700, "@yeoldecheshirecheese_", 5600),
    "The Churchill Arms": (4.5, 11800, "@churchillarmsw8", 29000),

    # === BAR CART LOCAL ===
    "CC Lounge & Whisky Bar": (4.3, 800, "@cconfront", 8500),
    "LIBRARY BAR": (4.5, 600, "@librarybartoronto", 13000),
    "Bar Notte": (4.2, 200, "@barnottesocialclub", 2900),  # closed/rebranded
    "Clockwork Champagne & Cocktails": (4.6, 400, "@clockworktoronto", 17000),
    "Taberna Social": (4.3, 100, "@tabernasocialto", 1500),
    "The Reservoir Lounge": (4.5, 800, "@reservoirlounge", 3500),
    # === BAR CART CITY-WIDE ===
    "Bar Pompette": (4.8, 153, "@barpompette_to", 19000),
    "Civil Liberties": (4.7, 1247, "@civlibto", 15000),
    "Library Bar": (4.5, 600, "@librarybartoronto", 13000),
    "Mother": (4.7, 980, "@mothercocktailbar", 20000),
    "Bar Mordecai": (4.3, 400, "@barmordecai", 14000),
    "Bar Raval": (4.4, 3095, "@bar_raval", 48000),
    "BarChef": (4.7, 500, "@barchef", 15000),
    "Compton Ave.": (4.7, 42, "@barcomptonave", 16000),
    "Midnight Market": (4.5, 300, "@midnightmkt", 5600),
    "After Seven": (4.4, 400, "@barafterseven", 7688),
    "Secrette": (4.3, 150, "@secretteonqueen", 1873),
    "À Toi": (4.5, 300, "@atoitoronto", 7200),
    "Project Gigglewater": (4.6, 500, "@projectgigglewater", 6000),
    "Suite 115": (4.5, 200, "@suite115.to", 8785),
    "Bar 404": (4.6, 200, "@bar404toronto", 4452),
    "Lonely Diner": (4.5, 100, "@lonely_diner", 4770),
    "The Little Jerry": (4.5, 300, "@littlejerryto", 17000),
    "Prequel and Co. Apothecary": (4.6, 295, "@barprequel", 40000),
    "Civil Works": (4.6, 200, "@civilworksto", 5000),
    "Slice of Life Bar": (4.5, 150, "@sliceoflifebar", 4000),
    "Doc's Green Door Lounge": (4.6, 100, "@docsgreendr", 3000),
    "Cocktail Bar": (4.5, 400, "@cocktailbarto", 8000),
    "Simpl Things": (4.5, 200, "@simplthingsto", 3000),
    "Powder Room": (4.5, 100, "@powderroomto", 4000),
    "In Good Spirits": (4.4, 300, "@ingoodspiritsto", 5000),
    # === BAR CART GLOBAL ===
    "Handshake Speakeasy": (4.7, 2000, "@handshakespeakeasy", 85000),
    "Tayēr + Elementary": (4.6, 1500, "@tayerelementary", 55000),
    "Connaught Bar": (4.6, 2000, "@connaughtbar", 45000),
    "Attaboy": (4.7, 800, "@attaboy_nyc", 25000),
    "Please Don't Tell (PDT)": (4.5, 1200, "@pdtnyc", 30000),
    "Cloakroom Bar": (4.7, 500, "@cloakroombar", 12000),
    "Bar Dominion": (4.5, 300, "@bardominionmtl", 8000),
    "Paradiso": (4.6, 3000, "@paradisobarcelona", 120000),

    # === BAR CATHEDRAL LOCAL ===
    "Sneaky Dee's": (4.2, 4000, "@thesneakydees", 34000),
    "The Reservoir Lounge": (4.5, 800, "@reservoirlounge", 3500),
    "C'est What": (4.5, 3400, "@cestwhatto", 4006),
    "HOTHOUSE": (4.0, 500, "@hothouserestaurant", 2000),
    "The Berczy": (4.3, 400, "@theberczytavern", 5000),
    "The Rivoli": (4.3, 1500, "@rivolitoronto", 13000),
    "El Mocambo": (4.2, 1000, "@theelmocambo", 26000),
    "The Cameron House": (4.5, 800, "@the.cameronhouse", 12000),
    "Bovine Sex Club": (4.1, 600, "@bovinesexclub", 17000),
    "The Painted Lady": (4.4, 500, "@paintedladyossington", 12000),
    # === BAR CATHEDRAL CITY-WIDE ===
    "Drake Underground": (4.3, 200, "@drakeunderground", 9441),
    "The Handlebar": (4.3, 500, "@handlebar_to", 5000),
    "Bambi's": (4.3, 300, "@bambistoronto", 8000),
    "BSMT 254": (4.2, 50, "@bsmt254", 3000),
    "Lula Lounge": (4.0, 1200, "@lulalounge", 27000),
    "The Comedy Bar": (4.5, 800, "@comedybarto", 20000),
    "Yuk Yuk's": (4.3, 500, "@yukyukscomedy*", 18000),  # chain ~16 locations
    "Ada Slaight Hall": (4.5, 200, None, None),  # event venue, no IG
    "Bangarang": (4.2, 300, "@bangarangbar", 6981),
    "Track & Field": (4.3, 500, "@trackandfieldbar", 9400),
    "Dance Cave": (4.0, 300, "@thedancecave", 4200),
    "Madison Avenue Pub": (4.0, 2000, "@madisonavenuepub", 14000),
    # === BAR CATHEDRAL GLOBAL ===
    "Ronnie Scott's": (4.5, 5000, "@ronniescotts", 95000),
    "Blue Note Jazz Club": (4.5, 8000, "@bluenotenyc", 180000),
    "The Troubadour": (4.5, 1500, "@troubadourlondon", 15000),
    "Rockwood Music Hall": (None, None, None, None),  # CLOSED
    "Union Chapel": (4.6, 2000, "@unionchapeluk", 30000),
    "The Commune": (4.4, 300, "@communenyc", 8000),

    # === ELOISE LOCAL ===
    "Amano Trattoria": (4.4, 1500, "@trattoria.amano", 6700),
    "The Keg Steakhouse": (4.3, 3000, "@thekegsteakhouse*", 117000),
    "Cluny Bistro": (4.3, 1000, "@clunydistillery", 21000),
    "SAMMARCO": (4.5, 500, "@sammarcosteak", 12000),
    "The Rosebud": (4.5, 400, "@rosebudto", 5000),
    "Archeo": (4.6, 159, "@archeotoronto", 3007),
    "Bindia Indian Bistro": (4.4, 800, "@bindiaindianbistro", 1600),
    # === ELOISE CITY-WIDE ===
    "Alo": (4.8, 1000, "@alorestaurant", 50000),
    "Canoe": (4.3, 2000, "@canoerestaurant", 47000),
    "Marben": (None, None, None, None),  # CLOSED
    "Edulis": (4.7, 500, "@edulisrestaurant", 24000),
    "Piano Piano": (4.4, 2000, "@pianopianotherestaurant*", 49000),  # 7 locations
    "Gusto 101": (4.3, 1500, "@gusto101to", 25000),
    "Terroni": (4.3, 3000, "@terroni.to*", 36000),  # ~12 locations
    "Byblos": (4.4, 1500, "@byblostoronto", 13000),
    "Giulietta": (4.6, 1197, "@giulietta972", 28000),
    "Don Alfonso 1890": (4.0, 810, "@donalfonsoto", 34000),
    "Grey Gardens": (4.6, 256, "@greygardens199", 11000),
    "Jacobs & Co. Steakhouse": (4.6, 2737, "@jacobssteakhouse", 19000),
    "The Chase": (4.4, 1000, "@thechaseto", 22000),
    "DaNico": (4.7, 169, "@danico.to", 18000),  # #3 Italian restaurant in world (50 Top Italy 2026)
    "Wynona": (4.5, 619, "@wynonatoronto", 16000),
    "Akin": (4.6, 500, "@akin.toronto", 10000),
    "The Frederick": (4.5, 400, "@thefrederickto", 8000),
    "The Berczy Tavern": (4.3, 400, "@theberczytavern", 5000),
    # === ELOISE GLOBAL ===
    "Lyle's": (None, None, None, None),  # CLOSED
    "Le Coucou": (4.5, 1554, "@lecoucou_nyc", 104000),
    "Estela": (4.5, 1346, "@estelanyc", 120000),
    "Bavel": (4.6, 820, "@baveldtla", 67000),
    "Candide": (4.7, 700, "@restaurant_candide", 15000),
    "Le Violon": (4.6, 301, "@leviolonmontreal", 29000),
    "Alma": (4.4, 400, "@alma.mtl", 29000),
    "Momofuku Ko": (None, None, None, None),  # CLOSED

    # === OSF LOCAL ===
    "Bellissimo Pizzeria & Ristorante": (4.3, 931, "@bellissimo164", 283),
    "Amano Italian Kitchen": (4.4, 1500, "@eat.amano", 8647),  # now Notte Ristorante (Jan 2026)
    "Cantina Mercatto": (4.3, 800, "@mercatto.to*", 7201),  # Mercatto group, multiple locations
    "Jack Astor's": (4.2, 8154, "@jack_astors*", 23000),  # SIR Corp, ~35 locations
    "Boston Pizza": (4.2, 2660, "@bostonpizzacanada*", 58000),  # 383 locations
    "Scaddabush Italian Kitchen & Bar": (4.5, 2000, "@scaddabush*", 24000),  # SIR Corp, ~10 locations
    # === OSF CITY-WIDE ===
    "Il Fornello": (4.3, 1122, "@ilfornello*", 3865),  # ~6 locations
    "Mangiare": (4.7, 239, "@mangiare.to", 4008),
    "The Good Son Restaurant": (4.4, 1620, "@thegoodson_to", 17000),
    "Piano Piano Restaurant": (4.3, 2000, "@pianopianotherestaurant*", 49000),  # 7 locations
    "Paisano's": (4.2, 1500, "@paisanosoriginal", 577),  # alt: @paisanos_orginal 2,345
    "Moxie's": (4.2, 1500, "@moxiescanada*", 203000),  # 50+ locations; also @moxies 185K
    "The Pickle Barrel": (4.1, 1000, "@thepicklebarrel*", 4995),  # ~12 locations
    "Montana's": (4.3, 1500, "@montanasbbq*", 27000),  # ~94 locations
    "Joey Restaurants": (4.9, 11349, "@joeyrestaurants*", 99000),  # 34+ locations (King St)
    "Gusto 101 / Gusto 54": (4.3, 1500, "@gusto101to", 25000),  # also @gusto54restaurantgroup 2,920
    "Uncle Tony's": (3.7, 400, "@uncletonysto", 614),
    "Café Diplomatico": (4.2, 3000, "@cafedip", 11000),
    # === OSF GLOBAL ===
    "Olive Garden": (4.2, 5000, "@olivegarden*", 771000),  # 900+ locations
    "Maggiano's Little Italy": (4.4, 3000, "@maggianoslittleitaly*", 127000),  # 49+ locations
    "Buca di Beppo": (4.1, 2000, "@bucadibeppo*", 85000),  # 40 locations
    "Carrabba's Italian Grill": (4.2, 1700, "@carrabbas*", 55000),  # 207 locations
    "Romano's Macaroni Grill": (3.8, 500, "@macaronigrill*", 17000),  # ~9 locations
    "Frankie & Benny's": (4.0, 2000, "@frankienbennys*", 71000),  # ~36 locations (UK)
    "ASK Italian": (4.0, 2000, "@askitalian*", 60000),  # ~62 locations (UK)
    "Prezzo": (3.9, 2000, "@prezzoitalian*", 59000),  # ~95 locations (UK)
    "Spaghetti Warehouse": (3.7, 1000, "@spaghettiwarehouse*", 2652),  # ~5 locations (USA)
}
