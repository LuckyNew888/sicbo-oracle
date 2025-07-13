# src/prediction_modules/sniper_pattern_predictor.py
import pandas as pd
from typing import List, Optional
# *** แก้ไข: เปลี่ยน Relative Import เป็น Absolute Import ***
from prediction_modules.base_predictor import BasePredictor, SicBoOutcome

class SniperPatternPredictor(BasePredictor):
    def __init__(self):
        # Define a wider range of known patterns for High/Low string.
        # These are adapted from Baccarat's SniperPattern.
        self.known_patterns = {
            "สูงต่ำสูงต่ำ": "สูง", "ต่ำสูงต่ำสูง": "ต่ำ", # Ping Pong
            "สูงสูงต่ำต่ำ": "สูง", "ต่ำต่ำสูงสูง": "ต่ำ", # Two-Two
            "สูงสูงต่ำสูงสูง": "ต่ำ", "ต่ำต่ำสูงต่ำต่ำ": "สูง", # Three-Two-Three (variant)
            "สูงสูงสูงต่ำต่ำต่ำ": "ต่ำ", "ต่ำต่ำต่ำสูงสูงสูง": "สูง", # Dragon followed by opposite dragon
            "สูงสูงสูงสูง": "สูง", # Long Dragon (predict continuation)
            "ต่ำต่ำต่ำต่ำ": "ต่ำ", # Long Dragon (predict continuation)
            "สูงต่ำต่ำสูง": "ต่ำ", # Specific break pattern
            "ต่ำสูงสูงต่ำ": "สูง", # Specific break pattern
        }

    def predict(self, history: pd.DataFrame) -> Optional[SicBoOutcome]:
        """
        Predicts by checking for various known patterns in the recent High/Low history.
        Adapted from Baccarat's SniperPattern.
        """
        if len(history) < 4: # Needs at least 4 rolls for most patterns
            return None
        
        # Get the last 6 non-triplet High/Low outcomes as a string
        # We use 6 as the maximum length for patterns in this module, adjust as needed.
        highlow_history_list = [val for val in history['HighLow'].tail(6).tolist() if val != 'ตอง']
        joined_history = "".join(highlow_history_list)

        # Iterate from longest possible pattern down to shorter ones
        # This prioritizes more specific (longer) pattern matches.
        for length in range(len(joined_history), 2, -1): # Check patterns from max length down to 3
            pattern_segment = joined_history[-length:]
            if pattern_segment in self.known_patterns:
                return self.known_patterns[pattern_segment]
        
        return None

    @property
    def name(self) -> str:
        return "สไนเปอร์"
