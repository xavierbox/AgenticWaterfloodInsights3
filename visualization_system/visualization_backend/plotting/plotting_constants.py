class ChartColors:
    """Centralized color management for all charts"""

    # Well types
    PRODUCER = "red"
    INJECTOR = "cyan"

    # Borders for well markers
    PRODUCER_BORDER = "darkred"
    INJECTOR_BORDER = "darkcyan"
    BORDER_WIDTH = 1

    # Production types
    OIL = "grey"
    WATER = "blue"
    GAS = "brown"
    LIQUID = "green"

    # Volume overlays
    WATER_DOMINATED = "blue"
    OIL_DOMINATED = "grey"

    # Utility
    SMALL_MARKER = "black"
    INACTIVE = "lightgrey"

    # Injection
    WATER_INJECTION = "cyan"

    @classmethod
    def get_injector_color(cls):
        return cls.INJECTOR

    @classmethod
    def get_producer_color(cls):
        return cls.PRODUCER

    @classmethod
    def get_border_config(cls, well_type="injector"):
        """Get border configuration for well markers"""
        if well_type == "injector":
            return {"color": cls.INJECTOR_BORDER, "width": cls.BORDER_WIDTH}
        elif well_type == "producer":
            return {"color": cls.PRODUCER_BORDER, "width": cls.BORDER_WIDTH}
        else:
            return {"color": "white", "width": 2}


# Default color palette for fallback use (e.g., sectors, unclassified traces)
default_colors = [
    "green",
    "cyan",
    "lightgrey",
    "firebrick",
    "blue",
    "red",
    "purple",
    "magenta",
    "brown",
    "pink",
    "goldenrod",
    "midnightblue",
    "darkred",
    "darkgreen",
    "darkslategray",
    "saddlebrown",
    "indigo",
    "darkmagenta",
    "navy",
    "teal",
    "darkslateblue",
    "crimson",
]

# Specific color mapping for known rate types - now references ChartColors
RATE_COLORS = {
    "gas_production": ChartColors.GAS,
    "liquid_production": ChartColors.LIQUID,
    "oil_production": ChartColors.OIL,
    "water_injection": ChartColors.WATER_INJECTION,
    "water_production": ChartColors.WATER,
}


def get_color(index):
    return default_colors[index % len(default_colors)]

