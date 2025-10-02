# services/season-compatibility/src/season_palettes.py
"""Static 16-season palette configuration"""

SEASON_PALETTES = {
    "Light Spring": {
        "temperature": "warm",
        "value": "light",
        "chroma": "medium-clear",
        "temperature_score": 0.7,
        "value_score": 0.8,
        "chroma_score": 0.6,
        "reference_colors": [
            [255, 229, 180],  # Light peach
            [152, 255, 152],  # Mint green
            [255, 218, 185],  # Peachy pink
            [176, 224, 230],  # Powder blue
            [255, 239, 213],  # Papaya whip
        ],
    },
    "True Spring": {
        "temperature": "warm",
        "value": "medium",
        "chroma": "clear",
        "temperature_score": 0.8,
        "value_score": 0.5,
        "chroma_score": 0.7,
        "reference_colors": [
            [255, 127, 80],  # Coral
            [64, 224, 208],  # Turquoise
            [255, 215, 0],  # Gold
            [255, 99, 71],  # Tomato
            [127, 255, 0],  # Chartreuse
        ],
    },
    "Bright Spring": {
        "temperature": "warm",
        "value": "medium-light",
        "chroma": "bright",
        "temperature_score": 0.75,
        "value_score": 0.6,
        "chroma_score": 0.9,
        "reference_colors": [
            [255, 20, 147],  # Deep pink
            [0, 255, 127],  # Spring green
            [255, 140, 0],  # Dark orange
            [0, 191, 255],  # Deep sky blue
            [255, 255, 0],  # Yellow
        ],
    },
    "Warm Spring": {
        "temperature": "warm",
        "value": "medium",
        "chroma": "medium",
        "temperature_score": 0.85,
        "value_score": 0.5,
        "chroma_score": 0.5,
        "reference_colors": [
            [255, 160, 122],  # Light salmon
            [154, 205, 50],  # Yellow green
            [255, 165, 0],  # Orange
            [240, 128, 128],  # Light coral
            [189, 183, 107],  # Dark khaki
        ],
    },
    "Light Summer": {
        "temperature": "cool",
        "value": "light",
        "chroma": "soft",
        "temperature_score": 0.3,
        "value_score": 0.8,
        "chroma_score": 0.3,
        "reference_colors": [
            [230, 230, 250],  # Lavender
            [176, 196, 222],  # Light steel blue
            [255, 182, 193],  # Light pink
            [211, 211, 211],  # Light gray
            [216, 191, 216],  # Thistle
        ],
    },
    "True Summer": {
        "temperature": "cool",
        "value": "medium",
        "chroma": "soft",
        "temperature_score": 0.25,
        "value_score": 0.5,
        "chroma_score": 0.35,
        "reference_colors": [
            [147, 112, 219],  # Medium purple
            [100, 149, 237],  # Cornflower blue
            [188, 143, 143],  # Rosy brown
            [119, 136, 153],  # Light slate gray
            [176, 224, 230],  # Powder blue
        ],
    },
    "Soft Summer": {
        "temperature": "cool-neutral",
        "value": "medium",
        "chroma": "soft",
        "temperature_score": 0.35,
        "value_score": 0.5,
        "chroma_score": 0.2,
        "reference_colors": [
            [128, 128, 128],  # Gray
            [143, 188, 143],  # Dark sea green
            [188, 143, 143],  # Rosy brown
            [169, 169, 169],  # Dark gray
            [136, 136, 136],  # Medium gray
        ],
    },
    "Cool Summer": {
        "temperature": "cool",
        "value": "medium-light",
        "chroma": "medium-soft",
        "temperature_score": 0.2,
        "value_score": 0.6,
        "chroma_score": 0.4,
        "reference_colors": [
            [70, 130, 180],  # Steel blue
            [123, 104, 238],  # Medium slate blue
            [186, 85, 211],  # Medium orchid
            [95, 158, 160],  # Cadet blue
            [138, 43, 226],  # Blue violet
        ],
    },
    "Soft Autumn": {
        "temperature": "warm-neutral",
        "value": "medium",
        "chroma": "soft",
        "temperature_score": 0.65,
        "value_score": 0.5,
        "chroma_score": 0.2,
        "reference_colors": [
            [188, 143, 143],  # Rosy brown
            [143, 188, 143],  # Dark sea green
            [210, 180, 140],  # Tan
            [160, 160, 160],  # Gray
            [189, 183, 107],  # Dark khaki
        ],
    },
    "True Autumn": {
        "temperature": "warm",
        "value": "medium",
        "chroma": "medium",
        "temperature_score": 0.75,
        "value_score": 0.4,
        "chroma_score": 0.5,
        "reference_colors": [
            [255, 140, 0],  # Dark orange
            [128, 128, 0],  # Olive
            [165, 42, 42],  # Brown
            [218, 165, 32],  # Goldenrod
            [184, 134, 11],  # Dark goldenrod
        ],
    },
    "Warm Autumn": {
        "temperature": "warm",
        "value": "medium",
        "chroma": "medium-rich",
        "temperature_score": 0.8,
        "value_score": 0.45,
        "chroma_score": 0.6,
        "reference_colors": [
            [255, 99, 71],  # Tomato
            [255, 127, 80],  # Coral
            [205, 92, 92],  # Indian red
            [244, 164, 96],  # Sandy brown
            [210, 105, 30],  # Chocolate
        ],
    },
    "Deep Autumn": {
        "temperature": "warm",
        "value": "deep",
        "chroma": "rich",
        "temperature_score": 0.7,
        "value_score": 0.2,
        "chroma_score": 0.65,
        "reference_colors": [
            [139, 69, 19],  # Saddle brown
            [128, 0, 0],  # Maroon
            [85, 107, 47],  # Dark olive green
            [139, 0, 0],  # Dark red
            [101, 67, 33],  # Dark brown
        ],
    },
    "Bright Winter": {
        "temperature": "cool",
        "value": "medium",
        "chroma": "bright",
        "temperature_score": 0.25,
        "value_score": 0.5,
        "chroma_score": 0.9,
        "reference_colors": [
            [255, 0, 255],  # Magenta
            [0, 255, 255],  # Cyan
            [255, 20, 147],  # Deep pink
            [0, 0, 255],  # Blue
            [255, 255, 0],  # Yellow
        ],
    },
    "True Winter": {
        "temperature": "cool",
        "value": "medium",
        "chroma": "clear",
        "temperature_score": 0.2,
        "value_score": 0.4,
        "chroma_score": 0.75,
        "reference_colors": [
            [0, 0, 139],  # Dark blue
            [128, 0, 128],  # Purple
            [220, 20, 60],  # Crimson
            [0, 128, 0],  # Green
            [255, 255, 255],  # White
        ],
    },
    "Cool Winter": {
        "temperature": "cool",
        "value": "medium-deep",
        "chroma": "medium-clear",
        "temperature_score": 0.15,
        "value_score": 0.3,
        "chroma_score": 0.7,
        "reference_colors": [
            [72, 61, 139],  # Dark slate blue
            [106, 90, 205],  # Slate blue
            [138, 43, 226],  # Blue violet
            [75, 0, 130],  # Indigo
            [128, 0, 128],  # Purple
        ],
    },
    "Deep Winter": {
        "temperature": "cool",
        "value": "deep",
        "chroma": "clear",
        "temperature_score": 0.2,
        "value_score": 0.1,
        "chroma_score": 0.8,
        "reference_colors": [
            [0, 0, 0],  # Black
            [25, 25, 112],  # Midnight blue
            [139, 0, 139],  # Dark magenta
            [0, 100, 0],  # Dark green
            [128, 0, 0],  # Maroon
        ],
    },
}

# Axis weights for scoring
SCORING_WEIGHTS = {"temperature": 0.4, "value": 0.3, "chroma": 0.3}
