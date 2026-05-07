# Each table passes its own column color rules as a dict:
# { column_index: { value: hex_color, ... } }

COLOR_CONFIG_TABLE_FEASIBILITY = {
    4: {
        "High": "#1a7a4a", "Moderate": "#b36a00", "Low": "#c0392b"
    },
    3: {
        "Low": "#1a7a4a", "Moderate": "#b36a00", "High": "#c0392b", "NC": "#888888"
    },
    6: {
        "Below Threshold": "#c0392b", "Caution": "#b36a00",
        "Acceptable": "#b8a800", "High": "#1a7a4a"
    },
}

COLOR_CONFIG_TABLE_RECOMMENDATION = {
    6: {
        "Good": "#1a7a4a", "Moderate": "#b36a00", "Low": "#c0392b"
    },
    7: {
        "Low": "#1a7a4a", "Moderate": "#b36a00", "High": "#c0392b", "NC": "#888888"
    },
    8: {
        "Not recommended": "#c0392b", "Use with caution": "#b36a00",
        "Recommended": "#b8a800", "Highly recommended": "#1a7a4a"
    },
}
