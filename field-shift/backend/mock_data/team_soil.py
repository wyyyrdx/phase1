TEAM_SOILS = {
    "sandy": {
        "name": "Sandy soil",
        "cec_meq_per_100g": "3-5",
        "crops": set(),
        "irrigation": "Drip irrigation in small, frequent amounts holds water better than infrequent heavy irrigation.",
        "improvement": "Add organic matter, compost, and peat moss so the soil keeps water and nutrients.",
    },
    "clay": {
        "name": "Clay soil",
        "cec_meq_per_100g": "up to 40",
        "crops": {"wheat", "barley"},
        "irrigation": "Clay holds water for a long time, so it needs fewer irrigations.",
        "improvement": "Add gypsum and organic matter, and avoid working the soil when it is sticky.",
    },
}
