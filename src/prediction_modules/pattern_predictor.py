# src/prediction_modules/pattern_predictor.py
import pandas as pd
from typing import Optional
# *** แก้ไข: เปลี่ยน Relative Import เป็น Absolute Import ***
from prediction_modules.base_predictor import BasePredictor, SicBoOutcome

class PatternPredictor(BasePredictor):
    def __init__(self):
        # Define known patterns for High/Low string and their predicted outcomes.
        # These patterns are based on common observations in Sic Bo, adapted from Baccarat's PatternAnalyzer.
        self.known_highlow_patterns = {
            # Baccarat-like patterns adapted for Sic Bo High/Low
            "สูงสูงต่ำสูงสูง": "สูง", # PPBPP -> HHBHH
            "ต่ำต่ำสูงต่ำต่ำ": "ต่ำ", # BBPBB -> LLHLL
            "สูงสูงต่ำต่ำ": "สูง",   # HHLL
            "ต่ำต่ำสูงสูง": "ต่ำ",   # LLHH
            "สูงต่ำสูงต่ำ": "สูง",   # HLHL
            "ต่ำสูงต่ำสูง": "ต่ำ",   # LHLH
            "สูงสูงสูงสูง": "สูง",   # HHHH (Predict continuation of trend)
            "ต่ำต่ำต่ำต่ำ": "ต่ำ",   # LLLL (Predict continuation of trend)
        }

    def predict(self, history: pd.DataFrame) -> Optional[SicBoOutcome]:
        """
        Predicts based on recognized High/Low patterns in recent history.
        Adapted from Baccarat's PatternAnalyzer.
        """
        if len(history) < 4: # Needs at least 4 rolls for most patterns
            return None
        
        # Focus on HighLow for pattern analysis, filtering out 'ตอง' (triplets)
        # We look at the last 6 non-triplet results to match patterns.
        highlow_history_list = [val for val in history['HighLow'].tail(6).tolist() if val != 'ตอง']
        highlow_history_str = "".join(highlow_history_list)

        # Iterate through known patterns from longest to shortest to find a match.
        # This ensures that more specific (longer) patterns are matched first.
        # Check patterns from length of joined_history down to 3 (min pattern length in patterns dict)
        for pattern_len in range(len(highlow_history_str), 2, -1): 
            current_segment = highlow_history_str[-pattern_len:]
            if current_segment in self.known_highlow_patterns:
                return self.known_highlow_patterns[current_segment]
        
        return None

    @property
    def name(self) -> str:
        return "รูปแบบ H/L"
