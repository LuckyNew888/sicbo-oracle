# src/prediction_modules/two_two_pattern_predictor.py
import pandas as pd
from typing import Optional
from .base_predictor import BasePredictor, SicBoOutcome

class TwoTwoPatternPredictor(BasePredictor):
    def predict(self, history: pd.DataFrame) -> Optional[SicBoOutcome]:
        """
        Predicts based on a 2-2 pattern (e.g., High-High-Low-Low).
        Adapted from Baccarat's TwoTwoPattern.
        """
        if len(history) < 4: # Needs at least 4 rolls
            return None
        
        # Get the last 4 non-triplet High/Low outcomes
        last_four_highlow = [val for val in history['HighLow'].tail(4).tolist() if val != 'ตอง']

        if len(last_four_highlow) < 4: # Ensure we have 4 non-triplet outcomes
            return None
        
        # Check for AABB pattern where A != B
        # e.g., สูง-สูง-ต่ำ-ต่ำ -> Predict สูง
        # e.g., ต่ำ-ต่ำ-สูง-สูง -> Predict ต่ำ
        if (last_four_highlow[0] == last_four_highlow[1] and
            last_four_highlow[2] == last_four_highlow[3] and
            last_four_highlow[0] != last_four_highlow[2]):
            return last_four_highlow[0] # Predict the outcome that started the pattern
        
        return None

    @property
    def name(self) -> str:
        return "รูปแบบ 2-2"
