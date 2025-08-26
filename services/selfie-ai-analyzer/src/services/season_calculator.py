# services/selfie-ai-analyzer/src/services/season_calculator.py
import numpy as np
from typing import Dict, Tuple
from ..schemas.analysis import ColorAttributes, SeasonScores
from shared.utils.logger import ServiceLogger

class SeasonCalculator:
    """Calculate season scores based on 16-season color analysis model"""
    
    def __init__(self, logger: ServiceLogger):
        self.logger = logger
        self.season_palettes = self._initialize_season_palettes()
    
    def _initialize_season_palettes(self) -> Dict:
        """Initialize color palettes for each season based on the 16-season model"""
        return {
            # SPRING - Warm, lively
            "light_spring": {
                "temperature": "warm_neutral",  # Warm to neutral
                "value": "light",
                "chroma": "medium_clear",
                "key_colors": [
                    [255, 229, 180],  # Light peach
                    [152, 251, 152],  # Mint green
                    [255, 250, 205],  # Lemon chiffon
                ],
                "eye_colors": [[173, 216, 230], [144, 238, 144]],  # Light blue, light green
                "hair_colors": [[255, 248, 220], [238, 232, 170]],  # Light blonde, golden blonde
                "skin_tones": [[255, 228, 196], [255, 235, 205]]   # Fair warm/neutral
            },
            "true_spring": {
                "temperature": "warm",
                "value": "medium",
                "chroma": "clear",
                "key_colors": [
                    [255, 127, 80],   # Coral
                    [64, 224, 208],   # Turquoise
                    [255, 215, 0],    # Gold
                ],
                "eye_colors": [[34, 139, 34], [64, 224, 208]],     # Warm green, turquoise
                "hair_colors": [[255, 215, 0], [255, 160, 122]],   # Golden/strawberry blonde
                "skin_tones": [[255, 239, 213], [255, 218, 185]]   # Warm ivory/peach
            },
            "bright_spring": {
                "temperature": "warm",
                "value": "medium",
                "chroma": "bright",
                "key_colors": [
                    [255, 99, 71],    # Hot coral
                    [0, 255, 127],    # Clear jade
                    [255, 69, 0],     # Red-orange
                ],
                "eye_colors": [[0, 191, 255], [50, 205, 50]],      # Clear blue, green
                "hair_colors": [[218, 165, 32], [184, 134, 11]],   # Medium blonde to copper
                "skin_tones": [[255, 228, 181], [255, 222, 173]]   # Clear warm undertone
            },
            "warm_spring": {
                "temperature": "very_warm",
                "value": "medium",
                "chroma": "medium",
                "key_colors": [
                    [255, 99, 71],    # Tomato red
                    [255, 193, 37],   # Marigold
                    [160, 82, 45],    # Sienna
                ],
                "eye_colors": [[154, 205, 50], [139, 69, 19]],     # Hazel, light brown
                "hair_colors": [[139, 90, 43], [139, 69, 19]],     # Golden brown, auburn
                "skin_tones": [[255, 228, 181], [255, 218, 185]]   # Golden beige/peach
            },
            
            # SUMMER - Cool, gentle
            "light_summer": {
                "temperature": "cool_neutral",
                "value": "light",
                "chroma": "soft",
                "key_colors": [
                    [176, 224, 230],  # Powder blue
                    [230, 230, 250],  # Lavender
                    [255, 182, 193],  # Light pink
                ],
                "eye_colors": [[135, 206, 235], [192, 192, 192]],  # Soft blue, gray-green
                "hair_colors": [[211, 211, 211], [205, 192, 176]], # Ash blonde, light brown
                "skin_tones": [[255, 228, 225], [255, 235, 238]]   # Fair cool/neutral
            },
            "true_summer": {
                "temperature": "cool",
                "value": "medium",
                "chroma": "soft",
                "key_colors": [
                    [188, 143, 143],  # Rosy brown
                    [100, 149, 237],  # Cornflower blue
                    [216, 191, 216],  # Thistle
                ],
                "eye_colors": [[128, 128, 128], [135, 206, 250]],  # Cool gray, soft blue
                "hair_colors": [[139, 125, 107], [128, 128, 128]], # Ash brown, cool blonde
                "skin_tones": [[255, 228, 225], [255, 218, 185]]   # Rosy beige/porcelain
            },
            "soft_summer": {
                "temperature": "cool_neutral",
                "value": "medium",
                "chroma": "muted",
                "key_colors": [
                    [188, 143, 143],  # Dusty rose
                    [143, 188, 143],  # Sage green
                    [176, 196, 222],  # Light steel blue
                ],
                "eye_colors": [[119, 136, 153], [128, 128, 128]],  # Gray-blue, gray-green
                "hair_colors": [[139, 125, 107], [160, 160, 160]], # Ash brown, dark blonde
                "skin_tones": [[245, 245, 220], [255, 228, 225]]   # Neutral beige
            },
            "cool_summer": {
                "temperature": "very_cool",
                "value": "medium",
                "chroma": "medium",
                "key_colors": [
                    [199, 21, 133],   # Cool raspberry
                    [112, 128, 144],  # Slate gray
                    [72, 61, 139],    # Dark slate blue
                ],
                "eye_colors": [[119, 136, 153], [154, 205, 50]],   # Blue-gray, cool hazel
                "hair_colors": [[160, 160, 160], [139, 125, 107]], # Ashy brown
                "skin_tones": [[255, 239, 213], [255, 235, 238]]   # Porcelain/cool ivory
            },
            
            # AUTUMN - Warm, subdued to rich
            "soft_autumn": {
                "temperature": "warm_neutral",
                "value": "medium",
                "chroma": "muted",
                "key_colors": [
                    [188, 143, 143],  # Mushroom
                    [128, 128, 0],    # Olive
                    [210, 180, 140],  # Tan
                ],
                "eye_colors": [[128, 128, 0], [154, 205, 50]],     # Olive green, soft hazel
                "hair_colors": [[139, 90, 43], [160, 160, 160]],   # Soft brown, dark blonde
                "skin_tones": [[245, 245, 220], [128, 128, 0]]     # Neutral beige/olive
            },
            "true_autumn": {
                "temperature": "warm",
                "value": "medium",
                "chroma": "rich",
                "key_colors": [
                    [255, 140, 0],    # Dark orange
                    [184, 134, 11],   # Dark goldenrod
                    [178, 34, 34],    # Firebrick
                ],
                "eye_colors": [[139, 90, 43], [50, 205, 50]],      # Warm brown, green
                "hair_colors": [[178, 34, 34], [139, 69, 19]],     # Red, auburn
                "skin_tones": [[255, 228, 181], [128, 128, 0]]     # Golden beige/olive
            },
            "warm_autumn": {
                "temperature": "very_warm",
                "value": "medium_deep",
                "chroma": "rich",
                "key_colors": [
                    [210, 105, 30],   # Chocolate
                    [184, 134, 11],   # Dark goldenrod
                    [205, 133, 63],   # Peru
                ],
                "eye_colors": [[184, 134, 11], [218, 165, 32]],    # Golden brown, amber
                "hair_colors": [[139, 69, 19], [160, 82, 45]],     # Deep golden brown
                "skin_tones": [[255, 228, 181], [205, 133, 63]]    # Golden/bronze
            },
            "deep_autumn": {
                "temperature": "warm",
                "value": "deep",
                "chroma": "rich",
                "key_colors": [
                    [0, 100, 0],      # Dark green
                    [139, 69, 19],    # Saddle brown
                    [128, 0, 0],      # Maroon
                ],
                "eye_colors": [[139, 69, 19], [128, 128, 0]],      # Dark brown, olive
                "hair_colors": [[0, 0, 0], [139, 69, 19]],         # Black-brown, deep auburn
                "skin_tones": [[160, 82, 45], [128, 128, 0]]       # Bronze, rich olive
            },
            
            # WINTER - Cool, high-contrast
            "bright_winter": {
                "temperature": "cool",
                "value": "medium",
                "chroma": "very_bright",
                "key_colors": [
                    [255, 0, 255],    # Fuchsia
                    [255, 255, 255],  # Pure white
                    [0, 0, 139],      # Dark blue
                ],
                "eye_colors": [[0, 191, 255], [0, 128, 0]],        # Icy blue, emerald
                "hair_colors": [[0, 0, 0], [139, 69, 19]],         # Black, dark brown
                "skin_tones": [[255, 239, 213], [245, 245, 220]]   # Porcelain
            },
            "true_winter": {
                "temperature": "very_cool",
                "value": "medium",
                "chroma": "clear",
                "key_colors": [
                    [220, 20, 60],    # Crimson
                    [0, 0, 205],      # Medium blue
                    [128, 128, 128],  # Gray
                ],
                "eye_colors": [[0, 0, 255], [128, 128, 128]],      # Cool blue, icy gray
                "hair_colors": [[0, 0, 0], [47, 79, 79]],          # Jet black, cool dark brown
                "skin_tones": [[255, 228, 225], [139, 69, 19]]     # Fair-deep cool
            },
            "cool_winter": {
                "temperature": "very_cool",
                "value": "medium",
                "chroma": "medium",
                "key_colors": [
                    [128, 0, 32],     # Burgundy
                    [0, 128, 128],    # Teal
                    [72, 61, 139],    # Dark slate blue
                ],
                "eye_colors": [[154, 205, 50], [119, 136, 153]],   # Cool hazel, gray-blue
                "hair_colors": [[128, 128, 128], [0, 0, 0]],       # Cool brown, black
                "skin_tones": [[255, 228, 225], [255, 239, 213]]   # Cool rose/porcelain
            },
            "deep_winter": {
                "temperature": "cool_neutral",
                "value": "deep",
                "chroma": "high",
                "key_colors": [
                    [0, 0, 0],        # Black
                    [25, 25, 112],    # Midnight blue
                    [139, 0, 139],    # Dark magenta
                ],
                "eye_colors": [[139, 69, 19], [0, 0, 0]],          # Dark brown, black
                "hair_colors": [[0, 0, 0], [47, 79, 79]],          # Black, black-brown
                "skin_tones": [[255, 228, 225], [139, 69, 19]]     # Fair-dark cool/neutral
            }
        }
    
    async def compute_season_scores(self, color_attributes: ColorAttributes) -> SeasonScores:
        """Compute scores for all 16 seasons based on extracted colors"""
        
        scores = {}
        
        for season_name, palette in self.season_palettes.items():
            score = self._calculate_season_score(color_attributes, palette)
            scores[season_name] = score
        
        # Normalize scores to 0-1 range
        max_score = max(scores.values()) if scores else 1
        if max_score > 0:
            scores = {k: v/max_score for k, v in scores.items()}
        
        return SeasonScores(**scores)
    
    def _calculate_season_score(
        self, 
        attributes: ColorAttributes, 
        palette: Dict
    ) -> float:
        """Calculate how well colors match a specific season palette"""
        
        score = 0.0
        weights = {
            "eye": 0.25,
            "hair": 0.25,
            "skin": 0.30,
            "overall": 0.20
        }
        
        # Compare eye colors
        if attributes.left_iris or attributes.right_iris:
            eye_color = attributes.left_iris.dominant_rgb if attributes.left_iris else attributes.right_iris.dominant_rgb
            eye_score = self._color_similarity(eye_color, palette["eye_colors"])
            score += eye_score * weights["eye"]
        
        # Compare hair colors
        if attributes.hair:
            hair_score = self._color_similarity(
                attributes.hair.dominant_rgb, 
                palette["hair_colors"]
            )
            score += hair_score * weights["hair"]
        
        # Compare skin tones
        if attributes.face_skin:
            skin_score = self._color_similarity(
                attributes.face_skin.dominant_rgb,
                palette["skin_tones"]
            )
            score += skin_score * weights["skin"]
        
        # Overall harmony with key colors
        if attributes.face_skin:
            harmony_score = self._evaluate_harmony(
                attributes.face_skin.dominant_rgb,
                palette["key_colors"]
            )
            score += harmony_score * weights["overall"]
        
        # Apply temperature, value, and chroma modifiers
        score *= self._get_characteristic_multiplier(attributes, palette)
        
        return score
    
    def _color_similarity(self, color1: list, color2_list: list) -> float:
        """Calculate similarity between a color and a list of reference colors"""
        
        if not color2_list:
            return 0.0
        
        # Convert to LAB color space for better perceptual distance
        similarities = []
        for ref_color in color2_list:
            # Simple Euclidean distance in RGB (could be improved with LAB)
            distance = np.sqrt(sum([(c1-c2)**2 for c1, c2 in zip(color1, ref_color)]))
            # Convert distance to similarity (0-1)
            similarity = max(0, 1 - distance / 441.67)  # max RGB distance is ~441.67
            similarities.append(similarity)
        
        return max(similarities)
    
    def _evaluate_harmony(self, skin_color: list, key_colors: list) -> float:
        """Evaluate how harmonious key colors would look with skin tone"""
        
        harmonies = []
        for key_color in key_colors:
            # Calculate color harmony based on color theory
            harmony = self._calculate_color_harmony(skin_color, key_color)
            harmonies.append(harmony)
        
        return np.mean(harmonies) if harmonies else 0.0
    
    def _calculate_color_harmony(self, color1: list, color2: list) -> float:
        """Calculate color harmony using color theory principles"""
        
        # Convert RGB to HSV for harmony calculation
        def rgb_to_hsv(rgb):
            r, g, b = [x/255.0 for x in rgb]
            max_c = max(r, g, b)
            min_c = min(r, g, b)
            diff = max_c - min_c
            
            if diff == 0:
                h = 0
            elif max_c == r:
                h = ((g - b) / diff) % 6
            elif max_c == g:
                h = (b - r) / diff + 2
            else:
                h = (r - g) / diff + 4
            
            h = h * 60
            s = 0 if max_c == 0 else diff / max_c
            v = max_c
            
            return h, s, v
        
        h1, s1, v1 = rgb_to_hsv(color1)
        h2, s2, v2 = rgb_to_hsv(color2)
        
        # Calculate harmony based on color relationships
        hue_diff = abs(h1 - h2)
        if hue_diff > 180:
            hue_diff = 360 - hue_diff
        
        # Complementary colors (180°) are harmonious
        # Analogous colors (30°) are harmonious
        # Triadic colors (120°) are harmonious
        harmony = 0.0
        
        if 170 <= hue_diff <= 190:  # Complementary
            harmony = 0.9
        elif hue_diff <= 30:  # Analogous
            harmony = 0.8
        elif 110 <= hue_diff <= 130:  # Triadic
            harmony = 0.7
        else:
            harmony = max(0, 1 - hue_diff / 180)
        
        # Adjust for saturation and value differences
        sat_diff = abs(s1 - s2)
        val_diff = abs(v1 - v2)
        
        harmony *= (1 - sat_diff * 0.3)
        harmony *= (1 - val_diff * 0.2)
        
        return harmony
    
    def _get_characteristic_multiplier(
        self, 
        attributes: ColorAttributes,
        palette: Dict
    ) -> float:
        """Get multiplier based on temperature, value, and chroma characteristics"""
        
        multiplier = 1.0
        
        # Temperature analysis
        undertone = self._analyze_temperature(attributes)
        if palette["temperature"] == "warm" and undertone == "warm":
            multiplier *= 1.2
        elif palette["temperature"] == "cool" and undertone == "cool":
            multiplier *= 1.2
        elif palette["temperature"] in ["warm_neutral", "cool_neutral"] and undertone == "neutral":
            multiplier *= 1.1
        
        # Value (depth) analysis
        depth = self._analyze_value(attributes)
        if palette["value"] == depth:
            multiplier *= 1.15
        
        # Chroma (clarity) analysis
        clarity = self._analyze_chroma(attributes)
        if palette["chroma"] == clarity:
            multiplier *= 1.1
        
        return min(multiplier, 1.5)  # Cap at 1.5x
    
    def _analyze_temperature(self, attributes: ColorAttributes) -> str:
        """Analyze warm vs cool undertone"""
        if not attributes.face_skin:
            return "neutral"
        
        r, g, b = attributes.face_skin.dominant_rgb
        
        # Warm: more yellow/golden undertones
        # Cool: more pink/blue undertones
        if r > b and g > b * 1.1:
            return "warm"
        elif b > r * 0.9:
            return "cool"
        else:
            return "neutral"
    
    def _analyze_value(self, attributes: ColorAttributes) -> str:
        """Analyze overall lightness/darkness"""
        values = []
        
        if attributes.hair:
            values.append(sum(attributes.hair.dominant_rgb) / 3)
        if attributes.face_skin:
            values.append(sum(attributes.face_skin.dominant_rgb) / 3)
        
        if not values:
            return "medium"
        
        avg_value = np.mean(values)
        
        if avg_value > 200:
            return "light"
        elif avg_value < 100:
            return "deep"
        else:
            return "medium"
    
    def _analyze_chroma(self, attributes: ColorAttributes) -> str:
        """Analyze color saturation/clarity"""
        saturations = []
        
        for region in [attributes.hair, attributes.face_skin, attributes.left_iris, attributes.right_iris]:
            if region:
                rgb = region.dominant_rgb
                max_c = max(rgb)
                min_c = min(rgb)
                if max_c > 0:
                    saturation = (max_c - min_c) / max_c
                    saturations.append(saturation)
        
        if not saturations:
            return "medium"
        
        avg_saturation = np.mean(saturations)
        
        if avg_saturation > 0.6:
            return "bright"
        elif avg_saturation < 0.3:
            return "muted"
        else:
            return "clear"