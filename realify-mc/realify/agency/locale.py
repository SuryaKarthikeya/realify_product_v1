"""R9 Part A — per-country synthesis config. Country is a BRAND property (agencies are country-neutral;
we do NOT model agency country). Country drives currency + formatting, COGS/margin bands, product
names/categories, and the channel set. US = USD / Western grouping / Amazon·Walmart·Shopify;
India = INR / lakh grouping / Amazon.in·Flipkart·Shopzee.

Money grouping itself is handled by realify.agency.money.format_money (Western vs en-IN) — this module
supplies the inputs (currency, channels, word banks, COGS bands, price bands) that make a world
locale-correct and deterministic."""

LOCALES = {
    "US": {
        "country": "US",
        "currency": "USD",
        "symbol": "$",
        "fx_ppm": 1_000_000,                      # USD identity
        "channels": ["Amazon US", "Walmart", "Shopify"],
        "primary_channel": "amazon",
        "cogs_lo": 0.28, "cogs_hi": 0.50,         # COGS as a fraction of price (US bands)
        "prices": [11, 16, 22, 29, 38, 49, 64, 79],   # whole USD — realistic consumer-goods prices
        "categories": ["Home & Kitchen", "Pet Supplies", "Outdoor", "Electronics", "Beauty",
                       "Grocery", "Toys"],
        "brand_words": ["Northwind", "Alpine", "Suncrest", "Corva", "Brightwater", "Cedar Grove",
                        "Meridian", "Harbor", "Pinecrest", "Vantage"],
        "brand_suffix": ["Home", "Gear", "Outdoors", "Audio", "Kitchen", "Supply", "Goods"],
    },
    "IN": {
        "country": "IN",
        "currency": "INR",
        "symbol": "₹",
        "fx_ppm": 83_500_000,                     # ₹ per USD ×1e6
        "channels": ["Amazon.in", "Flipkart", "Shopzee"],
        "primary_channel": "amazon",
        "cogs_lo": 0.35, "cogs_hi": 0.60,         # India COGS bands run higher than US (golden-tested)
        "prices": [499, 899, 1299, 1999, 2499, 3299],
        "categories": ["Car cover", "Dashcam", "Phone mount", "Seat organizer", "Tyre inflator",
                       "LED kit", "Floor mats", "Charger"],
        "brand_words": ["Kavery", "Deccan", "Ganga", "Konark", "Nilgiri", "Sarovar", "Vindhya",
                        "Coromandel", "Malabar", "Aravalli"],
        "brand_suffix": ["Auto", "Living", "Wellness", "Retail", "Traders", "Mobility", "Home"],
        "festival_ramp": True,                    # Diwali demand ramp
    },
}

VALID_COUNTRIES = tuple(LOCALES.keys())

# Real product-line names per category (R9.1): the decision surface NAMES the product. ~12 each so a
# ~24-SKU / 3-category brand never runs out. Deterministic pick by index.
PRODUCTS = {
    # ---- US categories ----
    "Home & Kitchen": ["Stainless Steel Garlic Press", "Ceramic Non-Stick Fry Pan", "Bamboo Cutting Board",
                       "Silicone Baking Mat Set", "Cast Iron Skillet 12\"", "Glass Meal-Prep Containers",
                       "Electric Milk Frother", "Pour-Over Coffee Dripper", "Digital Kitchen Scale",
                       "Collapsible Colander", "Insulated Water Bottle 32oz", "Knife Sharpening Rod"],
    "Pet Supplies": ["Orthopedic Dog Bed (Large)", "Stainless Steel Slow-Feeder Bowl", "Retractable Dog Leash",
                     "Interactive Cat Laser Toy", "No-Pull Dog Harness", "Ceramic Cat Water Fountain",
                     "Grooming De-shedding Brush", "Odor-Control Litter Mat", "Chew-Resistant Rope Toy",
                     "Travel Pet Carrier", "LED Safety Collar", "Automatic Treat Dispenser"],
    "Outdoor": ["4-Person Dome Tent", "Insulated Camping Cooler 45qt", "Trekking Poles (Pair)",
                "Portable Camp Stove", "Inflatable Sleeping Pad", "Hydration Backpack 2L",
                "LED Camping Lantern", "Folding Camp Chair", "Waterproof Dry Bag 20L",
                "Titanium Cookware Set", "Paracord Survival Bracelet", "Solar Power Bank"],
    "Electronics": ["USB-C 100W Charger", "Bluetooth Noise-Cancelling Earbuds", "1080p Webcam",
                    "Mechanical Keyboard TKL", "Portable SSD 1TB", "Wireless Charging Pad",
                    "Smart LED Bulb 4-Pack", "HDMI 2.1 Cable 6ft", "Laptop Docking Station",
                    "Ergonomic Wireless Mouse", "Surge Protector 8-Outlet", "Dashboard Phone Mount"],
    "Beauty": ["Vitamin C Facial Serum", "Jade Facial Roller", "Argan Oil Hair Mask",
               "Matte Liquid Lipstick", "Detox Clay Face Mask", "Bamboo Makeup Brush Set",
               "Retinol Night Cream", "Aloe Soothing Gel", "Volumizing Mascara",
               "Exfoliating Body Scrub", "Cordless Hair Curler", "SPF 50 Mineral Sunscreen"],
    "Grocery": ["Organic Cold-Brew Coffee", "Manuka Honey 250g", "Himalayan Pink Salt Grinder",
                "Extra-Virgin Olive Oil 1L", "Dark Roast Coffee Beans", "Matcha Green Tea Powder",
                "Almond Butter (No Sugar)", "Sea Salt Dark Chocolate", "Sparkling Water Variety Pack",
                "Protein Granola Clusters", "Aged Balsamic Vinegar", "Herbal Sleep Tea"],
    "Toys": ["Wooden Building Blocks 100pc", "STEM Robotics Kit", "Plush Teddy Bear 18\"",
             "Remote Control Race Car", "Watercolor Paint Set", "Magnetic Tile Set 60pc",
             "Dinosaur Figure Pack", "Kids' Play Kitchen", "Jumbo Jigsaw Puzzle",
             "Foam Dart Blaster", "Sensory Fidget Cube", "Glow-in-the-Dark Star Kit"],
    # ---- India categories (auto accessories) ----
    "Car cover": ["Waterproof Car Body Cover (Sedan)", "UV-Proof SUV Cover", "Hatchback Dust Cover",
                  "All-Weather Premium Car Cover", "Nylon Bike Cover", "Reflective Car Cover",
                  "Custom-Fit Cover (i20)", "Heavy-Duty Truck Tarp", "Breathable Indoor Cover",
                  "Windshield Sun Shade", "Car Cover with Mirror Pockets", "Compact Car Cover"],
    "Dashcam": ["Full-HD Dash Camera", "Dual-Channel Dashcam", "4K Night-Vision Dashcam",
                "Wi-Fi GPS Dashcam", "Rear-View Backup Camera", "Mini Discreet Dashcam",
                "Parking-Mode Dashcam", "Touchscreen Dash Camera", "Mirror-Mount Dashcam",
                "Loop-Recording Dashcam", "ADAS Smart Dashcam", "Motorbike Action Cam"],
    "Phone mount": ["Magnetic Dashboard Mount", "Air-Vent Phone Holder", "Suction Windshield Mount",
                    "Adjustable CD-Slot Mount", "Wireless-Charging Car Mount", "Bike Handlebar Mount",
                    "Gravity Auto-Clamp Mount", "Cup-Holder Phone Mount", "Rear-Seat Tablet Mount",
                    "360° Rotating Mount", "MagSafe Vent Mount", "Universal Clip Mount"],
    "Seat organizer": ["Back-Seat Organizer", "Car Trunk Organizer", "Seat-Gap Filler Pocket",
                       "Kids' Travel Tray", "Leather Console Organizer", "Hanging Seat Storage",
                       "Foldable Boot Organizer", "Seat-Back Tablet Holder", "Door-Pocket Organizer",
                       "Multi-Pocket Visor Organizer", "Net Cargo Organizer", "Under-Seat Storage Box"],
    "Tyre inflator": ["Digital Tyre Inflator", "Cordless Air Pump", "Portable 12V Compressor",
                      "Heavy-Duty Tyre Inflator", "Rechargeable Air Inflator", "Preset Auto-Stop Inflator",
                      "Mini Bike Pump", "Dual-Cylinder Compressor", "LED Emergency Inflator",
                      "Analog Tyre Inflator", "Fast-Fill Air Pump", "Smart App Inflator"],
    "LED kit": ["Interior LED Ambient Kit", "Headlight LED Bulb Pair", "RGB Footwell Light Kit",
                "Fog Lamp LED Set", "DRL Strip Kit", "License-Plate LED", "Underglow LED Kit",
                "Dashboard LED Strip", "Reverse LED Bulbs", "Door-Courtesy LED", "Boot LED Light",
                "Steering LED Ring"],
    "Floor mats": ["7D Leather Floor Mats", "All-Weather Rubber Mats", "Custom-Fit Car Mats",
                   "Universal PVC Mats", "3D Bucket Floor Mats", "Anti-Skid Mat Set",
                   "Premium Diamond Mats", "Boot Cargo Mat", "Grass-Style Mats", "Coil Car Mats",
                   "Dual-Layer Mats", "Waterproof Mat Set"],
    "Charger": ["Dual-USB Car Charger", "65W PD Car Charger", "Fast-Charge QC3.0 Adapter",
                "3-Port Car Charger", "Wireless Car Charger", "Type-C Car Adapter",
                "Cigarette-Lighter Splitter", "Metal-Body Car Charger", "LED Voltage Charger",
                "Retractable Cable Charger", "Mini Bullet Charger", "Multiport USB Hub"],
}

# Per-category brand-name banks (R15 Part B): a brand's display name is drawn from a bank ALIGNED to its
# PRIMARY category, so a Beauty brand reads beauty-plausible and a Pet brand pet-plausible (replaces the
# old category-blind word×suffix cross-product). Deterministic pick by ordinal; world-wide uniqueness is
# guaranteed by the synth layer's (category, ordinal) slot assignment. Keys mirror LOCALES[*]["categories"].
BRAND_NAMES = {
    "US": {
        "Home & Kitchen": ["Hearthstone Home", "Coppervale Kitchen", "Willow Row Home", "Maple Lane Kitchen",
                           "Stonewell Home", "Emberline Kitchen", "Birchwood Home", "Copperpot Kitchen"],
        "Pet Supplies": ["Waggle Pet Co", "Pawthentic", "Barkwell Pets", "Whisker Haven", "Trusty Paws",
                         "Fetchwell", "Companion Pet Co", "Pawgrove"],
        "Outdoor": ["Summit Trail Co", "Basecamp Outfitters", "Ridgeline Gear", "Wildpine Outdoors",
                    "Trailhead Supply", "Alpenglow Gear", "Backcountry Co", "Northridge Outdoors"],
        "Electronics": ["Voltcore", "Pulsewave Tech", "Circuitry Labs", "Nimbus Electronics",
                        "Kinetic Devices", "Boltgear Tech", "Voltbridge Tech", "Electra Devices"],
        "Beauty": ["Luminous Skin Co", "Velvet Bloom", "Rosewater Beauty", "Glowpetal Beauty", "Petal Grove",
                   "Aurelia Beauty", "Sable Silk", "Dewdrop Cosmetics"],
        "Grocery": ["Harvest Pantry", "Golden Fields Foods", "Wholesome Roots", "Orchard Vine Foods",
                    "Pure Harvest Co", "Meadowgrain Foods", "Nourish Provisions", "Sunhaven Pantry"],
        "Toys": ["Playful Minds", "Bright Sprout Toys", "Tinker & Co", "Wonderbox Toys", "Little Explorers",
                 "Giggle Works", "Jumble Toy Co", "Rainbow Sprocket"],
    },
    "IN": {
        "Car cover": ["ShieldFit Auto", "CoverKart", "ArmorWrap", "AutoShield India", "GuardSkin Auto",
                      "CarCocoon", "ProtectPro Auto", "DustGuard Covers"],
        "Dashcam": ["RoadEye", "DashPro India", "ClearView Cams", "SafeDrive Optics", "LensRoad",
                    "VisionDash", "GuardCam Auto", "TrailView Cams"],
        "Phone mount": ["GripDrive", "MountMate", "HoldFast Auto", "DashGrip", "SecureMount India",
                        "FlexHold", "ClampPro Auto", "SteadyMount"],
        "Seat organizer": ["TidyRide", "SeatStash", "CabinNeat", "OrganizeAuto", "StowMate",
                           "NeatSeat India", "CargoTidy", "PocketRide"],
        "Tyre inflator": ["AirFlex", "InflatePro", "PumpMate Auto", "TyreBoost", "RapidAir India",
                          "PressurePro", "AirVault", "FlexPump"],
        "LED kit": ["GlowLine Auto", "LumenKart", "BrightBeam India", "NeonRide", "AuraLED",
                    "VividGlow Auto", "RadiantKit", "SpectraLED"],
        "Floor mats": ["MatCraft Auto", "GripMat India", "TreadWell Mats", "FloorFit", "DuraMat Auto",
                       "ComfortTread", "PaveGuard Mats", "SnugMat"],
        "Charger": ["VoltRush", "ChargeKart", "PowerDrive Auto", "AmpMate", "RapidVolt India",
                    "FuseCharge", "EnerGrip", "BoltCharge Auto"],
    },
}

# Reverse map (display name -> category), built once, for coherence checks + name→category tagging.
_NAME_CATEGORY = {n: cat for banks in BRAND_NAMES.values() for cat, names in banks.items() for n in names}


def brand_name_for(country, category, ordinal):
    """Deterministic category-aligned brand name for the `ordinal`-th brand in `category`. Overflow past
    the bank gets a deterministic numeric suffix so names stay unique within a category."""
    bank = BRAND_NAMES.get(country, BRAND_NAMES["US"]).get(category)
    if not bank:
        return f"{category} {ordinal + 1}"
    base, wrap = bank[ordinal % len(bank)], ordinal // len(bank)
    return base if wrap == 0 else f"{base} {wrap + 1}"


def name_category(name):
    """The category a display name belongs to (reverse bank lookup; strips an overflow ' N' suffix).
    Returns None for names not drawn from a bank (e.g. a user-supplied override)."""
    if name in _NAME_CATEGORY:
        return _NAME_CATEGORY[name]
    head, _, tail = name.rpartition(" ")
    return _NAME_CATEGORY.get(head) if tail.isdigit() else None


# Real person names for agency members / brand owners (deterministic pick by index).
PEOPLE = {
    "US": ["Sarah Mitchell", "Jake Thompson", "Emily Carter", "Dan Foley", "Olivia Bennett",
           "Marcus Reed", "Hannah Brooks", "Ethan Parker", "Grace Sullivan", "Noah Fletcher"],
    "IN": ["Priya Sharma", "Arjun Rao", "Neha Gupta", "Vikram Nair", "Ananya Iyer",
           "Rohan Mehta", "Kavya Reddy", "Aditya Verma", "Sneha Kulkarni", "Karan Malhotra"],
}

AGENCIES = {
    "US": ["BrightPeak Commerce", "Cedarline Partners", "Northgate Growth", "Vantage Retail Group",
           "Harborview Commerce", "Summit Channel Co"],
    "IN": ["Kavery Commerce", "Deccan Growth Partners", "Coromandel Retail", "Nilgiri Channel Co",
           "Sarovar Commerce", "Malabar Retail Group"],
}


def product_name(country, category, idx):
    """Deterministic real product name for a category slot (falls back to the category if unlisted)."""
    names = PRODUCTS.get(category)
    return names[idx % len(names)] if names else f"{category} item {idx + 1}"


def person_name(country, idx):
    bank = PEOPLE.get(country, PEOPLE["US"])
    return bank[idx % len(bank)]


def agency_name(country, seed):
    bank = AGENCIES.get(country, AGENCIES["US"])
    return bank[sum(ord(c) for c in (seed or "x")) % len(bank)]


def get(country):
    """Locale config for a country code ('US'|'IN'); raises KeyError on an unknown country."""
    return LOCALES[country]


def channels_for(country):
    return list(LOCALES[country]["channels"])


def is_valid(country):
    return country in LOCALES
