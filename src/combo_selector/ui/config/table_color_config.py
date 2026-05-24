# Each table passes its own column color rules as a dict:
# { column_index: { value: hex_color, ... } }

COLOR_CONFIG_TABLE_FEASIBILITY = {
    4: {
        "High": "#1a7a2e", "Moderate": "#f5a623", "Low": "#d94f3d"
    },
    3: {
        "Low": "#1a7a2e", "Moderate": "#f5a623", "High": "#d94f3d", "NC": "#888888"
    },
    6: {
        "Insufficient ": "#d94f3d", "Cautionary": "#f5a623",
        "Acceptable": "#1a7a2e", "Suitable": "#6abf4b"
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
        "Not recommended": "#d94f3d", "Use with caution": "#f5a623",
        "Recommended": "#6abf4b", "Highly recommended": "#1a7a2e"
    },
}

COLOR_CONFIG_FINAL_EVALUATION = {
    8: {
        "Highly recommended": "#1a7a2e", "Recommended": "#6abf4b", "Use with caution": "#f5a623", "Not recommended": "#d94f3d"
    },
}
