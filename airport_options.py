from __future__ import annotations

AIRPORT_CHOICES = [
    {"label": "Montreal, Canada (YUL)", "code": "YUL"},
    {"label": "Ottawa, Canada (YOW)", "code": "YOW"},
    {"label": "Toronto Pearson, Canada (YYZ)", "code": "YYZ"},
    {"label": "Toronto City, Canada (YTZ)", "code": "YTZ"},
    {"label": "Vancouver, Canada (YVR)", "code": "YVR"},
    {"label": "New York JFK, United States (JFK)", "code": "JFK"},
    {"label": "Newark, United States (EWR)", "code": "EWR"},
    {"label": "Chicago O'Hare, United States (ORD)", "code": "ORD"},
    {"label": "Los Angeles, United States (LAX)", "code": "LAX"},
    {"label": "Miami, United States (MIA)", "code": "MIA"},
    {"label": "Mexico City, Mexico (MEX)", "code": "MEX"},
    {"label": "Bogota, Colombia (BOG)", "code": "BOG"},
    {"label": "Medellin, Colombia (MDE)", "code": "MDE"},
    {"label": "Cartagena, Colombia (CTG)", "code": "CTG"},
    {"label": "Lima, Peru (LIM)", "code": "LIM"},
    {"label": "Cusco, Peru (CUZ)", "code": "CUZ"},
    {"label": "Quito, Ecuador (UIO)", "code": "UIO"},
    {"label": "Guayaquil, Ecuador (GYE)", "code": "GYE"},
    {"label": "Santiago, Chile (SCL)", "code": "SCL"},
    {"label": "Buenos Aires Ezeiza, Argentina (EZE)", "code": "EZE"},
    {"label": "Buenos Aires Aeroparque, Argentina (AEP)", "code": "AEP"},
    {"label": "Sao Paulo Guarulhos, Brazil (GRU)", "code": "GRU"},
    {"label": "Rio de Janeiro Galeao, Brazil (GIG)", "code": "GIG"},
    {"label": "Panama City, Panama (PTY)", "code": "PTY"},
    {"label": "Madrid, Spain (MAD)", "code": "MAD"},
    {"label": "Barcelona, Spain (BCN)", "code": "BCN"},
    {"label": "Paris Charles de Gaulle, France (CDG)", "code": "CDG"},
    {"label": "London Heathrow, United Kingdom (LHR)", "code": "LHR"},
    {"label": "Amsterdam, Netherlands (AMS)", "code": "AMS"},
    {"label": "Tokyo Haneda, Japan (HND)", "code": "HND"},
    {"label": "Bangkok Suvarnabhumi, Thailand (BKK)", "code": "BKK"},
    {"label": "Sydney, Australia (SYD)", "code": "SYD"},
]

AIRPORT_LABELS = [item["label"] for item in AIRPORT_CHOICES]
AIRPORT_CODE_BY_LABEL = {item["label"]: item["code"] for item in AIRPORT_CHOICES}


SOUTH_AMERICA_PRESET = {
    "trip_name": "Coffee, mountains, and a little airport chaos",
    "currency": "CAD",
    "passengers": 1,
    "one_way_origin": "Montreal, Canada (YUL)",
    "one_way_destination": "Bogota, Colombia (BOG)",
    "one_way_date": "2026-11-08",
    "legs": [
        {
            "origin_label": "Montreal, Canada (YUL)",
            "destination_label": "Bogota, Colombia (BOG)",
            "date": "2026-11-08",
        },
        {
            "origin_label": "Bogota, Colombia (BOG)",
            "destination_label": "Quito, Ecuador (UIO)",
            "date": "2026-11-11",
        },
        {
            "origin_label": "Quito, Ecuador (UIO)",
            "destination_label": "Cusco, Peru (CUZ)",
            "date": "2026-11-14",
        },
        {
            "origin_label": "Cusco, Peru (CUZ)",
            "destination_label": "Montreal, Canada (YUL)",
            "date": "2026-11-19",
        },
    ],
}
