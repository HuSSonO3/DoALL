"""Unit conversion data and logic — standard units (factor-to-base) and temperature."""

UNIT_CATEGORIES = {
    "Length": {
        "Meter": 1.0,
        "Kilometer": 1000.0,
        "Centimeter": 0.01,
        "Millimeter": 0.001,
        "Mile": 1609.344,
        "Yard": 0.9144,
        "Foot": 0.3048,
        "Inch": 0.0254,
    },
    "Weight": {
        "Kilogram": 1.0,
        "Gram": 0.001,
        "Milligram": 0.000001,
        "Pound": 0.453592,
        "Ounce": 0.0283495,
        "Ton (metric)": 1000.0,
        "Ton (US)": 907.18474,
    },
    "Volume": {
        "Liter": 1.0,
        "Milliliter": 0.001,
        "Gallon (US)": 3.78541,
        "Quart": 0.946353,
        "Pint": 0.473176,
        "Cup": 0.236588,
        "Fluid Ounce": 0.0295735,
    },
    "Area": {
        "Square Meter": 1.0,
        "Square Kilometer": 1_000_000.0,
        "Square Mile": 2_589_988.11,
        "Hectare": 10_000.0,
        "Acre": 4046.856,
        "Square Foot": 0.092903,
    },
    "Speed": {
        "m/s": 1.0,
        "km/h": 0.277778,
        "mph": 0.44704,
        "Knot": 0.514444,
    },
}


def convert_standard(category, amount, from_unit, to_unit):
    """Convert between standard units using factor-to-base method."""
    units = UNIT_CATEGORIES[category]
    base = amount * units[from_unit]
    return base / units[to_unit]


def convert_temperature(amount, from_unit, to_unit):
    """Temperature uses formulas, not factors."""
    if from_unit == "Fahrenheit":
        c = (amount - 32) * 5 / 9
    elif from_unit == "Kelvin":
        c = amount - 273.15
    else:
        c = amount
    if to_unit == "Fahrenheit":
        return (c * 9 / 5) + 32
    elif to_unit == "Kelvin":
        return c + 273.15
    return c
