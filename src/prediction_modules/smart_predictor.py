# src/prediction_modules/smart_predictor.py
import pandas as pd
from typing import List, Optional
from .base_predictor import BasePredictor, SicBoOutcome

class SmartPredictor(BasePredictor):
    def __init__(self):
        # A comprehensive set of patterns, similar to Baccarat's SmartPredictor.
        self.patterns = {
            "สูงต่ำสูงต่ำ": "สูง", "ต่ำสูงต่ำสูง": "ต่ำ", # Ping Pong
            "สูงสูงต่ำต่ำ": "สูง", "ต่ำต่ำสูงสูง": "ต่ำ", # Two-Two
            "สูงสูงต่ำสูงสูง": "ต่ำ", "ต่ำต่ำสูงต่ำต่ำ": "สูง", # Three-Two-Three (variant)
            "สูงสูงสูงสูง": "สูง", "ต่ำต่ำต่ำต่ำ": "ต่ำ", # Long Dragon (predict continuation)
            "สูงต่ำต่ำสูง": "ต่ำ", "ต่ำสูงสูงต่ำ": "สูง", # Specific break patterns
            "สูงสูงต่ำต่ำสูงสูง": "ต่ำ", "ต่ำต่ำสูงสูงต่ำต่ำ": "สูง", # Extended Two-Two
        }

    def predict(self, history: pd.DataFrame) -> Optional[SicBoOutcome]:
        """
        Combines pattern matching with a trend-based prediction for a 'smarter' approach.
        Adapted from Baccarat's SmartPredictor.
        """
        if len(history) < 4: # Needs at least 4 rolls for initial patterns
            return None
        
        # Get last 8 non-triplet High/Low outcomes as a string for pattern matching
        highlow_history_list = [val for val in history['HighLow'].tail(8).tolist() if val != 'ตอง']
        joined_history = "".join(highlow_history_list)

        # Prioritize pattern matching from longest to shortest
        for length in range(len(joined_history), 2, -1): # Check patterns from max length down to 3
            segment = joined_history[-length:]
            if segment in self.patterns:
                return self.patterns[segment]

        # If no specific pattern, check for a strong trend in the last 10 non-triplet outcomes
        last_ten_highlow = [val for val in history['HighLow'].tail(10).tolist() if val != 'ตอง']
        if len(last_ten_highlow) >= 5: # Ensure enough data for trend check
            high_count = last_ten_highlow.count("สูง")
            low_count = last_ten_highlow.count("ต่ำ")
            
            # If one outcome significantly dominates (e.g., difference >= 3)
            if abs(high_count - low_count) >= 3:
                return "สูง" if high_count > low_count else "ต่ำ"

        # As a fallback, predict the last non-triplet outcome if no other strong signal
        if last_ten_highlow:
            return last_ten_highlow[-1]
            
        return None

    @property
    def name(self) -> str:
        return "Smart"
